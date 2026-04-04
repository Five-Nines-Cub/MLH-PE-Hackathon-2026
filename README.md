# MLH PE Hackathon — URL Shortener API

A URL shortener REST API built with Flask, Peewee ORM, and PostgreSQL.

**Stack:** Flask · Peewee ORM · PostgreSQL · uv

---

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url> && cd mlh-pe-hackathon

# 2. Copy environment config
cp .env.example .env

# 3. Start the docker container
docker compose up --build

# 4. Verify
curl http://localhost:8080/health
# → {"status":"ok"}
```

---

## API Reference

### Health

| Method | Endpoint  | Description |
|--------|-----------|-------------|
| GET    | `/health` | Returns `{"status":"ok"}` |

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

| Method | Endpoint       | Description                              |
|--------|----------------|------------------------------------------|
| GET    | `/urls`        | List all URLs (optional `?user_id=`)     |
| GET    | `/urls/<id>`   | Get URL by ID                            |
| POST   | `/urls`        | Create a short URL (auto-generates code) |
| PUT    | `/urls/<id>`   | Update title or is_active                |

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

```bash
uv sync --group dev
```

### Unit Tests
No database or Docker required — tests run entirely in-memory.

```bash
uv run pytest -m unit
```

### System Tests
Require the test database container to be running (separate from the app DB).

```bash
docker compose up db_test -d
uv run pytest -m system
```

The test DB runs on port `5433` with database `hackathon_test_db`. Tables are created and dropped automatically between tests.

### All Tests
```bash
docker compose up db_test -d
uv run pytest
```

### Load Tests
Requires the full stack (`web` + `db`) to be running.

```bash
docker compose up --build -d
docker compose run --rm k6 run --summary-export=/out/results.json /load_test_k6.js
```

CI runs automatically on every push via GitHub Actions.

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
│   └── test_events.py
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── load_test_k6.js
├── pyproject.toml
└── .env.example
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package manager
- Docker — for running PostgreSQL
