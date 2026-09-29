from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.unit_of_work import UnitOfWork
from src.domains.requests.command_repository import CommandRequestsRepository
from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus
from src.domains.requests.routes import request_router
from src.exception_handlers import register_exception_handlers


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(request_router)
    register_exception_handlers(app)
    return TestClient(app)


async def test_delete_route_removes_request(
    client: TestClient,
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request = RequestEntity(
        id=uuid4(),
        type="SHIFT_CORRECTION",
        status=RequestStatus.PENDING,
        data={},
        created_by_id="employee-1",
    )
    async with UnitOfWork() as session:
        await command_requests_repository.save(session, request)

    response = client.delete("/request/remove", params={"id": str(request.id)})

    assert response.status_code == 200, response.text
    async with UnitOfWork() as session:
        assert await command_requests_repository.get(session, request.id) is None


def test_delete_route_is_idempotent(client: TestClient) -> None:
    response = client.delete("/request/remove", params={"id": str(uuid4())})

    assert response.status_code == 200, response.text


async def test_save_route_creates_request(
    client: TestClient,
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request_id = uuid4()

    response = client.post(
        "/request/save",
        json={
            "id": str(request_id),
            "type": "LEAVE",
            "status": "PENDING",
            "data": {"days": 2},
            "created_by_id": "employee-1",
        },
    )

    assert response.status_code == 200, response.text
    async with UnitOfWork() as session:
        request = await command_requests_repository.get(session, request_id)
    assert request is not None
    assert request.type == "LEAVE"
    assert request.data == {"days": 2}


async def test_save_route_rejects_status_change_after_decision(
    client: TestClient,
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request = RequestEntity(
        id=uuid4(),
        type="LEAVE",
        status=RequestStatus.APPROVED,
        data={},
        created_by_id="employee-1",
    )
    async with UnitOfWork() as session:
        await command_requests_repository.save(session, request)

    response = client.post(
        "/request/save",
        json={"id": str(request.id), "status": "REJECTED"},
    )

    assert response.status_code == 409, response.text
    assert response.json() == {"detail": "The requested state change is not allowed."}
    async with UnitOfWork() as session:
        saved_request = await command_requests_repository.get(session, request.id)
    assert saved_request is not None
    assert saved_request.status is RequestStatus.APPROVED


async def test_request_query_routes_return_expected_shapes(
    client: TestClient,
    command_requests_repository: CommandRequestsRepository,
) -> None:
    request = RequestEntity(
        id=uuid4(),
        type="SHIFT_CORRECTION",
        status=RequestStatus.PENDING,
        data={"shift_id": "shift-1"},
        created_by_id="employee-1",
        reviewed_by_id="manager-1",
    )
    async with UnitOfWork() as session:
        await command_requests_repository.save(session, request)

    by_id_response = client.get(f"/request/{request.id}")
    filtered_response = client.get(
        "/request",
        params={
            "created_by_id": "employee-1",
            "reviewed_by_id": "manager-1",
            "status": "PENDING",
            "limit": 10,
            "offset": 0,
        },
    )
    unfiltered_response = client.get("/request")
    types_response = client.get(
        "/request/types",
        params={"created_by_id": "employee-1"},
    )

    assert by_id_response.status_code == 200, by_id_response.text
    assert by_id_response.json()["id"] == str(request.id)
    assert by_id_response.json()["created_at"] is not None
    assert by_id_response.json()["updated_at"] is not None
    assert filtered_response.status_code == 200, filtered_response.text
    assert filtered_response.json()["total"] == 1
    assert filtered_response.json()["limit"] == 10
    assert filtered_response.json()["offset"] == 0
    assert filtered_response.json()["items"][0]["created_at"] is not None
    assert filtered_response.json()["items"][0]["updated_at"] is not None
    assert unfiltered_response.status_code == 200, unfiltered_response.text
    assert unfiltered_response.json()["items"][0]["id"] == str(request.id)
    assert unfiltered_response.json()["items"][0]["created_at"] is not None
    assert unfiltered_response.json()["items"][0]["updated_at"] is not None
    assert types_response.status_code == 200, types_response.text
    assert types_response.json() == ["SHIFT_CORRECTION"]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": "0"},
        {"limit": "101"},
        {"offset": "-1"},
        {"sort_direction": "invalid"},
        {"status": "invalid"},
    ],
)
def test_list_requests_rejects_invalid_filters(
    client: TestClient,
    params: dict[str, str],
) -> None:
    response = client.get("/request", params=params)

    assert response.status_code == 422, response.text
