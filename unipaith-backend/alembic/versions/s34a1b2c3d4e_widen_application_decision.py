"""spec 34 — widen applications.decision for conditional_admission

Revision ID: s34a1b2c3d4e
Revises: a3029merge1b2c
Create Date: 2026-06-01 12:00:00.000000

Spec 34 (Decisions & Offers, institution-side) adds the ``conditional_admission``
decision value (21 chars), which overflows the original VARCHAR(20). Widening a
varchar is a metadata-only change in PostgreSQL — no table rewrite, no lock churn.
"""

import sqlalchemy as sa

from alembic import op

revision = "s34a1b2c3d4e"
down_revision = "a3029merge1b2c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "applications",
        "decision",
        existing_type=sa.String(20),
        type_=sa.String(30),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "applications",
        "decision",
        existing_type=sa.String(30),
        type_=sa.String(20),
        existing_nullable=True,
    )
