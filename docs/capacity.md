# Capacity Plan

This document summarizes load test results, identifies the system's limits, and describes the bottlenecks found.

---

## Test Setup

- **Tool:** k6 (via Docker)
- **Target:** Production server (`http://64.23.146.45:8080`)
- **Stack:** 2 × Flask/Gunicorn (4 workers × 4 threads) behind Nginx, backed by PostgreSQL + Redis

```bash
# Run load test
docker compose run --rm k6 run --summary-export=/out/results.json /load_test_k6.js

# With custom concurrency
docker compose run --rm -e VUS=500 k6 run --summary-export=/out/results.json /load_test_k6.js
```

---

## Results

| Concurrent Users | p95 Latency | Error Rate | Throughput |
|-----------------|-------------|------------|------------|
| 50 | 193.88ms | 0.00% | — |
| 200 | <1000ms | 0.00% | — |
| 500 | 936.32ms | 0.00% | 381 req/s |
| 1150 (breaking point) | — | ~0% | — |
| 1150–1500 | — | >10% (EOF + i/o timeout) | — |

All thresholds passed up to 500 VUs:
- `p(95) < 1000ms` ✅
- `error rate < 5%` ✅

---

## Bottlenecks Found

The following bottlenecks were identified iteratively by running k6 at 500 VUs, observing failure rates, applying a fix, and re-running.

| Iteration | Change | Error Rate | p95 |
|-----------|--------|------------|-----|
| Baseline | Flask dev server, 2 replicas | 43.62% | 4.62s |
| +Gunicorn (sync, 2 workers) | Switched from `flask run` to gunicorn | ~43% | ~4.5s |
| +Redis TTL 300s | Increased cache TTL from 60s → 300s | ~38% | ~4s |
| +Nginx tuning | `worker_processes auto`, keepalive, 1024 connections | ~25% | ~2s |
| +Gunicorn gthread (4 workers × 4 threads) | Replaced gevent with gthread | 20.02% | 658ms |
| +DB connection pooling (max 32) | `PooledPostgresqlDatabase` via Peewee | 2.60% | 769ms |
| +Nginx DNS fix | Force nginx restart on deploy to re-resolve Docker DNS | 0.00% | 936ms |

### Primary bottleneck: Database connections

Each request was opening a new Postgres connection. At 500 VUs this saturated the DB. Fixed with `PooledPostgresqlDatabase` capping at 32 connections shared across all Gunicorn workers. This was the single biggest fix — error rate dropped from 20% → 2.6%.

### Secondary bottleneck: Nginx DNS caching

Nginx resolved the `web` upstream hostname once at startup and cached it, routing 100% of traffic to a single replica. Fixed by restarting nginx on every deploy to force DNS re-resolution. This eliminated the remaining 2.6% error rate entirely.

---

## Estimated User Limits

Based on the load tests:

| Metric | Value |
|--------|-------|
| Max throughput (0% errors) | ~381 req/s |
| Safe concurrent users | 500+ |
| p95 latency at 500 VUs | 936ms |
| DB connection pool limit | 32 connections (shared across 2 replicas × 4 workers) |
| Redis cache TTL | 300s |

---

## Breaking Point Test (Ramping to 1500 VUs)

A ramp test was run directly against production to find the system's breaking point:

```
stages:
  - { duration: '20s', target: 500 }   // ramp up
  - { duration: '30s', target: 1500 }  // push to peak
  - { duration: '10s', target: 0 }     // ramp down
```

**Results:**
- Clean execution with 0% errors up to approximately **1150 VUs**
- At ~1150–1200 VUs, Nginx began dropping connections with **EOF errors** (connection reset before response)
- During ramp-down, 259 VUs got stuck in **i/o timeout** waiting for responses that never came
- The system recovered once VU count dropped back to 0

**Conclusion:** The current 2-replica setup (4 workers × 4 threads per replica) behind Nginx has a hard ceiling of approximately **1150 concurrent users** before connection errors appear. The primary limiting factor is Nginx's upstream connection capacity combined with the DB connection pool limit of 32.

---

## Scaling Recommendations

To handle more load beyond the current setup:

1. **Add more web replicas** — `docker compose up web -d --scale web=4`. Reduce per-instance DB pool size proportionally to stay within Postgres's `max_connections=100`.
2. **Increase Redis TTL** — reduces DB pressure for hot short codes.
3. **Upgrade the Droplet** — DB CPU exceeded 100% at 500 VUs with 2 replicas. More CPU headroom on the DB would raise the ceiling significantly.
4. **Separate DB onto its own Droplet** — currently DB and web share the same host, competing for CPU and memory.
