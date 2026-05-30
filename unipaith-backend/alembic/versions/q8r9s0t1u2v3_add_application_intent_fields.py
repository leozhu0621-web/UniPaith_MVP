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

import sqlalchemy as sa

from alembic import op

revision: str = "q8r9s0t1u2v3"
down_revision: str | None = "p7q8r9s0t1u2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("intent_reason", sa.String(length=64), nullable=True))
    op.add_column("applications", sa.Column("intent_rationale", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("applications", "intent_rationale")
    op.drop_column("applications", "intent_reason")
