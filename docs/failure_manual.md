## 🚨 Failure Manual

This file documents how the system behaves under failure, how to reproduce issues, and how to recover.

---

## 🧱 System Components

* **web** – Flask app (Gunicorn, horizontally scalable)
* **nginx** – Load balancer
* **db** – PostgreSQL database
* **redis** – Cache layer
* **fluent-bit** – Log shipper (ships to Better Stack)
* **prometheus** – Metrics scraper (scrapes both web containers every 15s)
* **grafana** – Dashboard (port 3000)
* **k6** – Load testing tool

---

## 📖 Runbooks

For step-by-step emergency guides, see:
- [Service Down Runbook](runbooks/service-down.md) — fired by Better Stack when `/health` is unreachable
- [High Error Rate Runbook](runbooks/high-error-rate.md) — fired by Better Stack when error logs exceed threshold

---

## 🚑 First Response Checklist

Something is wrong. Start here before diving into individual failure modes.

**Step 1 — Are containers running?**
```bash
docker ps
```
All of `web-1`, `web-2`, `nginx`, `redis`, `hackathon-db` should show `Up` and `(healthy)`. Any missing or `Restarting` container is your first lead.

**Step 2 — Is the app responding?**
```bash
curl -s http://localhost:8080/health
# Expected: {"status":"ok"}
```
If this fails, nginx or both web containers are down. If it returns 500, the app is up but something internal (DB, unhandled exception) is broken.

**Step 3 — Check logs on the unhealthy container**
```bash
docker logs --tail 50 mlh-pe-hackathon-2026-web-1
docker logs --tail 50 mlh-pe-hackathon-2026-nginx-1
docker logs --tail 50 hackathon-db
```
The app emits structured JSON logs — look for `"level": "ERROR"` lines. DB connection errors and unhandled exceptions appear here.

**Step 4 — Check resource usage**
```bash
docker stats --no-stream
```
DB CPU exceeding 100% → connection pool or query bottleneck. Web container memory spiking → possible leak or traffic surge.

**Step 5 — Check restart count**
```bash
docker inspect mlh-pe-hackathon-2026-web-1 --format '{{.RestartCount}} restarts'
```
A non-zero restart count means the container has been crashing and recovering. Cross-reference with logs from Step 3.

Once you've identified which component is failing, jump to the relevant section below.

| Symptom | Likely section |
|---------|---------------|
| Site completely unreachable (timeout) | §16 Droplet Unreachable or §5 Nginx Failure |
| `curl /health` times out (Droplet up) | §5 Nginx Failure or §15 Port Conflicts |
| `curl /health` returns 500 | §2 Database Failure or §3 DB Connection Pool Exhaustion |
| Container shows `Restarting` | §14 Missing Environment Variables |
| All responses slow, no errors | §3 DB Connection Pool, §6 High Load, §7 Cold Cache |
| Empty API responses | §8 Missing Seed Data |
| Build fails in CI | §11 uv Lockfile, §12 uv Version |
| Logs not appearing in Better Stack | §18 Fluent Bit Failure |
| Dashboard shows "No data" | §16 Grafana / Prometheus Down |

---

## Failure Modes & Recovery

### 1. Web Container Failure

**Trigger**

Kill the main process inside the container to simulate a real crash. Using `docker kill` from the outside marks the container as manually stopped and does **not** trigger the restart policy — you must crash the process from within:

```bash
docker exec mlh-pe-hackathon-2026-web-1 python3 -c "import os,signal; os.kill(1, signal.SIGKILL)"
```

Note: the container does not have a `kill` binary, so `docker exec ... kill -9 1` fails. Use the Python approach above.

**Behavior**
* The container exits immediately with code 137
* Docker detects the non-zero exit and restarts the container automatically (usually within 1–2 seconds)
* Nginx routes traffic to the remaining healthy replica during the restart window
* The restarted container passes its healthcheck (`GET /health`) before receiving new traffic

**Impact**
* Momentary reduction in capacity (one fewer replica)
* No user-facing outage if 2+ replicas are running

**Recovery**

