from src.domains.requests.queries.get_requests_created_by.query import (
    GetRequestsCreatedByQuery,
)
from src.domains.requests.query_models import PaginatedQueryModel, RequestQueryModel
from src.domains.requests.query_repository import QueryRequestsRepository


class GetRequestsCreatedByQueryHandler:
    def __init__(self, repository: QueryRequestsRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetRequestsCreatedByQuery) -> PaginatedQueryModel[RequestQueryModel]:
        return await self._repository.get_created_by(
            query.created_by_id,
            status=query.status,
            type=query.type,
            reviewed_by_id=query.reviewed_by_id,
            sort_direction=query.sort_direction,
            limit=query.limit,
            offset=query.offset,
        )
