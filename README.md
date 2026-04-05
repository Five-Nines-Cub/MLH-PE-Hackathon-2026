# MLH PE Hackathon — URL Shortener API

[![Better Stack Badge](https://uptime.betterstack.com/status-badges/v1/monitor/2j3wi.svg)](https://uptime.betterstack.com/?utm_source=status_badge). 


A URL shortener REST API built with Flask, Peewee ORM, and PostgreSQL.

**Stack:** Flask · Gunicorn · Peewee ORM · PostgreSQL · Redis · Nginx · Fluent Bit · uv

---

## Starting The Docker Container

```bash
# 1. Clone the repo
git clone <repo-url> && cd mlh-pe-hackathon

# 2. Copy environment config
cp .env.example .env

# 3. Start the docker container (starts 2 instances by default)
docker compose up --build

# 4. Start the docker container with a specified number of instances
docker compose up --build --scale web=<NumInstances>
```

---

## API Reference

### Health & Redirect

| Method | Endpoint        | Description |
|--------|-----------------|-------------|
| GET    | `/health`       | Returns `{"status":"ok"}` |
| GET    | `/<short_code>` | Redirects browser to original URL (301); 404 if inactive or not found |

---

### Users

| Method | Endpoint          | Description              |
|--------|-------------------|--------------------------|
| GET    | `/users`          | List all users (optional `?page=&per_page=`) |
| GET    | `/users/<id>`     | Get user by ID           |
| POST   | `/users`          | Create a user            |
| PUT    | `/users/<id>`     | Update a user            |
| DELETE | `/users/<id>`     | Delete a user            |
| POST   | `/users/bulk`     | Bulk import from CSV     |

**Create user body:**
```json
{ "username": "alice", "email": "alice@example.com" }
```

**Bulk import:**
```bash
curl -X POST http://localhost:8080/users/bulk -F "file=@users.csv"
```

---

### URLs

| Method | Endpoint                      | Description                              |
|--------|-------------------------------|------------------------------------------|
| GET    | `/urls`                       | List all URLs — filter via query params or JSON body: `user_id`, `is_active=true\|false` |
| GET    | `/urls/<id>`                  | Get URL by ID                            |
| POST   | `/urls`                       | Create a short URL (auto-generates 6-char code) |
| PUT    | `/urls/<id>`                  | Update `title` or `is_active`            |
| DELETE | `/urls/<id>`                  | Delete a URL and its events (idempotent, always 204) |

**Create URL body:**
```json
{ "user_id": 1, "original_url": "https://example.com", "title": "Example" }
```

---

### Events

| Method | Endpoint   | Description       |
|--------|------------|-------------------|
| GET    | `/events`  | List all events — filter via query params or JSON body: `url_id`, `user_id`, `event_type` |
| POST   | `/events`  | Create an event   |

Events are created automatically when a URL is created (`event_type: "created"`). Additional events (e.g. `click`, `view`) can be created manually.

**Create event body:**
```json
{ "url_id": 1, "user_id": 1, "event_type": "click", "details": { "referrer": "https://google.com" } }
```

`user_id` and `details` are optional.

---

## Seed Data

> **Note:** Seed data loads automatically on first startup via `seed/init.sql`. It only runs once when the database volume is empty.

**Fresh setup (first time or full reset):**
```bash
docker compose down -v && docker compose up --build
```
⚠️ `-v` deletes all existing data. Only use this for a clean slate.

**Already have data and just want to reseed manually:**

```bash
# Copy CSVs into the db container
docker cp users.csv hackathon-db:/tmp/users.csv
docker cp urls.csv hackathon-db:/tmp/urls.csv
docker cp events.csv hackathon-db:/tmp/events.csv

# Import in order (users → urls → events)
docker exec hackathon-db psql -U postgres -d hackathon_db -c "\COPY users(id,username,email,created_at) FROM '/tmp/users.csv' CSV HEADER;"
docker exec hackathon-db psql -U postgres -d hackathon_db -c "SELECT setval(pg_get_serial_sequence('users','id'), (SELECT MAX(id) FROM users));"

docker exec hackathon-db psql -U postgres -d hackathon_db -c "\COPY urls(id,user_id,short_code,original_url,title,is_active,created_at,updated_at) FROM '/tmp/urls.csv' CSV HEADER;"
docker exec hackathon-db psql -U postgres -d hackathon_db -c "SELECT setval(pg_get_serial_sequence('urls','id'), (SELECT MAX(id) FROM urls));"

docker exec hackathon-db psql -U postgres -d hackathon_db -c "\COPY events(id,url_id,user_id,event_type,timestamp,details) FROM '/tmp/events.csv' CSV HEADER;"
docker exec hackathon-db psql -U postgres -d hackathon_db -c "SELECT setval(pg_get_serial_sequence('events','id'), (SELECT MAX(id) FROM events));"
```

---

## Running Specific Services

The `docker-compose.yml` defines the following services: `db`, `web`, `nginx`, `redis`, `fluent-bit`, `db_test`, and `k6`. You rarely need all of them at once.

**App only (db + redis + web + nginx) — typical dev workflow:**
```bash
docker compose up db redis web nginx --build
```

**With log shipping to Better Stack:**
```bash
docker compose up db redis web nginx fluent-bit --build
```

**App DB only — if you just need Postgres for local development:**
```bash
docker compose up db -d
```

**Test DB only — for system tests without spinning up the full app:**
```bash
docker compose up db_test -d
```

**Stop and remove a specific service:**
```bash
docker compose stop db_test
docker compose rm -f db_test
```

---

## Running Tests

### Unit Tests
These tests test the smallest parts of the functionality in our program (functions, methods, classes etc). No database or Docker required to run these tests.

```bash
# 1. Install prerequisite packages
uv sync --group dev

# 2. Run unit tests
uv run pytest -m unit

# Run with coverage
uv run pytest -m unit --cov

# Run a single test file
uv run pytest tests/test_unit.py

# Run a single test by name
uv run pytest tests/<Test File>.py::<Test Name>
# Example:
uv run pytest tests/test_urls.py::test_create_url_valid
```

### System Tests
These tests test the api endpoints of our program. It requires the test database container to be running (separate from the app DB). 

```bash
# 1. Install prerequisite packages
uv sync --group dev

# 2. Start up the test docker container
docker compose up db_test -d

# 3. Run system tests
uv run pytest -m system

# Run with coverage
uv run pytest -m system --cov

# Run system tests for a single resource
uv run pytest tests/test_users.py
uv run pytest tests/test_urls.py
uv run pytest tests/test_events.py

# Run a single test by name
uv run pytest -m system -k "test_name"
```

System tests run on a separate test_DB on port `5433` with database `hackathon_test_db`. Tables are created and dropped automatically between tests.

### Load Tests
Before running the load tests, ensure that the docker instance is running. Follow the instructions in [Starting The Docker Container](#starting-the-docker-container) to start the docker instance. When starting the docker container, you can specify a specific number of instances.  

```bash
# Run the load tests using k6. default concurrent users = 50
docker compose run --rm k6 run --summary-export=/out/results.json /load_test_k6.js

# Run the load tests with a specified number of concurrent users . Replace <ConcurrentUsers> with an int
docker compose run --rm -e VUS=<ConcurrentUsers> k6 run --summary-export=/out/results.json /load_test_k6.js
```

Tests run against a real PostgreSQL instance using the same `DATABASE_*` env vars. CI runs automatically on every push via GitHub Actions.

---

## Project Structure

```
├── app/
│   ├── __init__.py        # App factory
│   ├── database.py        # DB proxy, BaseModel, connection hooks
│   ├── cache.py           # wrapper for redis cache calls
│   ├── logging.py         # configures the logger
│   ├── models/
│   │   ├── user.py
│   │   ├── url.py
│   │   └── event.py
│   └── routes/
│       ├── users.py
│       ├── urls.py
│       ├── events.py
│       └── metrics.py
├── tests/
│   ├── conftest.py        # system test fixtures (test DB setup)
│   ├── test_unit.py       # pure unit tests (no DB)
│   ├── test_health.py
│   ├── test_users.py
│   ├── test_urls.py
│   └── test_events.py
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Dockerfile
├── load_test_k6.js
├── pyproject.toml
├── nginx.conf
├── fluent-bit.conf    # Fluent Bit log shipper config (ships to Better Stack)
├── parsers.conf       # Fluent Bit JSON parser (unwraps app JSON logs)
└── .env.example
```

## Logging & Observability

The app emits structured JSON logs on every request via a custom `JSONFormatter` (`app/logging.py`):

```json
{"timestamp": "2026-04-05T11:27:45.119721", "level": "INFO", "message": "Created user id=1 username=alice", "module": "users"}
```

Log levels used:
- `INFO` — successful operations (user created, URL created, cache hits)
- `WARNING` — client errors (validation failures, 404s, 409 conflicts)

**View logs locally:**
```bash
docker compose logs -f web
```

**View logs without SSH (production):**
Logs are shipped to [Better Stack](https://betterstack.com) via Fluent Bit. Requires `BETTERSTACK_TOKEN` and `BETTERSTACK_HOST` set as environment variables (or GitHub secrets for CI).

**Metrics endpoint:**
```bash
curl http://localhost:8080/metrics/
# {"cpu_percent": 0.3, "ram_percent": 19.1, "ram_total": ..., "ram_used": ...}
```

---

## Error Handling

All errors are returned as JSON — never HTML.

### 404 — Not Found

Two layers handle 404s:

1. **Route-level** — each handler catches Peewee's `DoesNotExist` and returns a specific message.
2. **Global fallback** — `@app.errorhandler(404)` catches any unmatched route and returns `{"error": "Not found"}`.

| Endpoint | Trigger |
|----------|---------|
| `GET /users/<id>` | User ID not in DB |
| `PUT /users/<id>` | User ID not in DB |
| `GET /urls/<id>` | URL ID not in DB |
| `PUT /urls/<id>` | URL ID not in DB |
| `POST /urls` | `user_id` references a non-existent user |
| `POST /events` | `url_id` or `user_id` references a non-existent record |
| `GET /<short_code>` | Short code not found or URL is inactive |
| Any unknown route | No matching Flask route |

### 500 — Internal Server Error

Two layers handle 500s:

1. **Route-level** — `POST /urls` explicitly returns 500 if short code generation fails after 10 collision attempts.
2. **Global fallback** — `@app.errorhandler(500)` catches any unhandled exception and returns `{"error": "Internal server error"}`.

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- Docker — for running PostgreSQL
