# Runbook: Service Down

**Alert source:** Better Stack uptime monitor (`GET /health` check every 3 minutes)  
**Fires when:** `http://<DROPLET_IP>:8080/health` is unreachable  
**Severity:** Critical — full user-facing outage

---

## 1. Confirm the outage

```bash
curl -s http://<DROPLET_IP>:8080/health
```

- Returns `{"status": "ok"}` → false alarm, monitor may have had a blip. Watch for recurrence.
- Times out or connection refused → outage confirmed, continue below.

---

## 2. Check the Grafana dashboard

Open `http://<DROPLET_IP>:3000` → **URL Shortener** dashboard.

- **Request Rate panel** → has traffic dropped to zero?
- **Latency panel** → did latency spike before traffic dropped?
- **CPU / RAM panels** → did resource saturation precede the outage?

This tells you whether it was a crash, overload, or infrastructure failure.

---

## 3. SSH into the Droplet

```bash
ssh root@<DROPLET_IP>
cd MLH-PE-Hackathon-2026
```

---

## 4. Check container status

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

| Symptom | Likely cause |
|---------|-------------|
| `web-1` and `web-2` both missing or `Restarting` | App crash — go to §5 |
| `nginx` missing | Nginx down — go to §6 |
| All containers missing | Droplet rebooted — go to §7 |
| All containers `Up` | Port/network issue — go to §8 |

---

## 5. Web container crashed

Check logs for the crash reason:

```bash
docker logs --tail 50 mlh-pe-hackathon-2026-web-1
docker logs --tail 50 mlh-pe-hackathon-2026-web-2
```

Look for `ERROR` lines or Python tracebacks. Then restart:

```bash
docker compose up web -d --scale web=2
```

Docker's `restart: on-failure` policy should have already restarted it — check restart count:

```bash
docker inspect mlh-pe-hackathon-2026-web-1 --format '{{.RestartCount}} restarts'
```

A high restart count means a persistent crash loop — fix the root cause before restarting again.

---

## 6. Nginx down

```bash
docker logs --tail 20 mlh-pe-hackathon-2026-nginx-1
docker compose up nginx -d
```

If nginx was redeployed recently, it may have cached stale web container IPs. Always restart nginx after scaling web:

```bash
docker compose stop nginx && docker compose up nginx -d
```

---

## 7. Droplet rebooted

All containers will be stopped. Bring everything back:

```bash
docker compose up db redis -d
docker compose up web -d --scale web=2
sleep 10
docker compose stop nginx && docker compose up nginx -d
docker compose up fluent-bit prometheus grafana -d
```

---

## 8. Containers up but service unreachable

Test from inside the server:

```bash
curl -s http://localhost:8080/health
```

If this works but external access doesn't → **DigitalOcean firewall** is blocking port 8080.  
Go to **DigitalOcean UI → Networking → Firewalls** and verify port 8080 is open.

---

## 9. Verify recovery

```bash
curl -s http://<DROPLET_IP>:8080/health
# Expected: {"status": "ok"}
```

Check Grafana — request rate should resume within 1 scrape interval (15s).  
Better Stack will auto-resolve the alert once 2 consecutive health checks pass (~6 minutes).
