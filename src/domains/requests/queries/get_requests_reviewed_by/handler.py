from src.domains.requests.queries.get_requests_reviewed_by.query import (
    GetRequestsReviewedByQuery,
)
from src.domains.requests.query_models import PaginatedQueryModel, RequestQueryModel
from src.domains.requests.query_repository import QueryRequestsRepository


class GetRequestsReviewedByQueryHandler:
    def __init__(self, repository: QueryRequestsRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetRequestsReviewedByQuery) -> PaginatedQueryModel[RequestQueryModel]:
        return await self._repository.get_reviewed_by(
            query.reviewed_by_id,
            status=query.status,
            type=query.type,
            created_by_id=query.created_by_id,
            sort_direction=query.sort_direction,
            limit=query.limit,
            offset=query.offset,
        )