Handled automatically by Docker's `restart: on-failure` policy in `docker-compose.yml`. No manual intervention needed. To verify:

```bash
docker inspect mlh-pe-hackathon-2026-web-1 --format '{{.HostConfig.RestartPolicy.Name}}'
# expected: on-failure

docker ps  # container reappears within seconds
curl -s http://localhost:8080/health  # still returns {"status":"ok"}
```

If both replicas are down, bring them back with:
```bash
docker compose up -d --scale web=2
```

**Mitigation**

* `restart: on-failure` added to `docker-compose.yml` (note: `deploy.restart_policy` only works in Docker Swarm — it is ignored by `docker compose up`)
* Run 2+ replicas so nginx can absorb traffic during a single container restart
* Nginx healthcheck routes around unhealthy containers automatically

---

### 2. Database Failure

**Trigger**

```bash
docker stop hackathon-db
```

**Behavior**
* All API endpoints that touch the DB return 500 errors
* The app does not crash — Flask's 500 error handler returns `{"error": "Internal server error"}` as JSON
* Redis-cached responses (short code redirects, URL lookups) continue to work until TTL expires

**Impact**
* Effectively a full outage for write operations and uncached reads
* Cached redirects continue working for up to 300s (Redis TTL)

**Recovery**

```bash
docker start hackathon-db
```

The app reconnects automatically via Peewee's connection pool — no restart needed.

**Mitigation**
* `PooledPostgresqlDatabase` with `max_connections=32` prevents connection exhaustion under load (dropping error rate from 20% → 2.6% at 500 VUs)
* Redis caching provides a partial buffer — hot URLs continue to redirect even while DB is down
* Consider adding DB-level retries for transient connection failures

---

### 3. Database Connection Pool Exhaustion

**Trigger**
* High concurrent load (200+ VUs) against an under-provisioned pool, or a connection leak

**Behavior**
* The DB is running and healthy but requests still fail with 500 errors
* `docker logs` on the web container shows errors like:
  ```
  peewee.OperationalError: FATAL: remaining connection slots are reserved
  ```
  or:
  ```
  peewee.OperationalError: could not connect to server: Connection refused
  ```
* `docker stats` shows DB CPU spiking above 100% while web containers look normal

**Impact**
* Partial to full outage depending on severity — all DB-dependent endpoints return 500, cached responses still work

**Recovery**

Restart the web containers to flush open connections:
```bash
docker compose up -d --scale web=2 --force-recreate
```

Or reduce load temporarily while connections drain naturally.

**Mitigation**
* `PooledPostgresqlDatabase` is configured with `max_connections=32` shared across all Gunicorn workers — this was the single biggest fix, dropping error rate from 20% → 2.6% at 500 VUs
* Pool size of 32 was chosen to stay within Postgres's default `max_connections=100` while running 2 replicas × 4 workers × 4 threads
* If adding more replicas, reduce per-instance pool size proportionally to avoid saturating Postgres

**RTO:** ~30 seconds (time to force-recreate containers and pass healthcheck)

---

### 4. Redis Failure (Cache Down)

**Trigger**

```bash
docker stop mlh-pe-hackathon-2026-redis-1
```

**Behavior**
* All cache reads return `None` (miss)
* The app falls back to the database for every request — graceful degradation, no crash
* Cache writes are silently dropped

**Impact**
* No outage — app continues to function correctly
* Latency and DB load increase significantly under high concurrency (cache was absorbing the majority of read traffic)
* At 500 VUs, losing the cache pushed error rates up and p95 latency well above 1s

**Recovery**

```bash
docker start mlh-pe-hackathon-2026-redis-1
```

Cache warms automatically as requests come in. No app restart needed.

**Mitigation**
* Graceful cache fallback is implemented — `_cache_get` returns `None` on any Redis error and the app continues to the DB
* Redis TTL set to 300s to reduce cache miss frequency under normal operation
* Monitor cache hit rate to detect Redis degradation early

---

### 5. Nginx Failure

**Trigger**

```bash
docker stop mlh-pe-hackathon-2026-nginx-1
```

**Behavior**
* Port 8080 becomes unreachable immediately
* Web containers remain running and healthy — the failure is at the entry point only

