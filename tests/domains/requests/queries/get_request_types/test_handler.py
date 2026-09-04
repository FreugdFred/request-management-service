from uuid import uuid4

from dependency_container import Dependency

from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus
from src.domains.requests.queries.get_request_types.handler import (
    GetRequestTypesQueryHandler,
)
from src.domains.requests.queries.get_request_types.query import GetRequestTypesQuery


async def test_get_request_types_returns_distinct_sorted_filtered_types(
    command_requests_repository: CommandRequestsRepository,
) -> None:
    for type in ("SHIFT_CORRECTION", "LEAVE", "LEAVE"):
        await command_requests_repository.save(
            RequestEntity(
                id=uuid4(),
                type=type,
                status=RequestStatus.PENDING,
                data={},
                created_by_id="employee-1",
                reviewed_by_id="manager-1",
            )
        )

    await command_requests_repository.save(
        RequestEntity(
            id=uuid4(),
            type="OVERTIME",
            status=RequestStatus.APPROVED,
            data={},
            created_by_id="employee-1",
            reviewed_by_id="manager-1",
        )
    )

    handler = Dependency.get(GetRequestTypesQueryHandler)
    result = await handler.handle(
        GetRequestTypesQuery(
            created_by_id="employee-1",
            reviewed_by_id="manager-1",
            status=RequestStatus.PENDING,
        )
    )

    assert result == ["LEAVE", "SHIFT_CORRECTION"]
