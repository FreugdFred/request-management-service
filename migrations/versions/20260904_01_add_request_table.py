"""Add the request table.

Revision ID: 20260904_01
Revises:
Create Date: 2026-09-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260904_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    request_status = sa.Enum(
        "APPROVED",
        "PENDING",
        "REJECTED",
        name="request_status_enum",
    )

    op.create_table(
        "request",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", request_status, nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_by_id", sa.String(), nullable=False),
        sa.Column("reviewed_by_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("request")
    sa.Enum(name="request_status_enum").drop(op.get_bind(), checkfirst=True)
