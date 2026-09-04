from uuid import UUID

from pydantic import BaseModel


class DeleteRequestCommand(BaseModel):
    id: UUID