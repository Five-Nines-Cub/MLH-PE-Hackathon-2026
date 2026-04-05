# Decision Log

This document records the key technical decisions made during this project, including the context, the options considered, and the reasoning behind each choice.

---

## 1. Redis for Caching

**Decision:** Use Redis to cache URL lookups.

**Reasoning:**
URL redirects (`GET /<short_code>`) are the most frequent operation in a URL shortener and are read-heavy with low write frequency — an ideal cache use case. Redis provides a single shared cache that all workers and replicas can read from and write to. Redis is also an industry standard and is widely used. Cache entries are set with a configurable TTL (`REDIS_TTL`) and are explicitly invalidated on URL update or delete.

---

## 2. Nginx as a Reverse Proxy and Load Balancer

**Decision:** Use Nginx to sit in front of the web service.

**Options considered:**
- Nginx
- Digital Ocean Load Balancer

**Reasoning:**
Nginx handles load balancing across multiple web replicas, manages keepalive connections efficiently, and provides a single entry point on port 8080. Exposing Gunicorn directly would have meant no load balancing between replicas. The built-in load balancer provided by Digital Ocean was a viable option, however we chose not to use that due to the cost and because nginx was simple to configure. We configured Nginx with `least_conn` load balancing (routes each new request to the replica with the fewest active connections) rather than the default round-robin, which gives better distribution under variable request durations.

---

## 3. Gunicorn over Flask's Built-in Server
@Sanjeev PLS CHECK THIS TY
**Decision:** Use Gunicorn as the WSGI server in production.

**Options considered:**
- Gunicorn
- Flask's built-in development server
- uWSGI

**Reasoning:**
Flask's built-in server is single-threaded and not suitable for production workloads. Gunicorn provides multi-worker, multi-threaded request handling with minimal configuration. uWSGI is a valid alternative but is significantly more complex to configure. Gunicorn integrates cleanly with `uv run` and Docker, and supports both worker and thread-level concurrency (`--workers=4 --threads=4`).

---

## 4. Multiple Web Replicas

**Decision:** Run 2 web replicas by default via Docker Compose.

**Options considered:**
- Single instance
- Multiple replicas via Docker Compose
- Kubernetes

**Reasoning:**
Running multiple replicas improves availability and throughput. If one replica crashes, Nginx continues routing traffic to the remaining replica while Docker restarts the failed one. Kubernetes would provide more sophisticated orchestration but it seemed to complicated since we only really needed 2 instances to meet the scalability gold standard. Docker Compose's `deploy.replicas` gives us horizontal scaling with minimal configuration overhead.

---

## 5. uv as the Package Manager

**Decision:** Use `uv` instead of `pip` or `poetry`.

**Options considered:**
- uv
- pip + requirements.txt

**Reasoning:**
`uv` is significantly faster than pip for dependency resolution and installation, which matters in Docker builds where dependencies are installed from scratch on every image rebuild. It also provides lockfile support (`uv.lock`) out of the box, ensuring reproducible builds.

---

## 5. Fluent Bit as log shipper

**Decision:** Use Fluent Bit Log Shipper instead of _______.

**Options considered:**
- Use Fluent Bit Log Shipper
- ...

**Reasoning:**

---

## 5. Better Stack as log aggregator 

**Decision:** Better Stack instead of _______.

**Options considered:**
- Use Better Stack Log Aggregator
- ...

**Reasoning:**

