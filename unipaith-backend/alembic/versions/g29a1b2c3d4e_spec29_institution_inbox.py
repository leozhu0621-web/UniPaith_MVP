"""Spec 29 (Institution Messaging & Inbox): thread assignment + reason code.

This revision does two things:

1. **Extends ``conversations``** with the institution-side inbox metadata that
   layers over the shared student/institution thread transport:
   - ``assigned_to`` — the staff user who owns the thread (§2; null = the
     unassigned shared queue), FK ``users.id`` ON DELETE SET NULL.
   - ``reason_code`` — the institution's outbound reason code (§4); it drives
     the student's ``action_label`` via the §4 mapping.
   Plus the ``(institution_id, assigned_to)`` index the mine/unassigned/all
   filters hit.
2. **Widens ``ck_ai_turns_agent``** to admit the two new Spec 29 §8 agents
   (``institution_reply_drafter`` + ``inbound_intent_classifier``), keeping the
   full post-Spec-26 vocabulary (incl. ``segment_builder_nl``).

Chains off ``f27e5a1c0d34`` (the Spec 27 head) so the graph stays a single
linear head (``test_alembic_has_single_head``). All operations are guarded with
``_has_table`` / ``_has_column`` so the revision is a safe no-op against a
dev/test DB built from the models via ``create_all``.

Revision ID: g29a1b2c3d4e
Revises: f27e5a1c0d34
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "g29a1b2c3d4e"  # pragma: allowlist secret
down_revision = "f27e5a1c0d34"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Full post-Spec-29 vocabulary (adds the two institution-messaging agents).
_AGENT_CHECK_NEW = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier')"
)
# Prior state (post Spec 26).
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl')"
)


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {c["name"] for c in _inspector().get_columns(table)}


def _has_index(table: str, index: str) -> bool:
    if not _has_table(table):
        return False
    return index in {ix["name"] for ix in _inspector().get_indexes(table)}


def upgrade() -> None:
    # ── 1. extend conversations with the Spec 29 institution-inbox shape ──
    if _has_table("conversations"):
        if not _has_column("conversations", "reason_code"):
            op.add_column(
                "conversations", sa.Column("reason_code", sa.String(length=40), nullable=True)
            )
        if not _has_column("conversations", "assigned_to"):
            op.add_column(
                "conversations",
                sa.Column("assigned_to", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                "fk_conversations_assigned_to_user",
                "conversations",
                "users",
                ["assigned_to"],
                ["id"],
                ondelete="SET NULL",
            )
        if not _has_index("conversations", "ix_conversations_inst_assigned"):
            op.create_index(
                "ix_conversations_inst_assigned",
                "conversations",
                ["institution_id", "assigned_to"],
            )

    # ── 2. widen ck_ai_turns_agent for the institution-messaging agents ──
    if _has_table("ai_turns"):
        op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
        op.execute(
            f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_AGENT_CHECK_NEW})"
        )


def downgrade() -> None:
    if _has_table("ai_turns"):
        op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
        op.execute(
            f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_AGENT_CHECK_OLD})"
        )

    if _has_table("conversations"):
        if _has_index("conversations", "ix_conversations_inst_assigned"):
            op.drop_index("ix_conversations_inst_assigned", table_name="conversations")
        if _has_column("conversations", "assigned_to"):
            op.drop_constraint(
                "fk_conversations_assigned_to_user", "conversations", type_="foreignkey"
            )
            op.drop_column("conversations", "assigned_to")
        if _has_column("conversations", "reason_code"):
            op.drop_column("conversations", "reason_code")
