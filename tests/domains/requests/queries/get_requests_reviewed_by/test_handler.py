from uuid import uuid4

from dependency_container import Dependency

from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus
from src.domains.requests.queries.get_requests_reviewed_by.handler import (
    GetRequestsReviewedByQueryHandler,
)
from src.domains.requests.queries.get_requests_reviewed_by.query import (
    GetRequestsReviewedByQuery,
)


async def test_get_requests_reviewed_by_applies_all_filters(
    command_requests_repository: CommandRequestsRepository,
) -> None:
    expected = RequestEntity(
        id=uuid4(),
        type="LEAVE",
        status=RequestStatus.APPROVED,
        data={},
        created_by_id="employee-1",
        reviewed_by_id="manager-1",
    )
    await command_requests_repository.save(expected)

    for created_by_id, reviewed_by_id, status, type in (
        ("employee-2", "manager-1", RequestStatus.APPROVED, "LEAVE"),
        ("employee-1", "manager-2", RequestStatus.APPROVED, "LEAVE"),
        ("employee-1", "manager-1", RequestStatus.REJECTED, "LEAVE"),
        ("employee-1", "manager-1", RequestStatus.APPROVED, "OVERTIME"),
    ):
        await command_requests_repository.save(
            RequestEntity(
                id=uuid4(),
                type=type,
                status=status,
                data={},
                created_by_id=created_by_id,
                reviewed_by_id=reviewed_by_id,
            )
        )

    handler = Dependency.get(GetRequestsReviewedByQueryHandler)
    result = await handler.handle(
        GetRequestsReviewedByQuery(
            reviewed_by_id="manager-1",
            created_by_id="employee-1",
            status=RequestStatus.APPROVED,
            type="LEAVE",
        )
    )

    assert result.total == 1
    assert [request.id for request in result.items] == [expected.id]
    assert result.items[0].created_at is not None
    assert result.items[0].updated_at is not None
