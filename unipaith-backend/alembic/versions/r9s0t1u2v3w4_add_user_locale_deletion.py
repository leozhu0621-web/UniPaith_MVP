"""Add locale, timezone, deletion_requested_at to users.

Adds the columns the Settings page needs to persist per-user locale +
timezone preferences and to request a 30-day soft delete (Spec/1D).

Revision ID: r9s0t1u2v3w4
Revises: q8r9s0t1u2v3
Create Date: 2026-05-30 00:02:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "r9s0t1u2v3w4"
down_revision: str | None = "q8r9s0t1u2v3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Idempotent: the e4a5b6c7d8e9 column-sync migration may have already added
# these from the model on a fresh DB. ADD COLUMN IF NOT EXISTS converges the
# fresh and incremental (production) paths.


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS locale VARCHAR(10)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(64)")
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMP WITH TIME ZONE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS deletion_requested_at")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS timezone")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS locale")
