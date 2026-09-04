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
from src.domains.requests.queries.get_requests_created_by.handler import (
    GetRequestsCreatedByQueryHandler,
)
from src.domains.requests.queries.get_requests_created_by.query import (
    GetRequestsCreatedByQuery,
)
from src.domains.requests.queries.get_requests_reviewed_by.handler import (
    GetRequestsReviewedByQueryHandler,
)
from src.domains.requests.queries.get_requests_reviewed_by.query import (
    GetRequestsReviewedByQuery,
)
from src.domains.requests.query_models import PaginatedQueryModel, RequestQueryModel
from src.domains.requests.schemas import (
    CreatedRequestsFiltersInput,
    PaginationInput,
    RequestTypesFiltersInput,
    ReviewedRequestsFiltersInput,
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


@request_router.get(
    "/created-by/{created_by_id}",
    response_model=PaginatedQueryModel[RequestQueryModel],
)
async def get_requests_created_by(
    created_by_id: str,
    filters: Annotated[CreatedRequestsFiltersInput, Depends()],
    pagination: Annotated[PaginationInput, Depends()],
) -> PaginatedQueryModel[RequestQueryModel]:
    handler = Dependency.get(GetRequestsCreatedByQueryHandler)
    return await handler.handle(
        GetRequestsCreatedByQuery(
            created_by_id=created_by_id,
            status=filters.status,
            type=filters.type,
            reviewed_by_id=filters.reviewed_by_id,
            sort_direction=filters.sort_direction,
            limit=pagination.limit,
            offset=pagination.offset,
        )
    )


@request_router.get(
    "/reviewed-by/{reviewed_by_id}",
    response_model=PaginatedQueryModel[RequestQueryModel],
)
async def get_requests_reviewed_by(
    reviewed_by_id: str,
    filters: Annotated[ReviewedRequestsFiltersInput, Depends()],
    pagination: Annotated[PaginationInput, Depends()],
) -> PaginatedQueryModel[RequestQueryModel]:
    handler = Dependency.get(GetRequestsReviewedByQueryHandler)
    return await handler.handle(
        GetRequestsReviewedByQuery(
            reviewed_by_id=reviewed_by_id,
            status=filters.status,
            type=filters.type,
            created_by_id=filters.created_by_id,
            sort_direction=filters.sort_direction,
            limit=pagination.limit,
            offset=pagination.offset,
        )
    )


@request_router.get("/{id}", response_model=RequestQueryModel)
async def get_request(id: UUID) -> RequestQueryModel:
    handler = Dependency.get(GetRequestByIdQueryHandler)
    return await handler.handle(GetRequestByIdQuery(id=id))
