## 🚨 Failure Manual

This file documents how the system behaves under failure, how to reproduce issues, and how to recover.

---

## 🧱 System Components

* **web** – Flask app (Gunicorn, horizontally scalable)
* **nginx** – Load balancer
* **db** – PostgreSQL database
* **redis** – Cache layer
* **k6** – Load testing tool

---

## Failure Modes & Recovery

### 1. Web Container Failure

**Trigger**
TODO
```bash
docker stop mlh-pe-hackathon-2026-web-1 
```

**Behavior**
* One instance goes down
* Nginx routes traffic to remaining instances
* If there is only one instance, then the system will be unavailable

**Impact**

* Partial or full outage depending on number of replicas
* Increased load on other instances

**Recovery**
TODO
```bash
docker compose up -d --scale web=2
```

**Mitigation**

* Run multiple replicas
* Ensure proper restart handling for Gunicorn
* Notify on-call when servers have been down for 2+ hours (TODO: is 2 hours too long?) or 50%+ of servers are down

---

### 2. Database Failure

**Trigger**
TODO
```bash
docker stop hackathon-db
```

**Behavior**
* API returns 500 errors
* All DB queries fail

**Impact**
* Full outage

**Recovery**
TODO
```bash
docker start hackathon-db
```

**Mitigation**
* Add retry logic
* Use connection pooling
* Consider vertical scaling the database (future improvement)

---

### 3. Redis Failure (Cache Down)

**Trigger**
TODO
```bash
docker stop mlh-pe-hackathon-2026-redis-1
```

**Behavior**
* All cache calls will miss
* Api calls fall back to the database

**Impact**
* No outage, slower performance
* Latency, response time, and error rate can increase

**Recovery**
```bash
docker start mlh-pe-hackathon-2026-redis-1
```

**Mitigation**
TODO
* Graceful fallback (implemented)
* Monitor cache hit rate

---

### 4. Nginx Failure

**Trigger**
TODO
```bash
docker stop mlh-pe-hackathon-2026-nginx-1
```

**Behavior**
* No traffic reaches the app

**Impact**
* Full outage

**Recovery**

```bash
docker start mlh-pe-hackathon-2026-nginx-1
```

**Mitigation**
TODO: this doesn't make sense to me
* Validate configs before deploy
* Add health checks

---

### 5. High Load (200–500 Users)

**Trigger**
* Run k6 with high concurrency

**Behavior**
* Increased latency
* Possible error spikes
* High DB CPU usage

**Impact**
* Performance degradation

**Recovery**

```bash
docker compose up -d --scale web=4
```

**Mitigation**
* Redis caching (implemented)
* Scale web instances
* Optimize DB queries

---
(I stopped looking at stuff here)

### 6. Cold Cache / Cache Miss Surge

**Trigger**
* Redis restart or TTL expiration

**Behavior**
* Increased DB load
* Temporary latency spike

**Impact**
* Short-term slowdown

**Recovery**
* Automatic as cache warms

**Mitigation**
* Increase TTL (`REDIS_TTL`)
* Pre-warm cache for hot endpoints

---

### 7. Missing Seed Data

**Trigger**
* Reset DB volume or failed init scripts

**Behavior**
* Empty API responses

**Impact**
* App appears broken

**Recovery**
```bash
docker compose down -v
docker compose up --build
```

**Mitigation**
* Ensure seed scripts are in `/docker-entrypoint-initdb.d/`

---

### 8. Networking Issues
**Trigger**
* Using `localhost` instead of service names

**Behavior**
* Connection refused / EOF errors

**Impact**
* Services cannot communicate

**Fix**

* Use Docker service names:

  * `http://web:5000`
  * `http://nginx:80`

---

## 🛠 Debugging Commands

```bash
# View running containers
docker ps

# View logs
docker logs -f <container>

# Monitor resources
docker stats

# Test health endpoint
curl http://localhost:8080/health
```

