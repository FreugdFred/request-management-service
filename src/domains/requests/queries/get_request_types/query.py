from pydantic import BaseModel

from src.domains.requests.enums import RequestStatus


class GetRequestTypesQuery(BaseModel):
    created_by_id: str | None = None
    reviewed_by_id: str | None = None
    status: RequestStatus | None = None