**Impact**
* Full outage — all external traffic is blocked

**Recovery**

```bash
docker start mlh-pe-hackathon-2026-nginx-1
```

**Known issue — DNS caching bug:** Nginx resolves the `web` upstream hostname once at startup and caches it. After a redeploy that creates new web containers, nginx may continue routing all traffic to a stale (or single) container IP, effectively ignoring other replicas. This caused 100% of traffic to hit `web-1` while `web-2` was idle.

**Fix:** Force a full nginx restart on every deploy so it re-resolves Docker DNS and picks up all container IPs. This is why the CI deploy script runs:
```bash
docker compose stop nginx
docker compose up nginx -d
```

**Mitigation**
* Always restart nginx after scaling or redeploying web containers
* Validate nginx config before restarting: `docker exec mlh-pe-hackathon-2026-nginx-1 nginx -t`
* Web container healthchecks are configured so nginx only routes to containers that have passed `GET /health`

---

### 6. High Load (200–500 Users)

**Trigger**

```bash
docker compose run k6 run --vus 500 --duration 60s /load_test_k6.js
```

**Behavior**
* Increased latency
* Possible error spikes if DB connections are exhausted
* High DB CPU usage (observed exceeding 100% in `docker stats`)

**Impact**
* Performance degradation — p95 latency can spike to 4s+ without mitigation

**Recovery**

Scale up web replicas:
```bash
docker compose up -d --scale web=4
```

**Mitigation (applied iteratively — see bottleneck report in PROGRESS.md)**

| Fix | Effect |
|-----|--------|
| Switched `flask run` → Gunicorn gthread (4 workers × 4 threads) | Dropped error rate from ~43% |
| Redis TTL 60s → 300s | Reduced DB pressure from cache misses |
| Nginx `worker_connections 1024` + keepalive | Reduced connection queuing |
| `PooledPostgresqlDatabase` max 32 connections | Dropped error rate from 20% → 2.6% |
| Force nginx restart on deploy (DNS fix) | Dropped error rate from 2.6% → 0% |

---

### 7. Cold Cache / Cache Miss Surge

**Trigger**
* Redis restart or TTL expiration across many keys simultaneously

**Behavior**
* Spike in DB queries as all requests miss cache
* Temporary latency increase

**Impact**
* Short-term slowdown, no outage

**Recovery**
* Automatic — cache warms as requests come in

**Mitigation**
* TTL set to 300s to reduce expiration frequency
* Pre-warm cache for high-traffic short codes if needed

---

### 8. Missing Seed Data

**Trigger**
* Reset DB volume or failed init scripts

**Behavior**
* Empty API responses — tables exist but contain no data

**Impact**
* App appears broken (returns empty lists, 404s for all lookups)

**Recovery**
```bash
docker compose down -v
docker compose up --build
```

The `init.sql` script in `/docker-entrypoint-initdb.d/` runs automatically on first DB start and seeds initial data.

**Mitigation**
* Seed scripts are mounted at `/docker-entrypoint-initdb.d/` in `docker-compose.yml` — they run automatically on fresh volume creation

---

### 9. Networking Issues

**Trigger**
* Using `localhost` instead of Docker service names in config

**Behavior**
* `Connection refused` or `EOF` errors between containers

**Impact**
* Services cannot communicate — partial or full outage depending on which service is misconfigured

**Fix**
Use Docker Compose service names, not `localhost`:

| Service | Correct address |
|---------|----------------|
| Web app | `http://web:5000` |
| Database | `hackathon-db:5432` |
| Redis | `redis:6379` |
| Nginx | `http://nginx:80` |

---

### 10. Bad Input / Graceful Failure

**Trigger**
* Sending malformed JSON, missing required fields, wrong types, or non-existent IDs to the API

**Behavior**
* App returns clean JSON error responses — it does not crash or return HTML stack traces
* Global 404 and 500 handlers in `app/__init__.py` catch unhandled cases

**Impact**
* None — app remains fully operational

**Example responses**

