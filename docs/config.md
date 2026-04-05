# Configuration

All environment variables are configured in a `.env` file at the project root. Copy `.env.example` to get started:
```bash
cp .env.example .env
```

---

## Environment Variables

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_HOST` | `localhost` | Hostname of the PostgreSQL server. Set to `hackathon-db` when running in Docker |
| `DATABASE_PORT` | `5432` | Port the PostgreSQL server is listening on |
| `DATABASE_NAME` | `hackathon_db` | Name of the database to connect to |
| `DATABASE_USER` | `postgres` | PostgreSQL username |
| `DATABASE_PASSWORD` | `postgres` | PostgreSQL password |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `redis` | Hostname of the Redis server. Set to `redis` when running in Docker |
| `REDIS_PORT` | `6379` | Port the Redis server is listening on |
| `REDIS_DB` | `0` | Redis logical database index |
| `REDIS_TTL` | `60` | Time-to-live in seconds for cached entries. Set to `300` in `docker-compose.yml` |

### Flask

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_APP` | `app:create_app` | Entry point for the Flask application |
| `FLASK_RUN_HOST` | `0.0.0.0` | Host Flask binds to when using `flask run` |
| `FLASK_RUN_PORT` | `5000` | Port Flask listens on when using `flask run` |
| `FLASK_DEBUG` | — | Set to `1` to enable debug mode. Do not set in production |

### Python

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Disables Python output buffering so logs appear immediately in Docker. Should always be `1` in Docker |
| `SKIP_DB_INIT` | — | Set to any value to skip DB table creation and connection hooks on startup. Used in test environments |

### Better Stack (Log Shipping)

| Variable | Default | Description |
|----------|---------|-------------|
| `BETTERSTACK_TOKEN` | — | Source token for authenticating with Better Stack log ingestion. Set as a GitHub Secret in production |
| `BETTERSTACK_HOST` | — | Better Stack ingestion hostname (e.g. `in.logs.betterstack.com`). Set as a GitHub Secret in production |

### Grafana

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAFANA_PASSWORD` | — | Admin password for the Grafana dashboard at `:3000`. Set as a GitHub Secret in production |

---

## Test Database

The test database uses hardcoded values and is not configurable via `.env`. It runs as a separate Docker service on port `5433`.

| Variable | Value |
|----------|-------|
| `POSTGRES_USER` | `postgres` |
| `POSTGRES_PASSWORD` | `postgres` |
| `POSTGRES_DB` | `hackathon_test_db` |
| Port | `5433` |

---

## Example `.env`
```env
# Database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=hackathon_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL=300

# Flask
FLASK_APP=app:create_app
FLASK_DEBUG=0

# Better Stack
BETTERSTACK_TOKEN=your_token_here
BETTERSTACK_HOST=in.logs.betterstack.com

# Grafana
GRAFANA_PASSWORD=your_password_here
```

> **Note:** When running via `docker compose`, `DATABASE_HOST` should be `hackathon-db` and `REDIS_HOST` should be `redis` to match the Docker service names. For local development outside Docker, use `localhost` for both.