"""Add intent_reason + intent_rationale to applications.

Captures the student's "Why are you applying?" picker selection plus the
free-text rationale that's required when guardrail-scan returns red.
Backs the Apply > Guardrails tab — see gap-audit G-S4 and Spec/17.

Revision ID: q8r9s0t1u2v3
Revises: p7q8r9s0t1u2
Create Date: 2026-05-30 00:01:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "q8r9s0t1u2v3"
down_revision: str | None = "p7q8r9s0t1u2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Idempotent: the e4a5b6c7d8e9 column-sync migration may have already added
# these from the model on a fresh DB. ADD COLUMN IF NOT EXISTS converges the
# fresh and incremental (production) paths.


def upgrade() -> None:
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS intent_reason VARCHAR(64)")
    op.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS intent_rationale TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE applications DROP COLUMN IF EXISTS intent_rationale")
    op.execute("ALTER TABLE applications DROP COLUMN IF EXISTS intent_reason")
