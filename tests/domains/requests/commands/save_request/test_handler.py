from uuid import uuid4

import pytest
from dependency_container import Dependency

from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.commands.save_request.command import SaveRequestCommand
from src.domains.requests.commands.save_request.handlers import (
    SaveRequestCommandHandler,
)
from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus
from src.exceptions import ValidationException


async def test_create_requires_complete_request(
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request_id = uuid4()

    with pytest.raises(
        ValidationException,
        match=(
            f"Cannot create request {request_id}: missing required fields: "
            "type, status, created_by_id."
        ),
    ):
        await Dependency.get(SaveRequestCommandHandler).handle(
            SaveRequestCommand(id=request_id)
        )

    assert await command_requests_repository.get(request_id) is None


async def test_create_persists_complete_request(
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request_id = uuid4()

    await Dependency.get(SaveRequestCommandHandler).handle(
        SaveRequestCommand(
            id=request_id,
            note="Correct my shift",
            type="SHIFT_CORRECTION",
            status=RequestStatus.PENDING,
            created_by_id="employee-1",
        )
    )

    saved_request = await command_requests_repository.get(request_id)
    assert saved_request is not None
    assert saved_request.note == "Correct my shift"
    assert saved_request.type == "SHIFT_CORRECTION"
    assert saved_request.status is RequestStatus.PENDING
    assert saved_request.data == {}
    assert saved_request.created_by_id == "employee-1"
    assert saved_request.reviewed_by_id is None


async def test_update_applies_empty_and_explicitly_cleared_values(
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request = RequestEntity(
        id=uuid4(),
        note="Original note",
        type="SHIFT_CORRECTION",
        status=RequestStatus.PENDING,
        data={"shift_id": str(uuid4())},
        created_by_id="employee-1",
        reviewed_by_id="manager-1",
    )
    await command_requests_repository.save(request)

    await Dependency.get(SaveRequestCommandHandler).handle(
        SaveRequestCommand(
            id=request.id,
            note=None,
            type="PAUSE_CORRECTION",
            status=RequestStatus.APPROVED,
            data={},
            created_by_id="employee-2",
            reviewed_by_id=None,
        )
    )

    saved_request = await command_requests_repository.get(request.id)
    assert saved_request is not None
    assert saved_request.note is None
    assert saved_request.type == "PAUSE_CORRECTION"
    assert saved_request.status is RequestStatus.APPROVED
    assert saved_request.data == {}
    assert saved_request.created_by_id == "employee-2"
    assert saved_request.reviewed_by_id is None
