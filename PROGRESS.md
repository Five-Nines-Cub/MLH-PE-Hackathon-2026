# Hackathon Quest Progress

## Reliability
### 🥉 Tier 1: Bronze

| Objective | Status | Notes |
|-----------|--------|-------|
| Write unit tests with pytest | ✅ Done | 84 unit + system tests across health, users, urls, events |
| Set up GitHub Actions CI | ✅ Done | `.github/workflows/ci.yml` — runs on every push/PR |
| `GET /health` endpoint returns 200 | ✅ Done | `http://localhost:8080/health` |

#### Verification  
Screenshot of `GET /health` returning 200:  
![Health End Point](/report-images/Health_endpoint.png)  

Screenshot of Github Action CI with passing tests:  
![Github CI](/report-images/GithubCI.png)  

### 🥈 Tier 2: Silver

| Objective | Status | Notes |
|-----------|--------|-------|
| 50% Coverage: Use pytest-cov | ✅ Done | `pytest-cov` added to dev dependencies |
| Integration Testing: Write tests that hit the API | ✅ Done | System tests use Flask `test_client()` against a real DB |
| The Gatekeeper: CI fails if tests fail | ⬜ Todo | |
| Error Handling: Document how app handles 404s and 500s | ✅ Done | [See README](README.md#error-handling) |

#### Verification  
Screenshot of 50% Coverage:  
![Code Coverage](/report-images/code_coverage.png)  

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
![50 concurrent users](/report-images/50_concurrent_test.png)

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
![50 Concurrent Users](/report-images/200_concurrent_test.png)

Screenshot of terminal output showing 2 docker containers and nginx container:  
![Docker and Nginx Containers](/report-images/docker_nginx_container.png)

### 🥇 Tier 3: Gold

| Objective | Status | Notes |
|-----------|--------|-------|
| Handle 500+ concurrent users (or 100 req/sec) | TODO |  |
| Implement Redis | ✅ Done | TODO: Link to documentation |
| Identifying Bottlenecks | ✅ Done |  |
| Error rate must stay under 5% | TODO |  |

#### Verification  
Evidence of caching:  
![Evidence Of Caching](/report-images/caching.png)

Screenshot of terminal output showing 500+ concurrent users:  
![Docker and Nginx Containers](/report-images/docker_nginx_container.png)

Bottleneck Report:  
I ran docker ps to identify which parts of the system were under the most stress. The image below was taken from a 500+ concurrent user run with 2 web server instances and a nginx load balancer. From the image below, we can see that the database's CPU exceeds 100%, meaning this is the likely source of the bottleneck. 

The webservers are also very overloaded, 

![Docker and Nginx Containers](/report-images/bottleneck.png)


---

