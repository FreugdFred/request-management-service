from typing import Annotated
from uuid import UUID

from dependency_container import Dependency
from fastapi import APIRouter, Depends

from src.domains.requests.commands.delete_request.command import DeleteRequestCommand
from src.domains.requests.commands.delete_request.handlers import (
    DeleteRequestCommandHandler,
)
from src.domains.requests.commands.save_request.command import SaveRequestCommand
from src.domains.requests.commands.save_request.handlers import (
    SaveRequestCommandHandler,
)
from src.domains.requests.queries.get_request_by_id.handler import (
    GetRequestByIdQueryHandler,
)
from src.domains.requests.queries.get_request_by_id.query import GetRequestByIdQuery
from src.domains.requests.queries.get_request_types.handler import (
    GetRequestTypesQueryHandler,
)
from src.domains.requests.queries.get_request_types.query import GetRequestTypesQuery
from src.domains.requests.queries.get_requests.handler import GetRequestsQueryHandler
from src.domains.requests.queries.get_requests.query import GetRequestsQuery
from src.domains.requests.query_models import PaginatedQueryModel, RequestQueryModel
from src.domains.requests.schemas import (
    PaginationInput,
    RequestsFiltersInput,
    RequestTypesFiltersInput,
    SaveRequestInput,
)

request_router = APIRouter(prefix="/request", tags=["request"])


@request_router.post("/save")
async def save_request(input: SaveRequestInput) -> None:
    handler = Dependency.get(SaveRequestCommandHandler)
    command = SaveRequestCommand.model_validate(input.model_dump(exclude_unset=True))
    await handler.handle(command)


@request_router.delete("/remove")
async def delete_request(id: UUID) -> None:
    handler = Dependency.get(DeleteRequestCommandHandler)
    await handler.handle(DeleteRequestCommand(id=id))


@request_router.get("/types", response_model=list[str])
async def get_request_types(
    filters: Annotated[RequestTypesFiltersInput, Depends()],
) -> list[str]:
    handler = Dependency.get(GetRequestTypesQueryHandler)
    return await handler.handle(
        GetRequestTypesQuery(
            created_by_id=filters.created_by_id,
            reviewed_by_id=filters.reviewed_by_id,
            status=filters.status,
        )
    )


@request_router.get("", response_model=PaginatedQueryModel[RequestQueryModel])
async def get_requests(
    filters: Annotated[RequestsFiltersInput, Depends()],
    pagination: Annotated[PaginationInput, Depends()],
) -> PaginatedQueryModel[RequestQueryModel]:
    handler = Dependency.get(GetRequestsQueryHandler)
    return await handler.handle(
        GetRequestsQuery(
            created_by_id=filters.created_by_id,
            reviewed_by_id=filters.reviewed_by_id,
            status=filters.status,
            type=filters.type,
            sort_direction=filters.sort_direction,
            limit=pagination.limit,
            offset=pagination.offset,
        )
    )


@request_router.get("/{id}", response_model=RequestQueryModel)
async def get_request(id: UUID) -> RequestQueryModel:
    handler = Dependency.get(GetRequestByIdQueryHandler)
    return await handler.handle(GetRequestByIdQuery(id=id))
