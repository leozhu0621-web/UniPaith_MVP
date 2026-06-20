"""Add weight_research and weight_campus_life to student_preferences.

Revision ID: scoredweights1  # pragma: allowlist secret
Revises: uwmadpercred2  # pragma: allowlist secret
Create Date: 2026-06-20
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "scoredweights1"  # pragma: allowlist secret
down_revision = "uwmadpercred2"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_preferences",
        sa.Column("weight_research", sa.Integer(), nullable=True),
    )
    op.add_column(
        "student_preferences",
        sa.Column("weight_campus_life", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_preferences", "weight_campus_life")
    op.drop_column("student_preferences", "weight_research")
