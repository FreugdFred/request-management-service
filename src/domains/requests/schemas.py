from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.domains.requests.enums import RequestStatus


class SaveRequestInput(BaseModel):
    id: UUID
    note: str | None = None
    type: str | None = None
    status: RequestStatus | None = None
    data: dict[str, Any] | None = None
    created_by_id: str | None = None
    reviewed_by_id: str | None = None


class PaginationInput(BaseModel):
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class CreatedRequestsFiltersInput(BaseModel):
    status: RequestStatus | None = None
    type: str | None = None
    reviewed_by_id: str | None = None
    sort_direction: Literal["asc", "desc"] = "desc"


class ReviewedRequestsFiltersInput(BaseModel):
    status: RequestStatus | None = None
    type: str | None = None
    created_by_id: str | None = None
    sort_direction: Literal["asc", "desc"] = "desc"


class RequestTypesFiltersInput(BaseModel):
    created_by_id: str | None = None
    reviewed_by_id: str | None = None
    status: RequestStatus | None = None
