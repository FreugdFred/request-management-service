# Request Management Service API

Create, review, and retrieve employee requests such as leave, overtime, and
shift corrections through an HTTP API.

## Start the service

Python 3.13+, uv, and PostgreSQL are required.

Create a PostgreSQL database and set `DATABASE_URL` in your environment:

```text
DATABASE_URL=postgresql+asyncpg://request_management:request_management@localhost:5432/request_management
```

Then install dependencies, prepare the database, and start the service:

```console
uv sync
uv run alembic upgrade head
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Useful endpoints:

- API documentation: <http://localhost:8000/docs>
- OpenAPI document: <http://localhost:8000/openapi.json>
- Health check: <http://localhost:8000/health>

## Authentication

Authentication is disabled when `API_KEY` is unset. When configured, send it
on request endpoints as the `X-API-Key` header. The health endpoint remains
available without an API key.

## Create a request

Provide a new UUID, a request type of your choosing, a status, and the creator's
ID. Use `data` for request-specific information.

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

## Update or review a request

Send `POST /request/save` with the existing `id` and the fields to change.
Omitted fields stay unchanged. Send `note: null` or `reviewed_by_id: null` to
clear those values.

To approve a request, for example:

```json
{
  "id": "018f6f1e-7f89-7f44-a5b9-c62a854d24d8",
  "status": "APPROVED",
  "reviewed_by_id": "manager-123"
}
```

Statuses are `PENDING`, `APPROVED`, and `REJECTED`. Once approved or rejected,
a request cannot change to another status; attempts return HTTP 409.

## Endpoints

| Method | Path | Use |
| --- | --- | --- |
| `POST` | `/request/save` | Create or update a request. |
| `DELETE` | `/request/remove?id={request_id}` | Delete a request; already missing requests also succeed. |
| `GET` | `/request/{request_id}` | Get a request, or HTTP 404 if missing. |
| `GET` | `/request` | List requests with optional filters. |
| `GET` | `/request/types` | List distinct request types. |
| `GET` | `/health` | Check service health. |

`GET /request` accepts optional `created_by_id` and `reviewed_by_id` filters.
Omit both to list all requests, or supply both to match the creator and reviewer:

```http
GET /request
GET /request?created_by_id=employee-123
GET /request?reviewed_by_id=manager-123
GET /request?created_by_id=employee-123&reviewed_by_id=manager-123
```

You can also filter by `status` and `type`, set `sort_direction` (`asc` or
`desc`), and paginate with `limit` (1-100, default 50) and `offset` (default 0).
Responses contain `items`, `total`, `limit`, and `offset`.

## Events

To receive notifications about request creation, changes, and deletion, set
`NATS_URL` (for example, `nats://localhost:4222`) and subscribe to
`Request-Management-Service-API.*`. If you change `PROJECT_NAME`, use that
value as the subject prefix.

Messages contain `id`, `type`, `subject` (the creator's ID),
`occurrence_datetime`, and `data`. Request fields, including `request_id`,
are inside `data`. Ignore duplicate messages with the same `id`.

## Configuration

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | none | PostgreSQL connection URL using `postgresql+asyncpg://`. |
| `NATS_URL` | No | none | Enables event notifications through NATS. |
| `EVENT_RETENTION_MINUTES` | No | `10` | How long to keep sent event records, in minutes; must be positive. |
| `API_KEY` | No | none | Enables `X-API-Key` authentication. |
| `PROJECT_NAME` | No | `Request-Management-Service-API` | API title and NATS subject prefix. |
| `LOG_LEVEL` | No | `INFO` | Application log level. |
| `DEBUG` | No | `false` | Enables debug mode. |
