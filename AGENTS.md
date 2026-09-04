# Request Management Service: Architecture and Working Guide

This service is a FastAPI application built with SQLAlchemy, Pydantic, and a
small dependency-injection container. The code is organized by business
domain and follows CQRS: writes are commands and reads are queries.

## Service scope

The service owns employee requests. A request contains:

- a caller-provided UUID;
- an application-defined request type;
- a `PENDING`, `APPROVED`, or `REJECTED` status;
- optional notes and reviewer identity;
- request-specific JSON data;
- the identity of its creator; and
- database-managed creation and update timestamps.

Do not add shift or pause aggregates to this service. References to resources
owned by another service belong in request data or explicit identifiers; their
business rules remain in the owning service.

## How a request flows

Write requests follow this path:

`route -> input schema -> command -> command handler -> RequestEntity -> command repository`

Read requests follow this path:

`route -> query input -> query -> query handler -> query repository -> query model`

Keep these paths separate. Queries never mutate state. Commands return no read
projection when no response or an identifier is sufficient.

## Domain layout

Request code lives under `src/domains/requests/`:

```text
requests/
  commands/
    <use_case>/
      command.py
      handlers.py
  queries/
    <read_operation>/
      query.py
      handler.py
  entity.py
  events.py
  models.py
  mapper.py
  schemas.py
  query_models.py
  command_repository.py
  query_repository.py
  routes.py
  di.py
```

Do not add abstractions until there is a concrete use for them.

## CQRS conventions

- Commands describe an intent to change state, such as `SaveRequestCommand`
  and `DeleteRequestCommand`.
- Command handlers load the request entity, call entity behavior, persist it,
  and publish pulled domain events only after persistence succeeds.
- Queries describe one read operation and contain filtering and pagination
  values needed by that operation.
- Query handlers delegate reads to `QueryRequestsRepository`.
- Query repositories return query models, never entities or SQLAlchemy models.
- Routes resolve handlers through `Dependency`; they do not resolve
  repositories or contain business rules.

Current query use cases are:

- get a request by UUID;
- list requests created by an actor;
- list requests reviewed by an actor; and
- return distinct request types.

Paginated queries return `items`, `total`, `limit`, and `offset`. Use
`created_at` followed by `id` for deterministic ordering. Request projections
must expose both `created_at` and `updated_at` from `DbRequest`.

## Request aggregate behavior

`RequestEntity` owns request changes and records the corresponding domain
events. Use its factory and mutators instead of assigning fields directly in a
handler:

- `RequestEntity.create`
- `set_note`
- `set_type`
- `set_status`
- `set_data`
- `set_created_by_id`
- `set_reviewed_by_id`
- `delete`

Mutators must not record an event when the effective value does not change.
Copy mutable JSON data when accepting it or adding it to an event so later
mutation cannot alter entity history.

`reference_id` on a request event is the request's `created_by_id`. Every
request event also contains `request_id`; changed events contain the previous
and new values.

## Save behavior and validation

Saving is an upsert:

- a missing UUID creates a request and requires `type`, `status`, and
  `created_by_id`;
- an existing UUID applies only supplied update fields; and
- incomplete creates raise `ValidationException`.

For optional values, use explicit `is None` and `is not None` checks. For
partial updates, use Pydantic's `model_fields_set` or `exclude_unset=True` to
distinguish an omitted value from an explicitly supplied `null`, empty string,
empty object, or false value.

Validation belongs in the narrowest layer with enough information:

- schemas and command/query models validate input shape;
- `RequestEntity` enforces request lifecycle behavior;
- handlers coordinate operations that require loading a request; and
- repositories own SQL and persistence concerns.

Raise domain exceptions from entities and handlers. Map them to HTTP status
codes centrally in `src/exception_handlers.py`. Use `NotFoundException` for a
missing requested read and `ValidationException` for an incomplete create.

Delete operations are idempotent: deleting a missing request is a successful
no-op.

## Persistence and migrations

- Keep SQLAlchemy models in `models.py` and domain behavior in `entity.py`.
- Use `RequestMapper` only for command-side entity persistence.
- Build query projections directly from eagerly available database fields.
- Keep sessions short-lived and commit only after domain validation succeeds.
- Treat `created_at` and `updated_at` as database-managed values; do not add
  them to `RequestEntity` or command inputs.
- Use JSON-compatible request data and never mutate a caller-owned dictionary.
- Add an Alembic migration for every database schema or index change.
- Keep request migrations independent from migration histories owned by other
  services.
- Add indexes that match production query filters and ordering.

The workspace Compose setup may share one PostgreSQL server between services,
but each service should use its own database or schema and Alembic version
table. Do not point two independent Alembic histories at the same default
schema and `alembic_version` table.

## HTTP API

Current endpoints are:

- `POST /request/save`
- `DELETE /request/remove?id={request_id}`
- `GET /request/{request_id}`
- `GET /request/created-by/{created_by_id}`
- `GET /request/reviewed-by/{reviewed_by_id}`
- `GET /request/types`
- `GET /health`

Use Pydantic schemas for bodies and filter groups. Keep fixed paths such as
`/types`, `/created-by/...`, and `/reviewed-by/...` before the dynamic `/{id}`
route. Response models expose only intended API fields.

## Dependency injection

Every repository and handler used by a route must be registered in
`src/domains/requests/di.py`. `include_request_dependencies` must be called by
`src/dependencies.py`.

When adding an endpoint, verify:

1. The route resolves a handler, not a repository.
2. The handler and repository are registered.
3. The command or query name matches its CQRS side.
4. Omitted update fields retain their omission semantics.
5. The response model exposes only the intended fields.

## Coding practices

- Use timezone-aware datetimes. Domain event time comes from
  `AbstractTimeProvider`; never call `datetime.now()` directly in domain code.
- Use explicit optional-value checks instead of truthiness.
- Keep handlers small and SQL inside repositories.
- Never use Python dataclasses. Use Pydantic models, SQLAlchemy models, or
  regular behavior classes.
- Preserve existing user changes and avoid unrelated refactors.
- Do not reintroduce copied shift or pause code.

## Tests and checks

Mirror the source domain structure under `tests/`. Use pytest functions and
fixtures; do not write class-based tests.

Test business behavior through entities and handlers resolved from
`Dependency` with real repositories. Use an isolated SQLite database for
persistence tests. Do not use `unittest.mock`, `Mock`, `AsyncMock`, fake
repositories, or fake handlers. Override dependencies through `Dependency`.

Use the shared `FakeTimeProvider` configured in `tests/conftest.py`. Add a small
number of route tests for parsing, response shape, and dispatch without
duplicating every handler scenario. Query tests must verify timestamps when
the projection contract includes them. Do not add tests merely for mechanical
DI, SQL construction, logging, or migration wiring.

Before handing off a change, run:

```text
uv run ruff check src tests
uv run pyright src tests
uv run pytest
```

For schema changes, also run an Alembic upgrade and downgrade against an
isolated database. Application settings require `DATABASE_URL`; supply test
values through the environment or an uncommitted `.env` file and never put
credentials in source code or tests.
