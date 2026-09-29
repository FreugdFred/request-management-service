from uuid import UUID, uuid4

import pytest
from dependency_container import Dependency

from src.core.unit_of_work import UnitOfWork
from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus
from src.domains.requests.queries.get_requests.handler import (
    GetRequestsQueryHandler,
)
from src.domains.requests.queries.get_requests.query import (
    GetRequestsQuery,
)


async def test_get_requests_filters_and_paginates(
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
        async with UnitOfWork() as session:
            await command_requests_repository.save(session, request)
        matching_ids.append(request.id)

    async with UnitOfWork() as session:
        await command_requests_repository.save(
            session,
            RequestEntity(
                id=uuid4(),
                type="LEAVE",
                status=RequestStatus.APPROVED,
                data={},
                created_by_id="employee-1",
                reviewed_by_id="manager-1",
            ),
        )
    async with UnitOfWork() as session:
        await command_requests_repository.save(
            session,
            RequestEntity(
                id=uuid4(),
                type="LEAVE",
                status=RequestStatus.PENDING,
                data={},
                created_by_id="employee-2",
                reviewed_by_id="manager-1",
            ),
        )

    handler = Dependency.get(GetRequestsQueryHandler)
    result = await handler.handle(
        GetRequestsQuery(
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


@pytest.mark.parametrize(
    ("created_by_id", "reviewed_by_id", "expected_ids"),
    [
        (None, None, [1, 2, 3, 4]),
        ("employee-1", None, [1, 2, 4]),
        (None, "manager-1", [1, 3]),
        ("employee-1", "manager-1", [1]),
        ("missing", None, []),
        ("", None, []),
        (None, "", []),
    ],
)
async def test_identity_filters_are_optional_and_combined(
    command_requests_repository: CommandRequestsRepository,
    created_by_id: str | None,
    reviewed_by_id: str | None,
    expected_ids: list[int],
) -> None:
    async with UnitOfWork() as session:
        for id, creator, reviewer in (
            (1, "employee-1", "manager-1"),
            (2, "employee-1", "manager-2"),
            (3, "employee-2", "manager-1"),
            (4, "employee-1", None),
        ):
            await command_requests_repository.save(
                session,
                RequestEntity(
                    id=UUID(int=id),
                    type="LEAVE",
                    status=RequestStatus.PENDING,
                    data={},
                    created_by_id=creator,
                    reviewed_by_id=reviewer,
                ),
            )

    result = await Dependency.get(GetRequestsQueryHandler).handle(
        GetRequestsQuery(
            created_by_id=created_by_id,
            reviewed_by_id=reviewed_by_id,
            sort_direction="asc",
        )
    )

    assert [request.id for request in result.items] == [
        UUID(int=id) for id in expected_ids
    ]
    assert result.total == len(expected_ids)
    assert result.limit == 50
    assert result.offset == 0


@pytest.mark.parametrize("sort_direction, expected_id", [("asc", 2), ("desc", 3)])
async def test_unfiltered_requests_preserve_sorting_and_pagination(
    command_requests_repository: CommandRequestsRepository,
    sort_direction: str,
    expected_id: int,
) -> None:
    async with UnitOfWork() as session:
        for id in range(1, 5):
            await command_requests_repository.save(
                session,
                RequestEntity(
                    id=UUID(int=id),
                    type="LEAVE",
                    status=RequestStatus.PENDING,
                    data={},
                    created_by_id=f"employee-{id}",
                ),
            )

    result = await Dependency.get(GetRequestsQueryHandler).handle(
        GetRequestsQuery.model_validate(
            {"sort_direction": sort_direction, "limit": 1, "offset": 1}
        )
    )

    assert [request.id for request in result.items] == [UUID(int=expected_id)]
    assert result.total == 4
    assert result.limit == 1
    assert result.offset == 1
    assert result.items[0].created_at is not None
    assert result.items[0].updated_at is not None


async def test_get_requests_applies_all_filters(
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
    async with UnitOfWork() as session:
        await command_requests_repository.save(session, expected)

    for created_by_id, reviewed_by_id, status, type in (
        ("employee-2", "manager-1", RequestStatus.APPROVED, "LEAVE"),
        ("employee-1", "manager-2", RequestStatus.APPROVED, "LEAVE"),
        ("employee-1", "manager-1", RequestStatus.REJECTED, "LEAVE"),
        ("employee-1", "manager-1", RequestStatus.APPROVED, "OVERTIME"),
    ):
        async with UnitOfWork() as session:
            await command_requests_repository.save(
                session,
                RequestEntity(
                    id=uuid4(),
                    type=type,
                    status=status,
                    data={},
                    created_by_id=created_by_id,
                    reviewed_by_id=reviewed_by_id,
                ),
            )

    handler = Dependency.get(GetRequestsQueryHandler)
    result = await handler.handle(
        GetRequestsQuery(
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
