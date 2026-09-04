from uuid import uuid4

from dependency_container import Dependency

from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus
from src.domains.requests.queries.get_requests_created_by.handler import (
    GetRequestsCreatedByQueryHandler,
)
from src.domains.requests.queries.get_requests_created_by.query import (
    GetRequestsCreatedByQuery,
)


async def test_get_requests_created_by_filters_and_paginates(
    command_requests_repository: CommandRequestsRepository,
) -> None:
    matching_ids = []
    for type in ("LEAVE", "SHIFT_CORRECTION"):
        request = RequestEntity(
            id=uuid4(),
            type=type,
            status=RequestStatus.PENDING,
            data={},
            created_by_id="employee-1",
            reviewed_by_id="manager-1",
        )
        await command_requests_repository.save(request)
        matching_ids.append(request.id)

    await command_requests_repository.save(
        RequestEntity(
            id=uuid4(),
            type="LEAVE",
            status=RequestStatus.APPROVED,
            data={},
            created_by_id="employee-1",
            reviewed_by_id="manager-1",
        )
    )
    await command_requests_repository.save(
        RequestEntity(
            id=uuid4(),
            type="LEAVE",
            status=RequestStatus.PENDING,
            data={},
            created_by_id="employee-2",
            reviewed_by_id="manager-1",
        )
    )

    handler = Dependency.get(GetRequestsCreatedByQueryHandler)
    result = await handler.handle(
        GetRequestsCreatedByQuery(
            created_by_id="employee-1",
            status=RequestStatus.PENDING,
            reviewed_by_id="manager-1",
            sort_direction="asc",
            limit=1,
            offset=1,
        )
    )

    assert result.total == 2
    assert result.limit == 1
    assert result.offset == 1
    assert len(result.items) == 1
    assert result.items[0].id in matching_ids
    assert result.items[0].created_by_id == "employee-1"
    assert result.items[0].status is RequestStatus.PENDING
    assert result.items[0].created_at is not None
    assert result.items[0].updated_at is not None
