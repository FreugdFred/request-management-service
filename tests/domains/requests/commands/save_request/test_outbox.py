from uuid import uuid4

import pytest
from dependency_container import Dependency
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.unit_of_work import UnitOfWork
from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.commands.save_request.command import SaveRequestCommand
from src.domains.requests.commands.save_request.handlers import (
    SaveRequestCommandHandler,
)
from src.domains.requests.enums import RequestStatus
from src.domains.requests.exceptions import InvalidStateChangeException
from src.messaging.queries.repository import QueryMessagingRepository


@pytest.mark.usefixtures("enable_messaging")
async def test_create_queues_event_without_a_nats_connection() -> None:
    request_id = uuid4()

    await Dependency.get(SaveRequestCommandHandler).handle(
        SaveRequestCommand(
            id=request_id,
            type="LEAVE",
            status=RequestStatus.PENDING,
            created_by_id="employee-1",
        )
    )

    events = await Dependency.get(QueryMessagingRepository).list_unpublished()
    assert len(events) == 1
    assert events[0].type == "RequestCreatedEvent"
    assert events[0].subject == "employee-1"
    assert events[0].data == {
        "request_id": str(request_id),
        "note": None,
        "type": "LEAVE",
        "status": "PENDING",
        "data": {},
        "reviewed_by_id": None,
    }


async def test_create_does_not_queue_events_when_nats_is_unset() -> None:
    await Dependency.get(SaveRequestCommandHandler).handle(
        SaveRequestCommand(
            id=uuid4(),
            type="LEAVE",
            status=RequestStatus.PENDING,
            created_by_id="employee-1",
        )
    )

    assert await Dependency.get(QueryMessagingRepository).list_unpublished() == []


@pytest.mark.usefixtures("enable_messaging")
async def test_update_queues_only_effective_changes() -> None:
    request_id = uuid4()
    handler = Dependency.get(SaveRequestCommandHandler)
    await handler.handle(
        SaveRequestCommand(
            id=request_id,
            type="LEAVE",
            status=RequestStatus.PENDING,
            created_by_id="employee-1",
        )
    )
    await handler.handle(
        SaveRequestCommand(id=request_id, status=RequestStatus.APPROVED)
    )
    await handler.handle(
        SaveRequestCommand(id=request_id, status=RequestStatus.APPROVED)
    )

    events = await Dependency.get(QueryMessagingRepository).list_unpublished()
    assert sorted(event.type for event in events) == [
        "RequestCreatedEvent",
        "RequestStatusChangedEvent",
    ]
    changed = next(
        event for event in events if event.type == "RequestStatusChangedEvent"
    )
    assert changed.data == {
        "request_id": str(request_id),
        "previous_status": "PENDING",
        "status": "APPROVED",
    }


@pytest.mark.usefixtures("enable_messaging")
async def test_rejected_status_change_preserves_request_and_outbox() -> None:
    request_id = uuid4()
    handler = Dependency.get(SaveRequestCommandHandler)
    await handler.handle(
        SaveRequestCommand(
            id=request_id,
            type="LEAVE",
            status=RequestStatus.APPROVED,
            created_by_id="employee-1",
            note="Original",
        )
    )
    before = await Dependency.get(QueryMessagingRepository).list_unpublished()

    with pytest.raises(InvalidStateChangeException):
        await handler.handle(
            SaveRequestCommand(
                id=request_id,
                note="Changed",
                status=RequestStatus.REJECTED,
            )
        )

    async with Dependency.get(AsyncSession) as session:
        saved = await Dependency.get(CommandRequestsRepository).get(session, request_id)
    assert saved is not None
    assert saved.note == "Original"
    assert saved.status == RequestStatus.APPROVED
    assert await Dependency.get(QueryMessagingRepository).list_unpublished() == before


@pytest.mark.usefixtures("enable_messaging")
@pytest.mark.parametrize("existing", [False, True])
async def test_outbox_failure_rolls_back_request_save(existing: bool) -> None:
    request_id = uuid4()
    handler = Dependency.get(SaveRequestCommandHandler)
    command = SaveRequestCommand(
        id=request_id,
        type="LEAVE",
        status=RequestStatus.PENDING,
        created_by_id="employee-1",
        note="Original",
    )
    if existing:
        await handler.handle(command)
    before = await Dependency.get(QueryMessagingRepository).list_unpublished()
    async with UnitOfWork() as session:
        await session.execute(
            text(
                "CREATE TRIGGER reject_event BEFORE INSERT ON event "
                "BEGIN SELECT RAISE(ABORT, 'outbox unavailable'); END"
            )
        )

    command.note = "Changed"
    with pytest.raises(IntegrityError, match="outbox unavailable"):
        await handler.handle(command)

    async with Dependency.get(AsyncSession) as session:
        saved = await Dependency.get(CommandRequestsRepository).get(session, request_id)
    if existing:
        assert saved is not None
        assert saved.note == "Original"
    else:
        assert saved is None
    assert await Dependency.get(QueryMessagingRepository).list_unpublished() == before
