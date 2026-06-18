"""add claim columns to schools + programs

AI Structure (Spec 2) claim hinge: is_claimed / claimed_at / claimed_by_user_id.
Hand-written (autogenerate is unreliable here — env.py runs create_all). The
add_column ops are guarded by env.py to skip pre-existing objects, so this
replays cleanly on a fresh DB and adds only genuinely-new columns in prod.

Revision ID: aiclaim01
Revises: 92064a3f1d8d
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "aiclaim01"
down_revision: str | None = "92064a3f1d8d"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("schools", "programs")


def upgrade() -> None:
    for t in _TABLES:
        op.add_column(
            t,
            sa.Column("is_claimed", sa.Boolean(), server_default="false", nullable=False),
        )
        op.add_column(t, sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True))
        op.add_column(
            t,
            sa.Column(
                "claimed_by_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )


def downgrade() -> None:
    for t in _TABLES:
        op.drop_column(t, "claimed_by_user_id")
        op.drop_column(t, "claimed_at")
        op.drop_column(t, "is_claimed")
