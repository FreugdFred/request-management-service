import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: str
    subject: str
    data: dict[str, Any]
    occurrence_datetime: datetime
