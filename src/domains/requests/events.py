from typing import Any
from uuid import UUID

from src.core.events import DomainEvent
from src.domains.requests.enums import RequestStatus


class RequestEvent(DomainEvent):
    request_id: UUID


class RequestCreatedEvent(RequestEvent):
    note: str | None
    type: str
    status: RequestStatus
    data: dict[str, Any]
    reviewed_by_id: str | None


class RequestNoteChangedEvent(RequestEvent):
    previous_note: str | None
    note: str | None


class RequestTypeChangedEvent(RequestEvent):
    previous_type: str
    type: str


class RequestStatusChangedEvent(RequestEvent):
    previous_status: RequestStatus
    status: RequestStatus


class RequestDataChangedEvent(RequestEvent):
    previous_data: dict[str, Any]
    data: dict[str, Any]


class RequestCreatedByChangedEvent(RequestEvent):
    previous_created_by_id: str
    created_by_id: str


class RequestReviewedByChangedEvent(RequestEvent):
    previous_reviewed_by_id: str | None
    reviewed_by_id: str | None


class RequestDeletedEvent(RequestEvent):
    pass
