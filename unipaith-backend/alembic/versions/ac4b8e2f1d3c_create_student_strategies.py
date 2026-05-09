"""Phase A — create student_strategies.

The Strategy artifact bridges Stage 1 (Discovery) and Stage 2 (Match): it
turns the Goal Stack + Needs Map + profile into a broad strategy doc
(career → degree → academic path → financial path → geography). Versioned;
exactly one row per student can be `active` at a time, enforced by a partial
unique index. PATCH archives the original and creates a new draft (clone-and-
modify) so version history is intact.

`is_stub` is set to TRUE in Phase A — the rule-based generator produces
template prose. Plan 2 swaps the generator body for an LLM call and flips
the flag to FALSE.

Revision ID: ac4b8e2f1d3c
Revises: 9b3c5d7e8f1a
Create Date: 2026-05-09 17:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "ac4b8e2f1d3c"  # pragma: allowlist secret
down_revision = "9b3c5d7e8f1a"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_strategies",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Per-student monotonic version, computed on insert by the service.
        sa.Column("version", sa.Integer, nullable=False),
        # Allowed values: 'draft' | 'active' | 'archived'
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("career_target", sa.Text, nullable=True),
        sa.Column("target_degree", sa.String(120), nullable=True),
        sa.Column(
            "academic_path",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "financial_path",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "geographic_path",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("narrative", sa.Text, nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "generated_from_session_ids",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            nullable=False,
            server_default=sa.text("ARRAY[]::uuid[]"),
        ),
        sa.Column(
            "is_stub",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('draft','active','archived')",
            name="ck_student_strategies_status",
        ),
        sa.CheckConstraint(
            "version >= 1",
            name="ck_student_strategies_version_positive",
        ),
        sa.UniqueConstraint("student_id", "version", name="uq_student_strategies_student_version"),
    )
    op.create_index(
        "ix_student_strategies_student_status",
        "student_strategies",
        ["student_id", "status"],
    )
    # At most one active strategy per student. Partial unique index — works
    # because Postgres treats `archived` and `draft` rows as not part of the
    # uniqueness universe.
    op.create_index(
        "uq_student_strategies_one_active",
        "student_strategies",
        ["student_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_student_strategies_one_active", table_name="student_strategies")
    op.drop_index("ix_student_strategies_student_status", table_name="student_strategies")
    op.drop_table("student_strategies")
