from __future__ import annotations

from enum import StrEnum


class RequestStatus(StrEnum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
