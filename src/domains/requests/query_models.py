from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domains.requests.enums import RequestStatus


class PaginatedQueryModel[QueryModel](BaseModel):
    items: list[QueryModel]
    total: int
    limit: int
    offset: int


class RequestQueryModel(BaseModel):
    id: UUID
    note: str | None
    type: str
    status: RequestStatus
    data: dict[str, Any]
    created_by_id: str
    reviewed_by_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
