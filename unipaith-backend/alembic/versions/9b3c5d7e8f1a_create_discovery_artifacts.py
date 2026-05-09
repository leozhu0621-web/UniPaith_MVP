"""Phase A — create student_goals, student_needs, student_identity.

Discovery artifacts: durable rows the Discovery LLM (Plan 2) writes via
`extracted_signals`, and that students can manually edit on the Profile page
after the journey completes. Identity is single-row-per-student (deepest layer);
goals + needs are multi-row tables.

FKs into discovery_sessions are SET NULL on delete so a session deletion never
nukes a downstream artifact.

Revision ID: 9b3c5d7e8f1a
Revises: 8a2b1c4d5e6f
Create Date: 2026-05-09 16:30:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "9b3c5d7e8f1a"  # pragma: allowlist secret
down_revision = "8a2b1c4d5e6f"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── student_goals ──────────────────────────────────────────────────────
    op.create_table(
        "student_goals",
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
        # Allowed values: 'academic' | 'social' | 'personal'
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("specific", sa.Text, nullable=False),
        sa.Column("measurable", sa.Text, nullable=True),
        sa.Column("achievable_notes", sa.Text, nullable=True),
        sa.Column("relevant_notes", sa.Text, nullable=True),
        sa.Column("time_bound", sa.Date, nullable=True),
        # Allowed values: 'active' | 'met' | 'revised' | 'dropped'
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        # Allowed values: 'discovery' | 'manual'
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column(
            "source_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
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
            "category IN ('academic','social','personal')",
            name="ck_student_goals_category",
        ),
        sa.CheckConstraint(
            "status IN ('active','met','revised','dropped')",
            name="ck_student_goals_status",
        ),
        sa.CheckConstraint(
            "source IN ('discovery','manual')",
            name="ck_student_goals_source",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_student_goals_confidence",
        ),
        sa.CheckConstraint(
            "(source = 'discovery' AND source_session_id IS NOT NULL)"
            " OR (source = 'manual' AND source_session_id IS NULL)",
            name="ck_student_goals_source_provenance",
        ),
    )
    op.create_index(
        "ix_student_goals_student_status",
        "student_goals",
        ["student_id", "status"],
    )

    # ── student_needs ──────────────────────────────────────────────────────
    op.create_table(
        "student_needs",
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
        # Allowed values: 'physiological' | 'safety' | 'social'
        #               | 'self_esteem' | 'self_actualization'
        sa.Column("maslow_level", sa.String(30), nullable=False),
        sa.Column("need_type", sa.String(120), nullable=False),
        sa.Column("signal", sa.Text, nullable=False),
        # Allowed values: 'must_have' | 'strong_preference' | 'nice_to_have'
        sa.Column("severity", sa.String(30), nullable=False),
        # Allowed values: 'discovery' | 'manual' | 'inferred'
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column(
            "source_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("source_quote", sa.Text, nullable=True),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=True),
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
            "maslow_level IN ('physiological','safety','social',"
            "'self_esteem','self_actualization')",
            name="ck_student_needs_maslow_level",
        ),
        sa.CheckConstraint(
            "severity IN ('must_have','strong_preference','nice_to_have')",
            name="ck_student_needs_severity",
        ),
        sa.CheckConstraint(
            "source IN ('discovery','manual','inferred')",
            name="ck_student_needs_source",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_student_needs_confidence",
        ),
        # Provenance: discovery requires source_session_id; manual forbids it.
        # 'inferred' allows session_id to be present or null (LLM may infer
        # from cross-session signals).
        sa.CheckConstraint(
            "(source = 'discovery' AND source_session_id IS NOT NULL)"
            " OR (source = 'manual' AND source_session_id IS NULL)"
            " OR (source = 'inferred')",
            name="ck_student_needs_source_provenance",
        ),
    )
    op.create_index(
        "ix_student_needs_student_maslow",
        "student_needs",
        ["student_id", "maslow_level"],
    )

    # ── student_identity ───────────────────────────────────────────────────
    # PK is student_id — exactly one row per student. JSONB columns default to
    # empty arrays so partial-update logic doesn't have to special-case None.
    op.create_table(
        "student_identity",
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "core_values",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "worldview",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "self_awareness",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("identity_summary", sa.Text, nullable=True),
        sa.Column(
            "last_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("discovery_sessions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("student_identity")
    op.drop_index("ix_student_needs_student_maslow", table_name="student_needs")
    op.drop_table("student_needs")
    op.drop_index("ix_student_goals_student_status", table_name="student_goals")
    op.drop_table("student_goals")
