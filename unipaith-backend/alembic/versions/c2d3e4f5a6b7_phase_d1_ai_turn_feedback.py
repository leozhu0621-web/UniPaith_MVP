"""Phase D1 — ai_turn_feedback ledger.

Captures per-turn user signal on every AI surface. Used by the weekly
review pipeline + per-student safety profile + cost-of-quality
dashboards. See `unipaith.models.ai_feedback` for the model docstring.

Revision ID: c2d3e4f5a6b7
Revises: 9b1a2c3d4e5f
Create Date: 2026-05-10 16:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c2d3e4f5a6b7"  # pragma: allowlist secret
down_revision = "9b1a2c3d4e5f"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_turn_feedback",
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
        # Loose reference — see model docstring for why no FK.
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("surface", sa.String(40), nullable=False),
        sa.Column("vote", sa.String(20), nullable=False),
        sa.Column("reason_category", sa.String(40), nullable=True),
        sa.Column("free_text", sa.Text, nullable=True),
        sa.Column("context", postgresql.JSONB, nullable=True),
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
        sa.UniqueConstraint(
            "student_id",
            "target_id",
            "surface",
            name="uq_ai_feedback_student_target_surface",
        ),
        sa.CheckConstraint(
            "vote IN ('up','down','regenerate','not_right')",
            name="ck_ai_feedback_vote",
        ),
        sa.CheckConstraint(
            "surface IN ('orchestrator_turn','extractor_signal',"
            "'rationale','workshop_essay','workshop_interview',"
            "'workshop_test_prep','match_card','other')",
            name="ck_ai_feedback_surface",
        ),
    )
    op.create_index(
        "ix_ai_feedback_surface_created",
        "ai_turn_feedback",
        ["surface", "created_at"],
    )
    op.create_index(
        "ix_ai_feedback_student_created",
        "ai_turn_feedback",
        ["student_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_feedback_student_created", table_name="ai_turn_feedback")
    op.drop_index("ix_ai_feedback_surface_created", table_name="ai_turn_feedback")
    op.drop_table("ai_turn_feedback")
