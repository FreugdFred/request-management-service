from uuid import uuid4

import pytest
from dependency_container import Dependency
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.unit_of_work import UnitOfWork
from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.commands.delete_request.command import DeleteRequestCommand
from src.domains.requests.commands.delete_request.handlers import (
    DeleteRequestCommandHandler,
)
from src.domains.requests.commands.save_request.command import SaveRequestCommand
from src.domains.requests.commands.save_request.handlers import (
    SaveRequestCommandHandler,
)
from src.domains.requests.enums import RequestStatus
from src.messaging.queries.repository import QueryMessagingRepository


@pytest.mark.usefixtures("enable_messaging")
async def test_delete_queues_one_event_and_is_idempotent() -> None:
    request_id = uuid4()
    await Dependency.get(SaveRequestCommandHandler).handle(
        SaveRequestCommand(
            id=request_id,
            type="LEAVE",
            status=RequestStatus.PENDING,
            created_by_id="employee-1",
        )
    )
    handler = Dependency.get(DeleteRequestCommandHandler)

    await handler.handle(DeleteRequestCommand(id=request_id))
    await handler.handle(DeleteRequestCommand(id=request_id))

    async with Dependency.get(AsyncSession) as session:
        assert (
            await Dependency.get(CommandRequestsRepository).get(session, request_id)
            is None
        )
    events = await Dependency.get(QueryMessagingRepository).list_unpublished()
    assert sorted(event.type for event in events) == [
        "RequestCreatedEvent",
        "RequestDeletedEvent",
    ]
    deleted = next(event for event in events if event.type == "RequestDeletedEvent")
    assert deleted.subject == "employee-1"
    assert deleted.data == {"request_id": str(request_id)}


@pytest.mark.usefixtures("enable_messaging")
async def test_outbox_failure_rolls_back_request_delete() -> None:
    request_id = uuid4()
    await Dependency.get(SaveRequestCommandHandler).handle(
        SaveRequestCommand(
            id=request_id,
            type="LEAVE",
            status=RequestStatus.PENDING,
            created_by_id="employee-1",
        )
    )
    before = await Dependency.get(QueryMessagingRepository).list_unpublished()
    async with UnitOfWork() as session:
        await session.execute(
            text(
                "CREATE TRIGGER reject_event BEFORE INSERT ON event "
                "BEGIN SELECT RAISE(ABORT, 'outbox unavailable'); END"
            )
        )

    with pytest.raises(IntegrityError, match="outbox unavailable"):
        await Dependency.get(DeleteRequestCommandHandler).handle(
            DeleteRequestCommand(id=request_id)
        )

    async with Dependency.get(AsyncSession) as session:
        assert (
            await Dependency.get(CommandRequestsRepository).get(session, request_id)
            is not None
        )
    assert await Dependency.get(QueryMessagingRepository).list_unpublished() == before
