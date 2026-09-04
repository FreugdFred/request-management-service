from uuid import UUID

from pydantic import BaseModel

from src.domains.requests.enums import RequestStatus


class SaveRequestCommand(BaseModel):
    id: UUID
    note: str | None = None

    type: str | None = None
    status: RequestStatus | None = None

    data: dict | None = None
    created_by_id: str | None = None
    reviewed_by_id: str | None = None















