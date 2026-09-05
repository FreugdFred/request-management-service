from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domains.requests.entity import RequestEntity
from src.domains.requests.enums import RequestStatus
from src.domains.requests.events import (
    RequestCreatedByChangedEvent,
    RequestCreatedEvent,
    RequestDataChangedEvent,
    RequestDeletedEvent,
    RequestNoteChangedEvent,
    RequestReviewedByChangedEvent,
    RequestStatusChangedEvent,
    RequestTypeChangedEvent,
)
from domains.requests.exceptions import InvalidStateChangeException

NOW = datetime(2026, 9, 2, 12, tzinfo=UTC)


def test_create_records_request_created_event() -> None:
    request = RequestEntity.create(
        id=uuid4(),
        note="Correct my shift",
        type="SHIFT_CORRECTION",
        status=RequestStatus.PENDING,
        data={"minutes": 30},
        created_by_id="employee-1",
        reviewed_by_id=None,
    )

    assert request.pull_events() == (
        RequestCreatedEvent(
            reference_id="employee-1",
            request_id=request.id,
            note="Correct my shift",
            type="SHIFT_CORRECTION",
            status=RequestStatus.PENDING,
            data={"minutes": 30},
            reviewed_by_id=None,
            occurrence_datetime=NOW,
        ),
    )


def test_changes_record_previous_and_new_values() -> None:
    request = RequestEntity(
        id=uuid4(),
        note="Original note",
        type="SHIFT_CORRECTION",
        status=RequestStatus.PENDING,
        data={"minutes": 15},
        created_by_id="employee-1",
        reviewed_by_id="manager-1",
    )

    request.set_note(None)
    request.set_type("PAUSE_CORRECTION")
    request.set_status(RequestStatus.APPROVED)
    request.set_data({"minutes": 30})
    request.set_created_by_id("employee-2")
    request.set_reviewed_by_id(None)

    assert request.pull_events() == (
        RequestNoteChangedEvent(
            reference_id="employee-1",
            request_id=request.id,
            previous_note="Original note",
            note=None,
            occurrence_datetime=NOW,
        ),
        RequestTypeChangedEvent(
            reference_id="employee-1",
            request_id=request.id,
            previous_type="SHIFT_CORRECTION",
            type="PAUSE_CORRECTION",
            occurrence_datetime=NOW,
        ),
        RequestStatusChangedEvent(
            reference_id="employee-1",
            request_id=request.id,
            previous_status=RequestStatus.PENDING,
            status=RequestStatus.APPROVED,
            occurrence_datetime=NOW,
        ),
        RequestDataChangedEvent(
            reference_id="employee-1",
            request_id=request.id,
            previous_data={"minutes": 15},
            data={"minutes": 30},
            occurrence_datetime=NOW,
        ),
        RequestCreatedByChangedEvent(
            reference_id="employee-2",
            request_id=request.id,
            previous_created_by_id="employee-1",
            created_by_id="employee-2",
            occurrence_datetime=NOW,
        ),
        RequestReviewedByChangedEvent(
            reference_id="employee-2",
            request_id=request.id,
            previous_reviewed_by_id="manager-1",
            reviewed_by_id=None,
            occurrence_datetime=NOW,
        ),
    )


def test_unchanged_values_do_not_record_events() -> None:
    data = {"minutes": 15}
    request = RequestEntity(
        id=uuid4(),
        note=None,
        type="SHIFT_CORRECTION",
        status=RequestStatus.PENDING,
        data=data,
        created_by_id="employee-1",
        reviewed_by_id=None,
    )

    request.set_note(None)
    request.set_type("SHIFT_CORRECTION")
    request.set_status(RequestStatus.PENDING)
    request.set_data(data)
    request.set_created_by_id("employee-1")
    request.set_reviewed_by_id(None)

    assert request.pull_events() == ()


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (RequestStatus.APPROVED, RequestStatus.PENDING),
        (RequestStatus.APPROVED, RequestStatus.REJECTED),
        (RequestStatus.REJECTED, RequestStatus.PENDING),
        (RequestStatus.REJECTED, RequestStatus.APPROVED),
    ],
)
def test_decided_request_status_cannot_be_changed(
    current_status: RequestStatus,
    new_status: RequestStatus,
) -> None:
    request = RequestEntity(
        id=uuid4(),
        type="SHIFT_CORRECTION",
        status=current_status,
        data={},
        created_by_id="employee-1",
    )

    with pytest.raises(InvalidStateChangeException):
        request.set_status(new_status)

    assert request.status is current_status
    assert request.pull_events() == ()


@pytest.mark.parametrize(
    "status",
    [RequestStatus.APPROVED, RequestStatus.REJECTED],
)
def test_reapplying_decided_status_is_a_no_op(status: RequestStatus) -> None:
    request = RequestEntity(
        id=uuid4(),
        type="SHIFT_CORRECTION",
        status=status,
        data={},
        created_by_id="employee-1",
    )

    request.set_status(status)

    assert request.status is status
    assert request.pull_events() == ()


def test_delete_records_request_deleted_event() -> None:
    request = RequestEntity(
        id=uuid4(),
        type="SHIFT_CORRECTION",
        status=RequestStatus.PENDING,
        data={},
        created_by_id="employee-1",
    )

    request.delete()

    assert request.pull_events() == (
        RequestDeletedEvent(
            reference_id=request.created_by_id,
            request_id=request.id,
            occurrence_datetime=NOW,
        ),
    )
