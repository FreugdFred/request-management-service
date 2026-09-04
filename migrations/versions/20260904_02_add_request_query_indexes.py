"""Add indexes used by request queries.

Revision ID: 20260904_02
Revises: 20260904_01
Create Date: 2026-09-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260904_02"
down_revision: str | None = "20260904_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_request_created_by_id_created_at",
        "request",
        ["created_by_id", "created_at"],
    )
    op.create_index(
        "ix_request_reviewed_by_id_created_at",
        "request",
        ["reviewed_by_id", "created_at"],
    )
    op.create_index("ix_request_status", "request", ["status"])
    op.create_index("ix_request_type", "request", ["type"])


def downgrade() -> None:
    op.drop_index("ix_request_type", table_name="request")
    op.drop_index("ix_request_status", table_name="request")
    op.drop_index("ix_request_reviewed_by_id_created_at", table_name="request")
    op.drop_index("ix_request_created_by_id_created_at", table_name="request")
