from dependency_container import Dependency

from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.commands.delete_request.handlers import (
    DeleteRequestCommandHandler,
)
from src.domains.requests.commands.save_request.handlers import (
    SaveRequestCommandHandler,
)
from src.domains.requests.queries.get_request_by_id.handler import (
    GetRequestByIdQueryHandler,
)
from src.domains.requests.queries.get_request_types.handler import (
    GetRequestTypesQueryHandler,
)
from src.domains.requests.queries.get_requests_created_by.handler import (
    GetRequestsCreatedByQueryHandler,
)
from src.domains.requests.queries.get_requests_reviewed_by.handler import (
    GetRequestsReviewedByQueryHandler,
)
from src.domains.requests.query_repository import QueryRequestsRepository


def include_request_dependencies() -> None:
    Dependency.register(CommandRequestsRepository, CommandRequestsRepository)
    Dependency.register(QueryRequestsRepository, QueryRequestsRepository)
    Dependency.register(DeleteRequestCommandHandler, DeleteRequestCommandHandler)
    Dependency.register(SaveRequestCommandHandler, SaveRequestCommandHandler)
    Dependency.register(GetRequestByIdQueryHandler, GetRequestByIdQueryHandler)
    Dependency.register(GetRequestTypesQueryHandler, GetRequestTypesQueryHandler)
    Dependency.register(
        GetRequestsCreatedByQueryHandler,
        GetRequestsCreatedByQueryHandler,
    )
    Dependency.register(
        GetRequestsReviewedByQueryHandler,
        GetRequestsReviewedByQueryHandler,
    )
