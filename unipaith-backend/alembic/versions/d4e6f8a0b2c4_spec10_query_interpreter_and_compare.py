"""Spec 10 — query_interpreter agent + student_compare_lists.

Two changes for the Discovery type-first search build:
  1. Widen the `ai_turns.agent` CHECK constraint to allow 'query_interpreter'
     (the DiscoveryQueryInterpreter LLM agent's ledger label). Without this,
     enabling `ai_discovery_query_v2_enabled` would 500 on the audit-ledger
     write. With the flag off (default) the rule-based parser runs and no
     ai_turns row is written, so this is safe either way.
  2. Create `student_compare_lists` — the server-persisted global compare set
     (spec 10 §8), capped at 4 in the service layer.

Revision ID: d4e6f8a0b2c4
Revises: c8e4a2b1f9d3
Create Date: 2026-05-31 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "d4e6f8a0b2c4"  # pragma: allowlist secret
down_revision = "c8e4a2b1f9d3"  # pragma: allowlist secret
branch_labels = None
depends_on = None


_NEW_AGENT_CHECK = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter')"
)
_OLD_AGENT_CHECK = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher')"
)


def upgrade() -> None:
    # 1. Widen the ai_turns.agent CHECK for the new query_interpreter agent.
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_NEW_AGENT_CHECK})")

    # 2. Server-persisted compare set (spec 10 §8).
    op.create_table(
        "student_compare_lists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "program_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("student_id", "program_id", name="uq_student_compare_student_program"),
    )
    op.create_index("ix_student_compare_lists_student_id", "student_compare_lists", ["student_id"])
    op.create_index("ix_student_compare_lists_program_id", "student_compare_lists", ["program_id"])


def downgrade() -> None:
    op.drop_index("ix_student_compare_lists_program_id", table_name="student_compare_lists")
    op.drop_index("ix_student_compare_lists_student_id", table_name="student_compare_lists")
    op.drop_table("student_compare_lists")

    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_OLD_AGENT_CHECK})")
