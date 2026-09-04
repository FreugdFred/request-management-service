from copy import deepcopy
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PrivateAttr, validate_call

from src.core.events import DomainEvent
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


class Request(BaseModel):
    id: UUID
    note: str | None = None

    type: str
    status: RequestStatus
    data: dict[str, Any]

    created_by_id: str
    reviewed_by_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RequestEntity(Request):
    _events: list[DomainEvent] = PrivateAttr(default_factory=list)

    @classmethod
    def create(
        cls,
        *,
        id: UUID,
        type: str,
        status: RequestStatus,
        created_by_id: str,
        note: str | None = None,
        data: dict[str, Any] | None = None,
        reviewed_by_id: str | None = None,
    ) -> Self:
        request = cls(
            id=id,
            note=note,
            type=type,
            status=status,
            data=deepcopy(data) if data is not None else {},
            created_by_id=created_by_id,
            reviewed_by_id=reviewed_by_id,
        )
        request._record_event(
            RequestCreatedEvent(
                reference_id=request.created_by_id,
                request_id=request.id,
                note=request.note,
                type=request.type,
                status=request.status,
                data=deepcopy(request.data),
                reviewed_by_id=request.reviewed_by_id,
            )
        )
        return request

    def pull_events(self) -> tuple[DomainEvent, ...]:
        events = tuple(self._events)
        self._events.clear()
        return events

    def delete(self) -> None:
        self._record_event(
            RequestDeletedEvent(
                reference_id=self.created_by_id,
                request_id=self.id,
            )
        )

    def set_note(self, note: str | None) -> None:
        if note == self.note:
            return

        previous_note = self.note
        self.note = note
        self._record_event(
            RequestNoteChangedEvent(
                reference_id=self.created_by_id,
                request_id=self.id,
                previous_note=previous_note,
                note=note,
            )
        )

    def set_type(self, type: str) -> None:
        if type == self.type:
            return

        previous_type = self.type
        self.type = type
        self._record_event(
            RequestTypeChangedEvent(
                reference_id=self.created_by_id,
                request_id=self.id,
                previous_type=previous_type,
                type=type,
            )
        )

    @validate_call
    def set_status(self, status: RequestStatus) -> None:
        if status == self.status:
            return

        previous_status = self.status
        self.status = status
        self._record_event(
            RequestStatusChangedEvent(
                reference_id=self.created_by_id,
                request_id=self.id,
                previous_status=previous_status,
                status=status,
            )
        )

    def set_data(self, data: dict[str, Any]) -> None:
        if data == self.data:
            return

        previous_data = deepcopy(self.data)
        self.data = deepcopy(data)
        self._record_event(
            RequestDataChangedEvent(
                reference_id=self.created_by_id,
                request_id=self.id,
                previous_data=previous_data,
                data=deepcopy(self.data),
            )
        )

    def set_created_by_id(self, created_by_id: str) -> None:
        if created_by_id == self.created_by_id:
            return

        previous_created_by_id = self.created_by_id
        self.created_by_id = created_by_id
        self._record_event(
            RequestCreatedByChangedEvent(
                reference_id=self.created_by_id,
                request_id=self.id,
                previous_created_by_id=previous_created_by_id,
                created_by_id=created_by_id,
            )
        )

    def set_reviewed_by_id(self, reviewed_by_id: str | None) -> None:
        if reviewed_by_id == self.reviewed_by_id:
            return

        previous_reviewed_by_id = self.reviewed_by_id
        self.reviewed_by_id = reviewed_by_id
        self._record_event(
            RequestReviewedByChangedEvent(
                reference_id=self.created_by_id,
                request_id=self.id,
                previous_reviewed_by_id=previous_reviewed_by_id,
                reviewed_by_id=reviewed_by_id,
            )
        )

    def _record_event(self, event: DomainEvent) -> None:
        self._events.append(event)
