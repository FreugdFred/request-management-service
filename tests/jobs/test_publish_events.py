import json
from uuid import uuid4

import pytest
from dependency_container import Dependency
from nats.aio.client import Client as NatsClient

from src.core.events import DomainEvent
from src.core.unit_of_work import UnitOfWork
from src.domains.requests.commands.save_request.command import SaveRequestCommand
from src.domains.requests.commands.save_request.handlers import (
    SaveRequestCommandHandler,
)
from src.domains.requests.enums import RequestStatus
from src.jobs.publish_events import publish_events
from src.messaging.commands.repository import CommandMessagingRepository
from src.messaging.queries.repository import QueryMessagingRepository
from tests.fakes.nats_recording_client import RecordingNatsClient


async def test_does_not_publish_events_when_nats_is_not_configured() -> None:
    async with UnitOfWork() as session:
        await Dependency.get(CommandMessagingRepository).save_many(
            session,
            [DomainEvent(reference_id="employee-1")],
        )

    await publish_events()

    events = await Dependency.get(QueryMessagingRepository).list_unpublished()
    assert len(events) == 1


@pytest.mark.usefixtures("enable_messaging")
async def test_publishes_request_event_envelope() -> None:
    request_id = uuid4()
    nats_client = RecordingNatsClient()
    Dependency.register_instance(NatsClient, nats_client)
    await Dependency.get(SaveRequestCommandHandler).handle(
        SaveRequestCommand(
            id=request_id,
            type="LEAVE",
            status=RequestStatus.PENDING,
            created_by_id="employee-1",
            data={"days": 2},
        )
    )
    events = await Dependency.get(QueryMessagingRepository).list_unpublished()

    await publish_events()

    assert len(nats_client.messages) == 1
    subject, payload = nats_client.messages[0]
    assert subject == "Request-Management-Service-API.RequestCreatedEvent"
    assert json.loads(payload) == {
        "id": str(events[0].id),
        "type": "RequestCreatedEvent",
        "subject": "employee-1",
        "occurrence_datetime": "2026-09-02T12:00:00Z",
        "data": {
            "request_id": str(request_id),
            "type": "LEAVE",
            "status": "PENDING",
            "note": None,
            "data": {"days": 2},
            "reviewed_by_id": None,
        },
    }
    assert await Dependency.get(QueryMessagingRepository).list_unpublished() == []
    assert nats_client.confirmed_messages == nats_client.messages


@pytest.mark.usefixtures("enable_messaging")
async def test_failed_confirmation_keeps_event_available_for_retry() -> None:
    nats_client = RecordingNatsClient()
    nats_client.flush_error = TimeoutError("No confirmation")
    Dependency.register_instance(NatsClient, nats_client)
    await Dependency.get(SaveRequestCommandHandler).handle(
        SaveRequestCommand(
            id=uuid4(),
            type="LEAVE",
            status=RequestStatus.PENDING,
            created_by_id="employee-1",
        )
    )
    events = await Dependency.get(QueryMessagingRepository).list_unpublished()

    with pytest.raises(TimeoutError, match="No confirmation"):
        await publish_events()

    assert await Dependency.get(QueryMessagingRepository).list_unpublished() == events
    assert nats_client.confirmed_messages == []

    nats_client.flush_error = None
    await publish_events()

    assert await Dependency.get(QueryMessagingRepository).list_unpublished() == []
    assert len(nats_client.messages) == 2
    assert nats_client.messages[0] == nats_client.messages[1]