```bash
# Missing fields → 422
curl -s -X POST http://localhost:8080/urls/ -H "Content-Type: application/json" -d '{}'
# {"error": {"original_url": "original_url is required", "user_id": "user_id is required"}}

# Non-existent resource → 404
curl -s http://localhost:8080/users/99999
# {"error": "User not found"}

# Unknown route → 404
curl -s http://localhost:8080/totally/fake/route
# {"error": "Not found"}
```

---

### 11. uv Lockfile Out of Sync

**Trigger**
* `pyproject.toml` was updated (dependency added/removed) but `uv.lock` was not regenerated before committing

**Behavior**
* Docker build fails with an error like:
  ```
  error: The lockfile at `uv.lock` needs to be updated, but `--frozen` was provided.
  ```
* The `uv sync --frozen` step in the Dockerfile treats a stale lockfile as a hard error — the image cannot be built

**Impact**
* Full CI/CD failure — no new image is built, no deploy happens

**Recovery**
```bash
uv lock        # regenerate the lockfile
git add uv.lock
git commit -m "Update uv.lock"
git push
```

**Mitigation**
* Always run `uv lock` after modifying `pyproject.toml` before pushing
* CI will catch this immediately since the build step fails

---

### 12. uv Version Incompatibility (Unpinned `uv:latest`)

**Trigger**
* The Dockerfile pulls `ghcr.io/astral-sh/uv:latest` at build time — a breaking uv release could silently change behavior or fail the build

**Behavior**
* Build may fail with unexpected errors, or produce a working image with different dependency resolution than expected

**Impact**
* Non-deterministic builds — works locally, fails in CI (or vice versa)

**Recovery**
* Pin uv to a specific version in the Dockerfile:
  ```dockerfile
  COPY --from=ghcr.io/astral-sh/uv:0.6.0 /uv /usr/local/bin/uv
  ```

**Mitigation**
* Pin to a specific uv version and update it deliberately rather than pulling `latest` on every build

---

### 13. Gunicorn Worker Config Mismatch

**Trigger**
* Running the container directly (e.g. `docker run`) instead of via `docker compose up`

**Behavior**
* The `CMD` in the Dockerfile starts Gunicorn with `--workers=2` and no threading
* `docker-compose.yml` overrides this with `--workers=4 --threads=4` (gthread worker class)
* Running without compose gives a significantly weaker server — lower throughput, higher latency under load

**Impact**
* No crash, but performance degrades — at 500 VUs the 2-worker sync config produced ~43% error rate vs 0% with the compose config

**Recovery**
* Always use `docker compose up` to start the stack, not `docker run` directly

---

### 14. Missing Environment Variables / Secrets

**Trigger**
* `.env` file missing on the server, or GitHub secrets not configured in the repository

**Behavior**
* App fails to connect to the database at startup
* Container enters a crash loop — healthcheck fails, Docker restarts it repeatedly with exponential backoff
* `docker ps` shows the container as `Restarting` or `unhealthy`

**Impact**
* Full outage — no web container reaches healthy state, nginx has no backend to route to

**Recovery**
```bash
# Check what the container is seeing
docker logs mlh-pe-hackathon-2026-web-1

# Recreate .env on the server manually, then restart
docker compose up -d web
```

