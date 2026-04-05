# Hackathon Quest Progress

## Reliability
### 🥉 Tier 1: Bronze

| Objective | Status | Notes |
|-----------|--------|-------|
| Write unit tests with pytest | ✅ Done | 97 unit + system tests across health, users, urls, events |
| Set up GitHub Actions CI | ✅ Done | `.github/workflows/ci.yml` — runs on every push/PR |
| `GET /health` endpoint returns 200 | ✅ Done | `http://localhost:8080/health` |

#### Verification  
Screenshot of `GET /health` returning 200:  
![Health End Point](report-images/Health_endpoint.png)  

Screenshot of Github Action CI with passing tests:  
![Github CI](report-images/GithubCI.png)  

### 🥈 Tier 2: Silver

| Objective | Status | Notes |
|-----------|--------|-------|
| 50% Coverage: Use pytest-cov | ✅ Done | `pytest-cov` added to dev dependencies |
| Integration Testing: Write tests that hit the API | ✅ Done | System tests use Flask `test_client()` against a real DB |
| The Gatekeeper: CI fails if tests fail | ✅ Done | See below |
| Error Handling: Document how app handles 404s and 500s | ✅ Done | [See README](README.md#error-handling) |

#### Verification  
Screenshot of 50% Coverage:  
![Code Coverage](report-images/code_coverage.png) 

Screenshots of deploy workflow dependency and failed test commits:  
![The Gatekeeper Workflow](report-images/gatekeeper1.png)  
![Failed Test Run](report-images/gatekeeper2.png). 
![Failed Commit](report-images/gatekeeper3.png). 

### 🥇 Tier 3: Gold

| Objective | Status | Notes |
|-----------|--------|-------|
| 70% Coverage: Use pytest-cov | ✅ Done | See image below |
| Graceful failure | ✅ Done | Live demo against prod (See below) |
| Restarts automatically when app process or container is killed | ✅ Done | `restart: on-failure` in docker-compose.yml — demo TODO |
| Create failure manual and document exactly what happens when things break | ✅ Done | [Failure Manual](./failure_manual.md) |

#### Verification  
Screenshot of 70% Coverage:  
![Code Coverage](report-images/code_coverage.png)  

#### Graceful Failure — Live Demo

A script was run against the production server (`http://64.23.146.45:8080`) sending 9 bad inputs. Every case returned a clean JSON `{"error": "..."}` response with an appropriate 4xx status code — no crashes, no HTML stack traces.

**Tests run:**

| # | Input | Expected Status | What it verifies |
|---|-------|-----------------|------------------|
| 1 | `POST /urls/` with empty `{}` body | 422 | Missing required fields returns validation error |
| 2 | `POST /urls/` with `"this is not json"` body | 422 | Malformed / non-JSON body does not crash the app |
| 3 | `POST /urls/` with `user_id: 99999` (non-existent) | 404 | Reference to missing resource returns 404 JSON |
| 4 | `POST /users/` with `username: 123` (number) | 422 | Wrong field type returns validation error |
| 5 | `POST /users/` with no `email` field | 422 | Missing field returns validation error |
| 6 | `GET /users/99999` | 404 | Non-existent user returns 404 JSON |
| 7 | `GET /urls/99999` | 404 | Non-existent URL returns 404 JSON |
| 8 | `GET /nonexistentcode` | 404 | Unknown short code returns 404 JSON |
| 9 | `GET /totally/fake/route` | 404 | Unknown route returns 404 JSON |

Live demo video:  
https://github.com/user-attachments/assets/9ea2292a-210b-4ac5-ab4c-8919ee41c6fe




---

## Scalability
### 🥉 Tier 1: Bronze

| Objective | Status | Notes |
|-----------|--------|-------|
| Set up k6 or Locust for load testing | ✅ Done | utilizes k6 docker image |
| Simulate 50 concurrent users hitting your service | ✅ Done | See image below |
| Document your Response Time (Latency) and Error Rate | ✅ Done | see image below |

#### Verification  
Screenshot of terminal output showing 50 concurrent users:  
![50 concurrent users](report-images/50_concurrent_test.png)

Documented baseline p95 response time:  
```
  █ THRESHOLDS 

    http_req_duration
    ✓ 'p(95)<500' p(95)=193.88ms

    http_req_failed
    ✓ 'rate<0.01' rate=0.00%
```

### 🥈 Tier 2: Silver

| Objective | Status | Notes |
|-----------|--------|-------|
| 200 concurrent users for load testing | ✅ Done | Number of concurrent users can be configured in the command to run the tests |
| Run 2+ instances of your app (containers) using Docker Compose | ✅ Done | Number of instances can be configured when starting up the container |
| Put a Load Balancer (Nginx) in front to split traffic between instances | ✅ Done | See image below |
| Keep response times under 3 seconds | ✅ Done | See image below |

#### Verification  
Screenshot of terminal output showing 200 concurrent users:  
![200 Concurrent Users](report-images/200_concurrent_test.png)

Screenshot of terminal output showing 2 docker containers and nginx container:  
![Docker and Nginx Containers](report-images/docker_nginx_container.png)

### 🥇 Tier 3: Gold

| Objective | Status | Notes |
|-----------|--------|-------|
| Handle 500+ concurrent users (or 100 req/sec) | ✅ Done | 381 req/s See k6 load test results screenshot  |
| Implement Redis | ✅ Done | Caching short code → URL mappings with 300s TTL |
| Identifying Bottlenecks | ✅ Done | See bottleneck report below |
| Error rate must stay under 5% | ✅ Done | 0% error rate (See below) |

#### Verification  
Evidence of caching:  
![Evidence Of Caching](report-images/caching.png)   

![Cache Hit Count](report-images/CacheHitCount.png)   

Screenshot of terminal output showing 500+ concurrent users:  
![500 concurrent users](report-images/500_concurrent_load_balanced.png)

Error Rate from above screenshot:
```
   █ THRESHOLDS

    http_req_duration
    ✓ 'p(95)<1000' p(95)=936.32ms

    http_req_failed
    ✓ 'rate<0.05' rate=0.00%


  █ TOTAL RESULTS

    checks_total.......: 23614   380.910431/s
    checks_succeeded...: 100.00% 23614 out of 23614
    checks_failed......: 0.00%   0 out of 23614
```

Bottleneck Report:

**Methodology:** Iteratively ran k6 at 500 VUs, observed failure rates and response times, applied targeted fixes, and re-ran to measure improvement.

| Iteration | Change | Error Rate | p95 |
|-----------|--------|------------|-----|
| Baseline | Flask dev server, 2 replicas | 43.62% | 4.62s |
| +Gunicorn (sync, 2 workers) | Switched from `flask run` to gunicorn | ~43% | ~4.5s |
| +Redis TTL 300s | Increased cache TTL from 60s → 300s | ~38% | ~4s |
| +Nginx tuning | `worker_processes auto`, keepalive, 1024 connections | ~25% | ~2s |
| +Gunicorn gthread (4 workers × 4 threads) | Replaced gevent (conflicted with Peewee) with gthread | 20.02% | 658ms |
| +DB connection pooling (max 32) | `PooledPostgresqlDatabase` via Peewee playhouse | 2.60% | 769ms |
| +Nginx load balancing fix | Forced nginx restart on deploy to re-resolve Docker DNS | 0.00% | 936ms |

**Identified Bottlenecks:**

1. **Database connections (primary)** — Each request opened a new Postgres connection. At 500 VUs this saturated the DB. Fixed with `PooledPostgresqlDatabase` capping connections at 32, shared across workers. This was the single biggest improvement — error rate dropped from 20% → 2.6%.

2. **Flask dev server** — `flask run` is single-threaded and not production-grade. Replaced with Gunicorn (`gthread` worker class). `gevent` was also tested but caused conflicts with Peewee's synchronous psycopg2 driver.

3. **Nginx connection limits** — Default nginx config had no `worker_connections` limit set, causing connection queuing. Added `worker_processes auto` and `worker_connections 1024` with upstream keepalive.

4. **Cache TTL too short** — Redis TTL of 60s caused frequent cache misses under load, pushing traffic back to the DB. Increased to 300s.

5. **Nginx DNS caching (root cause of load imbalance)** — Nginx resolved `web` to a single container IP at startup and stuck to it, sending 100% of traffic to one replica. Fixed by forcing a full nginx restart on every CI deploy so it re-resolves Docker DNS and picks up all container IPs. This eliminated the remaining 2.6% error rate entirely — final error rate is 0.00%.

I ran `docker stats` to identify which parts of the system were under the most stress. The image below was taken from a 500+ concurrent user run with 2 web server instances and a nginx load balancer. From the image below, we can see that the database's CPU exceeds 100%, confirming it as the primary bottleneck.

The web servers are also under significant load, though the database remains the primary bottleneck.

![Docker Stats](report-images/bottleneck.png)

The image below shows Nginx routing all traffic to a single container (` mlh-pe-hackathon-2026-web-1`) due to incorrect load balancing configuration — Nginx cached the DNS resolution at startup and never re-resolved it, effectively ignoring the second replica entirely.

![Nginx Load Balancing Misconfiguration](report-images/bottleneck2.png)

---

## Observability
### 🥉 Tier 1: Bronze

| Objective | Status | Notes |
|-----------|--------|-------|
| Configure JSON logs | ✅ Done | See image below |
| Expose a /metrics endpoint showing CPU/RAM usage | ✅ Done | See image below |
| Have a way to view logs without SSH-ing into the server. | ✅ Done | Fluent Bit ships logs to Better Stack — viewable at betterstack.com |

#### Verification  
JSON logs:  
![JSON logs](report-images/json_logs.png)

Metrics endpoint:  
![Metrics endpoint](report-images/metrics.png). 

External Logs (BetterStack):
![Betterstack logs](report-images/BetterStackLogs.png). 

### 🥈 Tier 2: Silver

| Objective | Status | Notes |
|-----------|--------|-------|
| Configure alerts for "Service Down" and "High Error Rate" | ✅ Done | Uptime monitor + log alert in Better Stack (see config below) |
| Connect alerts to a channel (Slack, Discord, Email) | ✅ Done | E-mail alerts configured for the team |
| Alert must fire within 5 minutes of failure | ✅ Done | Service Down: ~3 min, High Error Rate: ~1-2 min |

#### Verification

Service Down Monitor:
![Service Down Monitor](report-images/ServiceDown1.png)
![Service Down Alert](report-images/ServiceDown2.png)

High Error Rate Alert:
![High Error Rate Alert](report-images/HighError1.png)
![High Error Rate Config](report-images/HighError2.png)

#### Alert Configuration

**Service Down** — Better Stack Uptime Monitor:
```yaml
monitor:
  name: Service Down
  url: http://64.23.146.45:8080/health
  alert_when: url_becomes_unavailable
  check_frequency: 3 minutes
  confirmation_period: immediate
  recovery_period: 3 minutes
  notification:
    channel: email
    team: Current team
```

**High Error Rate** — Better Stack Log Alert:
```yaml
alert:
  name: High Error Rate
  source: five_nines_prod
  query: "log.level:WARNING OR log.level:ERROR"
  detection_method: threshold
  condition: count > 10
  run_every: 1 minute
  on_data_from: last 1 minute
  confirmation_period: immediately
  recovery_period: 2 minutes
  notification:
    channel: email
    team: Current team
```

### 🥇 Tier 3: Gold

| Objective | Status | Notes |
|-----------|--------|-------|
| Build a visual dashboard tracking 4+ metrics (Latency, Traffic, Errors, Saturation) | ✅ Done | Grafana dashboard with 5 panels — Traffic, Error Rate, Latency p50/p95/p99, CPU, RAM |
| Write a runbook — "In Case of Emergency" guide | ✅ Done | [service-down.md](runbooks/service-down.md) and [high-error-rate.md](runbooks/high-error-rate.md) |
| Diagnose a fake issue using only the dashboard and logs | ⬜ Todo | |

#### Verification

Grafana Dashboard:
![Grafana Dashboard](report-images/Grafana.png)
