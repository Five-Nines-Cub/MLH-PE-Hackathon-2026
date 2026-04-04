# Hackathon Quest Progress

## Reliability
### 🥉 Tier 1: Bronze

| Objective | Status | Notes |
|-----------|--------|-------|
| Write unit tests with pytest | ✅ Done | 39 unit + system tests across health, users, urls, events |
| Set up GitHub Actions CI | ✅ Done | `.github/workflows/ci.yml` — runs on every push/PR |
| `GET /health` endpoint returns 200 | ✅ Done | `http://localhost:8080/health` |

#### Verification
Screenshot of `GET /health` returning 200:
![Health End Point](/report-images/Health_endpoint.png)

Screenshot of Github Action CI with passing tests:
![Github CI](/report-images/GithubCI.png)

## Scalability
### 🥉 Tier 1: Bronze

| Objective | Status | Notes |
|-----------|--------|-------|
| Set up k6 or Locust for load testing | ✅ Done | utilizes k6 docker image |
| Simulate 50 concurrent users hitting your service | ✅ Done | See image below |
| Document your Response Time (Latency) and Error Rate | ✅ Done | see image below |

## Scalability
### 🥉 Tier 1: Bronze

| Objective | Status | Notes |
|-----------|--------|-------|
| Set up k6 or Locust for load testing | ✅ Done | utilizes k6 docker image |
| Simulate 50 concurrent users hitting your service | ✅ Done | INSERT PHOTO |
| Document your Response Time (Latency) and Error Rate | ✅ Done | `http://localhost:8080/health` |


#### Verification  
Screenshot of terminal output showing 50 concurrent users:  
![50 concurrent users](/report-images/50_concurrent_test.png)

### 🥈 Tier 2: Silver

| Objective | Status | Notes |
|-----------|--------|-------|
| 200 concurrent users for load testing | TODO |  |
| Run 2+ instances of your app (containers) using Docker Compose | TODO |  |
| Put a Load Balancer (Nginx) in front to split traffic between instances | TODO |  |


Documented baseline p95 response time:  
```
  █ THRESHOLDS 

    http_req_duration
    ✓ 'p(95)<500' p(95)=193.88ms

    http_req_failed
    ✓ 'rate<0.01' rate=0.00%
```


---

