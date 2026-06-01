"""Spec 32 — Review Workspace: widen ``ck_ai_turns_agent`` for the two new
review-workspace assist agents (``review_synthesis`` §4 + ``review_assistant``
§6, both Sonnet).

Chains off ``a3029merge1b2c`` (the current head) so the graph stays a single
linear head (``test_alembic_has_single_head``). The only schema change is the
CHECK-constraint widening — additive and guarded, so it is a safe no-op against
a dev/test DB built from the models via ``create_all`` (the constraint there
already includes the new vocabulary).

Revision ID: a32revwork1b2c
Revises: a3029merge1b2c
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a32revwork1b2c"  # pragma: allowlist secret
down_revision = "a3029merge1b2c"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Full post-Spec-32 vocabulary (adds the two review-workspace assist agents).
_AGENT_CHECK_NEW = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant')"
)
# Prior state (post Spec 29).
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
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
