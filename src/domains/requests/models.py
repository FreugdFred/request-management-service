from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import JSON, Enum, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from src.core.base import Base
from src.core.mixins import TimestampMixin
from src.domains.requests.enums import RequestStatus

json_type = JSON().with_variant(JSONB(), "postgresql")


class DbRequest(Base, TimestampMixin):
    __tablename__ = "request"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    type: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status_enum"),
        nullable=False,
        default=RequestStatus.PENDING,
    )

    data: Mapped[dict[str, Any]] = mapped_column(
        MutableDict.as_mutable(json_type),
        nullable=False,
        default=dict,
    )

    created_by_id: Mapped[str] = mapped_column(nullable=False)
    reviewed_by_id: Mapped[str | None] = mapped_column(nullable=True)
