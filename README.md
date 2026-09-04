# Request Management Service API

The Request Management Service stores and retrieves employee requests such as
leave, overtime, and shift-correction requests. It exposes a FastAPI HTTP API,
persists data with SQLAlchemy, and publishes request lifecycle events to NATS
when NATS is configured.

## Start the service

Python 3.13+, uv, and PostgreSQL are required.

```console
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Set the database URL before running migrations or the service:

```text
DATABASE_URL=postgresql+asyncpg://request_management:request_management@localhost:5432/request_management
NATS_URL=nats://localhost:4222
```

Useful endpoints:

- API documentation: <http://localhost:8000/docs>
- OpenAPI document: <http://localhost:8000/openapi.json>
- Health check: <http://localhost:8000/health>

## Authentication

Authentication is disabled when `API_KEY` is unset. When configured, send it
on request endpoints as the `X-API-Key` header. The health endpoint remains
available without an API key.

## Request model

```json
{
  "id": "018f6f1e-7f89-7f44-a5b9-c62a854d24d8",
  "note": "Please correct Tuesday's shift",
  "type": "SHIFT_CORRECTION",
  "status": "PENDING",
  "data": {"shift_id": "shift-123"},
  "created_by_id": "employee-123",
  "reviewed_by_id": null
}
```

`type` is an application-defined string. `status` must be `PENDING`,
`APPROVED`, or `REJECTED`. Query responses also include `created_at` and
`updated_at` timestamps.

## API

### Save a request

`POST /request/save`

The endpoint is an upsert. Creating a request requires `id`, `type`, `status`,
and `created_by_id`. On an update, omitted fields remain unchanged; send
`note: null` or `reviewed_by_id: null` to clear those nullable values.

```console
curl -X POST "http://localhost:8000/request/save" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "018f6f1e-7f89-7f44-a5b9-c62a854d24d8",
    "type": "LEAVE",
    "status": "PENDING",
    "data": {"from": "2026-09-10", "through": "2026-09-12"},
    "created_by_id": "employee-123"
  }'
```

### Delete a request

`DELETE /request/remove?id={request_id}`

Deletion is idempotent: deleting an unknown request is a successful no-op.

### Get a request

`GET /request/{request_id}`

Returns one request or HTTP 404 when it does not exist.

### List requests created by an actor

`GET /request/created-by/{created_by_id}`

Optional query parameters are `status`, `type`, `reviewed_by_id`,
`sort_direction` (`asc` or `desc`), `limit` (1-100), and `offset`.

### List requests reviewed by an actor

`GET /request/reviewed-by/{reviewed_by_id}`

Optional query parameters are `status`, `type`, `created_by_id`,
`sort_direction` (`asc` or `desc`), `limit` (1-100), and `offset`.

Both list endpoints return:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

`total` counts every matching request before pagination. Results are ordered by
creation time and then request ID, making pagination deterministic.

### Get request types

`GET /request/types`

Returns distinct request types in alphabetical order. Optional filters are
`created_by_id`, `reviewed_by_id`, and `status`.

## Events

Successful commands publish events using the subject
`{PROJECT_NAME}.{EventClassName}` when `NATS_URL` is set. Request events include
created, changed, and deleted events. Every event contains `reference_id`,
`occurrence_datetime`, and `request_id`.

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | none | SQLAlchemy async database URL. |
| `NATS_URL` | No | none | NATS connection URL; publishing is disabled when unset. |
| `API_KEY` | No | none | Enables `X-API-Key` authentication. |
| `PROJECT_NAME` | No | `Request-Management-Service-API` | API title and NATS subject prefix. |
| `LOG_LEVEL` | No | `INFO` | Application log level. |
| `DEBUG` | No | `false` | Enables FastAPI debug mode. |

## Development checks

```console
uv run ruff check src tests
uv run pyright src tests
uv run pytest
```
