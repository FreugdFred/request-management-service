from src.domains.requests.queries.get_requests.query import (
    GetRequestsQuery,
)
from src.domains.requests.query_models import PaginatedQueryModel, RequestQueryModel
from src.domains.requests.query_repository import QueryRequestsRepository


class GetRequestsQueryHandler:
    def __init__(self, repository: QueryRequestsRepository) -> None:
        self._repository = repository

    async def handle(
        self, query: GetRequestsQuery
    ) -> PaginatedQueryModel[RequestQueryModel]:
        return await self._repository.get_many(
            created_by_id=query.created_by_id,
            status=query.status,
            type=query.type,
            reviewed_by_id=query.reviewed_by_id,
            sort_direction=query.sort_direction,
            limit=query.limit,
            offset=query.offset,
        )
