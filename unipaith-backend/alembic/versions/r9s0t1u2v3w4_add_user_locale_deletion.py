"""Add locale, timezone, deletion_requested_at to users.

Adds the columns the Settings page needs to persist per-user locale +
timezone preferences and to request a 30-day soft delete (Spec/1D).

Revision ID: r9s0t1u2v3w4
Revises: q8r9s0t1u2v3
Create Date: 2026-05-30 00:02:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "r9s0t1u2v3w4"
down_revision: str | None = "q8r9s0t1u2v3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("locale", sa.String(length=10), nullable=True))
    op.add_column("users", sa.Column("timezone", sa.String(length=64), nullable=True))
    op.add_column(
        "users",
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "deletion_requested_at")
    op.drop_column("users", "timezone")
    op.drop_column("users", "locale")
