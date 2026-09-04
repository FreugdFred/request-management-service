from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

from src.core.types import TimezoneAwareDateTime


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        TimezoneAwareDateTime(), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TimezoneAwareDateTime(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
