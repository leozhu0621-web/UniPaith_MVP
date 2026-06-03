"""Demo feedback survey — feedback table.

Stores in-app demo feedback submissions (title + message). Guarded create so it
is a safe no-op against the conftest ``create_all`` test DB and runs
incrementally in production from the prior head.

Revision ID: fdbk0a1b2c3d
Revises: s60a1b2c3d4e
Create Date: 2026-06-03

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "fdbk0a1b2c3d"  # pragma: allowlist secret
down_revision = "s60a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if _has_table("feedback"):
        return
    op.create_table(
        "feedback",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("role", sa.String(length=30), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", postgresql.JSONB(), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_feedback_user_id", table_name="feedback")
    op.drop_table("feedback")
