# Runbook: High Error Rate

**Alert source:** Better Stack log alert  
**Fires when:** More than 10 `WARNING` or `ERROR` log entries in the last 1 minute  
**Severity:** High — degraded service, users receiving errors

---

## 1. Confirm the alert

Check Better Stack for the triggering logs — they will show which module is logging warnings and the error messages.

Then check Grafana → **Error Rate panel** at `http://<DROPLET_IP>:3000`:

- Is the error rate sustained or a one-time spike?
- Which time did it start?

---

## 2. SSH into the Droplet

```bash
ssh root@<DROPLET_IP>
cd MLH-PE-Hackathon-2026
```

---

## 3. Check live logs

```bash
docker logs --tail 100 mlh-pe-hackathon-2026-web-1 | grep -E "WARNING|ERROR"
docker logs --tail 100 mlh-pe-hackathon-2026-web-2 | grep -E "WARNING|ERROR"
```

Match the error pattern to the table below:

| Log message | Likely cause | Go to |
|-------------|-------------|-------|
| `connection to server...failed` | Database down or pool exhausted | §4 |
| `User not found` / `URL not found` | Bad client requests (expected) | §5 |
| `Could not generate unique short code` | Short code collision (rare) | §6 |
| `Internal server error` | Unhandled exception | §7 |
| Redis connection errors | Redis down | §8 |

---

## 4. Database issues

Check if DB is running:

```bash
docker ps | grep hackathon-db
curl -s http://localhost:8080/health
```

If DB is down:
```bash
docker start hackathon-db
```

If DB is up but connections are exhausted (pool full):
```bash
docker stats --no-stream | grep db
```
DB CPU exceeding 100% confirms connection pressure. Restart web containers to flush connections:
```bash
docker compose up -d --scale web=2 --force-recreate
```

---

## 5. High 404/422 rate from bad client requests

`WARNING` logs for `User not found`, `URL not found`, or validation errors are **expected** — they mean clients are sending bad requests, not that the app is broken.

Check if the volume is abnormal:
```bash
docker logs --tail 200 mlh-pe-hackathon-2026-web-1 | grep WARNING | wc -l
```

If it's a sudden spike of 404s from a single pattern, it may be a misconfigured client or a scan. No action needed unless it's saturating the DB.

---

## 6. Short code collision

Very rare. Happens when `POST /urls` fails to generate a unique short code after 10 attempts.

```bash
docker logs mlh-pe-hackathon-2026-web-1 | grep "short code"
```

If seen repeatedly, the short code space may be saturated. No immediate fix — note it and address short code length in the codebase.

---

## 7. Unhandled exception (500 errors)

```bash
docker logs --tail 100 mlh-pe-hackathon-2026-web-1 | grep "Internal server error"
```

Look for a Python traceback immediately above the error line. This is a code bug — fix and redeploy via CI or manually:

```bash
git pull origin main
docker compose build --no-cache web
docker compose up web -d --scale web=2
```

---

## 8. Redis down

```bash
docker ps | grep redis
docker start mlh-pe-hackathon-2026-redis-1
```

The app degrades gracefully without Redis (falls back to DB for all reads) but error rate will increase under load. Restore Redis to reduce DB pressure.

---

## 9. Verify recovery

```bash
docker logs --tail 50 mlh-pe-hackathon-2026-web-1 | grep -E "WARNING|ERROR"
```

Check Grafana — error rate should drop. Better Stack auto-resolves after 2 minutes with no new matching logs.
