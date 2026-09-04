from uuid import uuid4

from dependency_container import Dependency

from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.commands.delete_request.command import DeleteRequestCommand
from src.domains.requests.commands.delete_request.handlers import (
    DeleteRequestCommandHandler,
)
from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus


async def test_delete_request_is_idempotent(
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request_id = uuid4()
    await command_requests_repository.save(
        RequestEntity(
            id=request_id,
            note="Correct my shift",
            type="SHIFT_CORRECTION",
            status=RequestStatus.PENDING,
            data={"shift_id": str(uuid4())},
            created_by_id="employee-1",
        )
    )

    handler = Dependency.get(DeleteRequestCommandHandler)
    await handler.handle(DeleteRequestCommand(id=request_id))
    await handler.handle(DeleteRequestCommand(id=request_id))

    assert await command_requests_repository.get(request_id) is None