**Mitigation**
* CI deploy script writes `.env` from GitHub secrets before starting containers — ensure all secrets (`DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `FLASK_DEBUG`) are set in the repository settings

---

### 15. Port Conflicts

**Trigger**
* Another process on the host is already using port `8080` (nginx), `5432` (postgres), or `6379` (redis)

**Behavior**
* `docker compose up` starts but the conflicting service silently fails to bind its port
* The service appears running in `docker ps` but is unreachable from the host

**Impact**
* Partial outage — whichever service has the port conflict is inaccessible

**Recovery**
```bash
# Find what is using the port
lsof -i :8080
lsof -i :5432
lsof -i :6379

# Kill the conflicting process or change the port mapping in docker-compose.yml
```

---

### 16. Grafana / Prometheus Down (Dashboard Unavailable)

**Trigger**
```bash
docker stop mlh-pe-hackathon-2026-grafana-1
docker stop mlh-pe-hackathon-2026-prometheus-1
```

**Behavior**
* `http://<host>:3000` is unreachable — dashboard is unavailable
* The app itself is unaffected — Prometheus and Grafana are read-only observers
* If only Prometheus is down, Grafana shows "No data" but continues loading

**Impact**
* No user-facing outage — purely an observability gap

**Recovery**
```bash
docker compose up prometheus grafana -d
```

Grafana's volume (`grafana_data`) persists the dashboard and datasource config — no re-provisioning needed.

**Known issue — Grafana password on volume reset:** `GF_SECURITY_ADMIN_PASSWORD` only takes effect on first startup. If the `grafana_data` volume is wiped and restarted, the password resets to whatever `GRAFANA_PASSWORD` is set to in `.env`. If the secret is missing, it defaults to `admin`.

**Mitigation**
* Both services use `restart: on-failure` — Docker will restart them automatically after a crash
* Dashboard and datasource are provisioned from files (`grafana/provisioning/`) — recreating the volume restores everything automatically

---

### 17. DigitalOcean Droplet Unreachable

**Trigger**
* Droplet is powered off, rebooted, or unresponsive (OOM kill, kernel panic, etc.)

**Behavior**
* `http://<DROPLET_HOST>:8080` is unreachable — all requests time out
* Better Stack uptime monitor fires a "Service Down" alert within ~3 minutes
* SSH access is also unavailable until the Droplet recovers

**Impact**
* Full outage — the entire stack is hosted on a single Droplet

**Recovery**

1. Log in to the [DigitalOcean Control Panel](https://cloud.digitalocean.com)
2. Navigate to **Droplets** → select the Droplet
3. If powered off: click **Power On**
4. If unresponsive: click **Power Cycle** (hard reboot)
5. Wait ~30 seconds, then SSH back in and verify:

```bash
ssh root@<DROPLET_HOST>
cd MLH-PE-Hackathon-2026
docker ps   # check containers came back up
curl -s http://localhost:8080/health
```

If containers did not restart automatically:
```bash
docker compose up db redis web nginx fluent-bit -d --scale web=2
```

**Mitigation**
* Docker's `restart: on-failure` policy restarts individual containers after a crash, but does not help if the entire Droplet goes down
* DigitalOcean provides a recovery console in the UI if SSH is unavailable — use **Droplet Console** under Access

---

### 18. Fluent Bit Failure (Log Shipping Down)

**Trigger**

```bash
docker stop mlh-pe-hackathon-2026-fluent-bit-1
```

**Behavior**
* App logs are still written to stdout by the web containers — nothing changes from the app's perspective
* Logs stop being shipped to Better Stack — the external log viewer goes dark
* Better Stack's "High Error Rate" alert may stop firing since it relies on ingested logs

**Impact**
* No user-facing outage — the app continues to run normally
* Observability is degraded: logs are only accessible via `docker logs` on the server

**Recovery**

```bash
docker start mlh-pe-hackathon-2026-fluent-bit-1
```

Fluent Bit resumes shipping from where it left off (it uses a file position tracker). Logs produced during the downtime may not be retroactively shipped.

**Mitigation**
* Fluent Bit is isolated from the app — its failure cannot cascade to the web or DB containers
* Ensure `BETTERSTACK_TOKEN` and `BETTERSTACK_HOST` are set correctly; a missing token causes Fluent Bit to silently drop logs without crashing

---

## 🛠 Debugging Commands

```bash
# View running containers
docker ps

# View logs for a specific container
docker logs -f mlh-pe-hackathon-2026-web-1

# Monitor CPU/memory across all containers
docker stats

# Test health endpoint
curl -s http://localhost:8080/health

# Check restart policy on a container
docker inspect mlh-pe-hackathon-2026-web-1 --format '{{.HostConfig.RestartPolicy.Name}}'

# Check restart count (non-zero means it has crashed and recovered)
docker inspect mlh-pe-hackathon-2026-web-1 --format '{{.RestartCount}}'

# Validate nginx config
docker exec mlh-pe-hackathon-2026-nginx-1 nginx -t
```
