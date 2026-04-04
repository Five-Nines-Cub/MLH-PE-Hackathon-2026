# MLH PE Hackathon — URL Shortener API

A URL shortener REST API built with Flask, Peewee ORM, and PostgreSQL.

**Stack:** Flask · Peewee ORM · PostgreSQL · uv

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
| GET    | `/urls`                       | List all URLs (optional `?user_id=`)     |
| GET    | `/urls/<id>`                  | Get URL by ID                            |
| POST   | `/urls`                       | Create a short URL (auto-generates code) |
| PUT    | `/urls/<id>`                  | Update title or is_active                |

**Create URL body:**
```json
{ "user_id": 1, "original_url": "https://example.com", "title": "Example" }
```

---

### Events

| Method | Endpoint   | Description       |
|--------|------------|-------------------|
| GET    | `/events`  | List all events   |

Events are created automatically when a URL is created (`event_type: "created"`).

---

## Seed Data

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

## Running Tests

### Unit Tests
These tests test the smallest parts of the functionality in our program (functions, methods, classes etc). No database or Docker required to run these tests.

```bash
# 1. Install prerequisite packages
uv sync --group dev

# 2. Run unit tests
uv run pytest -m unit
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
│   ├── models/
│   │   ├── user.py
│   │   ├── url.py
│   │   └── event.py
│   └── routes/
│       ├── users.py
│       ├── urls.py
│       └── events.py
├── tests/
│   ├── conftest.py        # system test fixtures (test DB setup)
│   ├── test_unit.py       # pure unit tests (no DB)
│   ├── test_health.py
│   ├── test_users.py
│   ├── test_urls.py
│   ├── test_events.py
│   └── test_redirect.py
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── load_test_k6.js
├── pyproject.toml
├── nginx.conf
└── .env.example
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- Docker — for running PostgreSQL
