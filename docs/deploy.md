# Deployment Guide

The app runs on a **DigitalOcean Droplet** provisioned via the DigitalOcean UI. All deployments are automated through GitHub Actions CI — every push to `main` that passes tests is deployed automatically.

---

## Infrastructure

| Component | Details |
|-----------|---------|
| Provider | DigitalOcean |
| Type | Droplet (Ubuntu) |
| Setup | Provisioned via DigitalOcean UI |
| Access | SSH via root + key stored in GitHub Secrets |
| App URL | `http://<DROPLET_HOST>:8080` |

---

## How CI Deploys

Defined in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). The `deploy` job runs automatically on every push to `main` after tests pass.

**Steps CI runs on the Droplet:**

```bash
cd MLH-PE-Hackathon-2026
git pull origin main

# Write .env from GitHub Secrets
echo "DATABASE_NAME=..." > .env
# ... (all secrets written here)

# Start DB and Redis (if not already running)
docker compose up db redis -d

# Rebuild and restart web containers
docker compose build --no-cache web
docker compose up web -d --scale web=2

# Restart nginx to re-resolve Docker DNS (important — see note below)
sleep 10
docker compose stop nginx
docker compose up nginx -d

# Start log shipper
docker compose up fluent-bit -d
docker compose up prometheus grafana -d
```

> **Why nginx is restarted on every deploy:** Nginx caches Docker DNS at startup. Without a restart, it routes all traffic to the original container IP and ignores new replicas. The restart forces it to re-resolve and pick up all `web` containers.

---

## GitHub Secrets Required

These must be set in the repository under **Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `DROPLET_HOST` | IP address of the DigitalOcean Droplet |
| `DROPLET_SSH_KEY` | Private SSH key with root access to the Droplet |
| `FLASK_DEBUG` | Set to `0` in production |
| `DATABASE_NAME` | Production DB name |
| `DATABASE_HOST` | Set to `hackathon-db` (Docker service name) |
| `DATABASE_USER` | PostgreSQL username |
| `DATABASE_PASSWORD` | PostgreSQL password |
| `BETTERSTACK_TOKEN` | Better Stack source token for log shipping |
| `BETTERSTACK_HOST` | Better Stack ingestion host |
| `GRAFANA_PASSWORD` | Grafana admin password (only applied on first startup) |

---

## Manual Deploy (Emergency)

If CI is broken or you need to deploy manually, SSH into the Droplet and run the deploy steps yourself:

```bash
ssh root@<DROPLET_HOST>

cd MLH-PE-Hackathon-2026
git pull origin main

# Rebuild and restart
docker compose build --no-cache web
docker compose up web -d --scale web=2
sleep 10
docker compose stop nginx
docker compose up nginx -d
```

---

## Rollback

CI does not maintain previous images. To roll back to a prior commit:

```bash
ssh root@<DROPLET_HOST>

cd MLH-PE-Hackathon-2026
git log --oneline -10          # find the commit to roll back to
git checkout <commit-hash>

docker compose build --no-cache web
docker compose up web -d --scale web=2
sleep 10
docker compose stop nginx
docker compose up nginx -d
```

To return to the latest main:
```bash
git checkout main
git pull origin main
```

---

## Verifying a Deploy

```bash
# Check all containers are running
docker ps

# Hit the health endpoint
curl -s http://localhost:8080/health
# Expected: {"status": "ok"}

# Check logs
docker compose logs -f web
```
