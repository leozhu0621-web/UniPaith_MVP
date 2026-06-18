"""add program_preferences

The program side of the shared Prompt Library (AI Structure, Spec 2/3) — the
program's target-applicant preferences that drive the program→student match
direction. Hand-written (only this table); autogenerate is unreliable in this
repo because env.py runs create_all for the current model set.

Revision ID: 92064a3f1d8d
Revises: utaprof1
Create Date: 2026-06-18

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "92064a3f1d8d"  # pragma: allowlist secret
down_revision: str | None = "utaprof1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "program_preferences",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("program_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pref_min_gpa", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("pref_test_bands", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pref_fields", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("pref_levels", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("pref_countries", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("weight_academic", sa.Integer(), nullable=True),
        sa.Column("weight_field_fit", sa.Integer(), nullable=True),
        sa.Column("weight_outcomes_alignment", sa.Integer(), nullable=True),
        sa.Column("weight_funding_need", sa.Integer(), nullable=True),
        sa.Column("weight_geographic", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=30), server_default="derived", nullable=False),
        sa.Column("confidence", sa.Numeric(precision=3, scale=2), nullable=True),
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
        sa.ForeignKeyConstraint(["program_id"], ["programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("program_id"),
    )


def downgrade() -> None:
    op.drop_table("program_preferences")
