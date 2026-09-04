from src.domains.requests.queries.get_request_types.query import GetRequestTypesQuery
from src.domains.requests.query_repository import QueryRequestsRepository


class GetRequestTypesQueryHandler:
    def __init__(self, repository: QueryRequestsRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetRequestTypesQuery) -> list[str]:
        return await self._repository.get_types(
            created_by_id=query.created_by_id,
            reviewed_by_id=query.reviewed_by_id,
            status=query.status,
        )
