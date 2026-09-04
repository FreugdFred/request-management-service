from uuid import uuid4

import pytest
from dependency_container import Dependency

from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus
from src.domains.requests.queries.get_request_by_id.handler import (
    GetRequestByIdQueryHandler,
)
from src.domains.requests.queries.get_request_by_id.query import GetRequestByIdQuery
from src.exceptions import NotFoundException


async def test_get_request_by_id_returns_request(
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request = RequestEntity(
        id=uuid4(),
        note="Please correct my shift",
        type="SHIFT_CORRECTION",
        status=RequestStatus.PENDING,
        data={"shift_id": "shift-1"},
        created_by_id="employee-1",
    )
    await command_requests_repository.save(request)

    handler = Dependency.get(GetRequestByIdQueryHandler)
    result = await handler.handle(GetRequestByIdQuery(id=request.id))

    assert result.id == request.id
    assert result.note == request.note
    assert result.data == request.data
    assert result.created_at is not None
    assert result.updated_at is not None


async def test_get_request_by_id_raises_when_request_does_not_exist() -> None:
    request_id = uuid4()
    handler = Dependency.get(GetRequestByIdQueryHandler)

    with pytest.raises(NotFoundException, match=str(request_id)):
        await handler.handle(GetRequestByIdQuery(id=request_id))
