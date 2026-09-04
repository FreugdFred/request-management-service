from typing import Literal

from pydantic import BaseModel, Field

from src.domains.requests.enums import RequestStatus


class GetRequestsCreatedByQuery(BaseModel):
    created_by_id: str
    status: RequestStatus | None = None
    type: str | None = None
    reviewed_by_id: str | None = None
    sort_direction: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
