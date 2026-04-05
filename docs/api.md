## Table of Contents
- [API Reference](#api-reference)
    - [Health](#health)
    - [Redirect](#redirect)
    - [Users](#users)
        - [GET /users](#get-users)
        - [GET /users/id](#get-usersid)
        - [POST /users](#post-users)
        - [PUT /users/id](#put-usersid)
        - [DELETE /users/id](#delete-usersid)
        - [POST /users/bulk](#post-usersbulk)
    - [URLs](#urls)
        - [GET /urls](#get-urls)
        - [GET /urls/id](#get-urlsid)
        - [POST /urls](#post-urls)
        - [PUT /urls/id](#put-urlsid)
        - [DELETE /urls/id](#delete-urlsid)
    - [Events](#events)
        - [GET /events](#get-events)
        - [POST /events](#post-events)
    - [Metrics](#metrics)
- [Error Handling](#error-handling)
    - [404 — Not Found](#404--not-found)
    - [500 — Internal Server Error](#500--internal-server-error)


---

# API Reference

Base url: TODO

---
## Health

### `GET /health`
Returns service status.


**Response**
| Code | Description |
|--------|-------------|
| `200 OK` | Service is running |

```json
{ "status": "ok" }
```

**curl**
```bash
curl http://localhost:8080/health
```
---
## Redirect

### `GET /<short_code>`
Redirects to the original URL (301). Returns 404 if the short code is inactive or not found.

**Request**
| Path Param  | Type | Required | Description |
|-------|------|----------|-------------|
| `short_code` | `string` | Yes | The 6-character short code |


**Response**
| Code | Description |
|--------|-------------|
| `301 Moved Permanently` | Redirects to the original URL |
| `404 Not Found` | Short code not found or URL is inactive |

```json
//404 Response Body
{ "error": "URL not found" }
```
**curl**
```bash
curl -L http://localhost:8080/OvfxQA
```
---
## Users

### `GET /users`
List all users. Supports pagination via query params.

**Request**
| Query Param | Type | Required | Description |
|-------------|------|----------|-------------|
| `page` | `int` | No | Page number (default: 1) |
| `per_page` | `int` | No | Results per page (default: 20) |

**Response** 
| Status | Description |
|--------|-------------|
| `200 OK` | Array of user objects |

```json
[
  {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com",
    "created_at": "2026-01-01T00:00:00"
  }
]
```

**curl**
```bash
# Minimal
curl http://localhost:8080/users

# With optional fields
curl "http://localhost:8080/users?page=2&per_page=10"
```

### `GET /users/<id>`
Get a single user by ID. Returns 404 if not found.

**Request**
| Path Param  | Type | Required | Description |
|-------|------|----------|-------------|
| `id`  | `int` | Yes | User ID |

**Response**

| Code | Description |
|--------|-------------|
| `200 OK` | User object |
| `404 Not Found` | User ID does not exist |

**Response**
```json
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-01-01T00:00:00"
}
```

**curl**
```bash
curl http://localhost:8080/users/1
```

### `POST /users`
Create a new user.

**Request**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | `string` | Yes | Unique username |
| `email` | `string` | Yes | Unique email address |


**Response**

| Code | Description |
|--------|-------------|
| `201 Created` | User created successfully |
| `409 Conflict` | Username or email already exists |
| `422 Unprocessable Entity` | Missing or invalid fields |

```json
//201 Response
{
  "id": 1,
  "username": "alice",
  "email": "alice@example.com",
  "created_at": "2026-01-01T00:00:00"
}
```

**curl**
```bash
curl -X POST http://localhost:8080/users \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@example.com"}'
```

### `PUT /users/<id>`
Update an existing user. Returns 404 if not found.

**Request** 
| Path Param  | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `int` | Yes | User ID |

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | `string` | No | New username |
| `email` | `string` | No | New email address |

**curl**
```bash
curl -X PUT http://localhost:8080/users/1 \
  -H "Content-Type: application/json" \
  -d '{"username": "alice2"}'
```

### `DELETE /users/<id>`
Delete a user by ID. Returns 404 if not found.

| Path Param  | Type | Required | Description |
|-------|------|----------|-------------|
| `id`  | `int` | Yes | User ID |

**Response**
| Status | Description |
|--------|-------------|
| `204 No Content` | Always — even if user did not exist |

**curl**
```bash
curl -X DELETE http://localhost:8080/users/1
```

### `POST /users/bulk`
Bulk import users from a CSV file. CSV must have headers: `username`, `email`.

**Request** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `file` | Yes | CSV file with `username` and `email` columns |

**Response**

| Code | Description |
|--------|-------------|
| `201 Created` | Users imported successfully |
| `200 OK` | File was valid but contained no rows |
| `400 Bad Request` | No file provided |

**Response**
```json
//201 response
{ "imported": 42 }
```
**curl**
```bash
curl -X POST http://localhost:8080/users/bulk \
  -F "file=@users.csv"
```

---
## URLs

### `GET /urls`
List all URLs. Supports optional filters.

| Query Param | Type | Required | Description |
|-------------|------|----------|-------------|
| `user_id` | `int` | No | Filter by user ID |
| `is_active` | `bool` | No | Filter by active status (`true` or `false`) |

**Response**

| Code | Description |
|--------|-------------|
| `200 OK` | Array of URL objects |

```json
[
  {
    "id": 1,
    "short_code": "OvfxQA",
    "original_url": "https://example.com",
    "title": "Example",
    "is_active": true,
    "user_id": 1,
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00"
  }
]
```

**curl**
```bash
curl http://localhost:8080/urls
curl "http://localhost:8080/urls?user_id=1&is_active=true"
```


### `GET /urls/<id>`
Get a single URL by ID. Returns 404 if not found.

**Request**
| Path Param  | Type | Required | Description |
|-------|------|----------|-------------|
| `id`  | `int` | Yes | URL ID |

**Response**

| Code | Description |
|--------|-------------|
| `200 OK` | URL object (may be served from Redis cache) |
| `404 Not Found` | URL ID does not exist |

```json
{
  "id": 1,
  "short_code": "OvfxQA",
  "original_url": "https://example.com",
  "title": "Example",
  "is_active": true,
  "user_id": 1,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

**curl**
```bash
curl http://localhost:8080/urls/1
```


### `POST /urls`
Create a new short URL. Auto-generates a 6-character short code.

**Request** `application/json`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | `int` | Yes | ID of the owning user |
| `original_url` | `string` | Yes | The full URL to shorten |
| `title` | `string` | No | Human-readable label |
| `is_active` | `bool` | No | Whether the short URL is active (default: `true`) |

**Response Codes**

| Status | Description |
|--------|-------------|
| `201 Created` | URL created successfully |
| `404 Not Found` | `user_id` does not exist |
| `422 Unprocessable Entity` | Missing required fields |
| `500 Internal Server Error` | Failed to generate a unique short code after 10 attempts |

**Response Body** `201`
```json
{
  "id": 1,
  "short_code": "OvfxQA",
  "original_url": "https://example.com",
  "title": "Example",
  "is_active": true,
  "user_id": 1,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `id` | `int` | URL ID |
| `short_code` | `string` | Auto-generated 6-character short code |
| `original_url` | `string` | The full destination URL |
| `title` | `string` | Human-readable label (may be `null`) |
| `is_active` | `bool` | Whether the short URL is active |
| `user_id` | `int` | ID of the owning user |
| `created_at` | `string` | ISO 8601 timestamp |
| `updated_at` | `string` | ISO 8601 timestamp |

**curl**
```bash
curl -X POST http://localhost:8080/urls \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "original_url": "https://example.com", "title": "Example"}'
```

---

### `PUT /urls/<id>`
Update a URL's title or active status. Invalidates the Redis cache for this URL.

**Request**

| Param | Location | Type | Required | Description |
|-------|----------|------|----------|-------------|
| `id` | path | `int` | Yes | URL ID |

`application/json` body:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | No | New title |
| `is_active` | `bool` | No | Enable or disable the short URL |

**Response Codes**

| Status | Description |
|--------|-------------|
| `200 OK` | Updated URL object |
| `404 Not Found` | URL ID does not exist |

**Response Body** `200`
```json
{
  "id": 1,
  "short_code": "OvfxQA",
  "original_url": "https://example.com",
  "title": "New Title",
  "is_active": false,
  "user_id": 1,
  "created_at": "2026-01-01T00:00:00",
  "updated_at": "2026-01-01T00:00:00"
}
```

| Key | Type | Description |
|-----|------|-------------|
| `id` | `int` | URL ID |
| `short_code` | `string` | Auto-generated 6-character short code |
| `original_url` | `string` | The full destination URL |
| `title` | `string` | Updated title (may be `null`) |
| `is_active` | `bool` | Updated active status |
| `user_id` | `int` | ID of the owning user |
| `created_at` | `string` | ISO 8601 timestamp |
| `updated_at` | `string` | ISO 8601 timestamp of last update |

**curl**
```bash
curl -X PUT http://localhost:8080/urls/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

### `DELETE /urls/<id>`
Delete a URL and all its associated events. Always returns 204 (idempotent).

**Request**

| Param | Location | Type | Required | Description |
|-------|----------|------|----------|-------------|
| `id` | path | `int` | Yes | URL ID |

**Response Codes**

| Status | Description |
|--------|-------------|
| `204 No Content` | Always — even if URL did not exist |

**curl**
```bash
curl -X DELETE http://localhost:8080/urls/1
```

---
## Events

### `GET /events`
List all events. Supports optional filters.

| Query Param | Type | Required | Description |
|-------------|------|----------|-------------|
| `url_id` | `int` | No | Filter by URL ID |
| `user_id` | `int` | No | Filter by user ID |
| `event_type` | `string` | No | Filter by type (e.g. `click`, `created`) |

**Response**

| Code | Description |
|--------|-------------|
| `200 OK` | Array of event objects |

```json
[
  {
    "id": 1,
    "url_id": 1,
    "user_id": 1,
    "event_type": "click",
    "timestamp": "2026-01-01T00:00:00",
    "details": { "referrer": "https://google.com" }
  }
]
```

**curl**
```bash
curl http://localhost:8080/events
curl "http://localhost:8080/events?url_id=1&event_type=click"
```

### `POST /events`
Create a new event. Events are also created automatically with `event_type: "created"` whenever a URL is created.

**Request** 

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url_id` | `int` | Yes | ID of the associated URL |
| `event_type` | `string` | Yes | Type of event (e.g. `click`, `view`) |
| `user_id` | `int` | No | ID of the associated user |
| `details` | `object` | No | Arbitrary JSON object with extra metadata |

> `details` must be a JSON object if provided — strings, arrays, and other types are rejected with 422.


**Response**

| Code | Description |
|--------|-------------|
| `201 Created` | Event created successfully |
| `404 Not Found` | `url_id` or `user_id` does not exist |
| `422 Unprocessable Entity` | Missing required fields or `details` is not a JSON object |

```json
{
  "id": 1,
  "url_id": 1,
  "user_id": 1,
  "event_type": "click",
  "timestamp": "2026-01-01T00:00:00",
  "details": { "referrer": "https://google.com" }
}
```

**curl**
```bash
# Minimal
curl -X POST http://localhost:8080/events \
  -H "Content-Type: application/json" \
  -d '{"url_id": 1, "event_type": "click"}'

# With optional fields
curl -X POST http://localhost:8080/events \
  -H "Content-Type: application/json" \
  -d '{"url_id": 1, "user_id": 1, "event_type": "click", "details": {"referrer": "https://google.com"}}'
```
---

## Metrics

### `GET /metrics`
Returns current system resource usage.

**Response**

| Code | Description |
|--------|-------------|
| `200 OK` | System metrics object |
| `500 Internal Server Error` | psutil not available |

```json
{
  "cpu_percent": 0.2,
  "ram_percent": 24.5,
  "ram_used": 2014597120,
  "ram_total": 8217448448
}
```

**curl**
```bash
curl http://localhost:8080/metrics
```
---

# Error Handling

All errors are returned as JSON — never HTML.

## 404 — Not Found

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

## 500 — Internal Server Error

Two layers handle 500s:

1. **Route-level** — `POST /urls` explicitly returns 500 if short code generation fails after 10 collision attempts.
2. **Global fallback** — `@app.errorhandler(500)` catches any unhandled exception and returns `{"error": "Internal server error"}`.

---