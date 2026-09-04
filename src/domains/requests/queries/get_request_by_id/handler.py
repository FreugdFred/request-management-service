from src.domains.requests.queries.get_request_by_id.query import GetRequestByIdQuery
from src.domains.requests.query_models import RequestQueryModel
from src.domains.requests.query_repository import QueryRequestsRepository
from src.exceptions import NotFoundException


class GetRequestByIdQueryHandler:
    def __init__(self, repository: QueryRequestsRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetRequestByIdQuery) -> RequestQueryModel:
        request = await self._repository.get(query.id)
        if request is None:
            raise NotFoundException(RequestQueryModel, str(query.id))

        return request
