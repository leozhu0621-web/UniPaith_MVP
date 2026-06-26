"""add strategy/outcome_brief/identity_summary to ck_ai_turns_agent

The discovery-handoff strategy generator, the offer outcome-brief, and the
identity-summary narrator all write audit rows with
``agent IN ('strategy','outcome_brief','identity_summary')`` via
``AIClient.message(... db=db)``. Those names were never added to the
``ck_ai_turns_agent`` CHECK, so in production (``mock_mode`` off, real
provider + real session) every *successful* call raised an IntegrityError on
``db.flush()`` — the agent's ``except`` swallowed it and returned its stub
template, and the failed flush poisoned the surrounding request transaction.
Tests never caught it because ``mock_mode`` returns before the turn is logged.

Extend the CHECK to admit the three agent names. Mirrors
``unipaith.models.ai_artifacts.AiTurn`` and ``unipaith.ai.client.Agent``.

Revision ID: aiturnagents1
Revises: uclawhotuition1
Create Date: 2026-06-26
"""

from __future__ import annotations

from alembic import op

revision = "aiturnagents1"
down_revision = "uclawhotuition1"
branch_labels = None
depends_on = None


_AGENTS_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'intelligence_digest',"
    "'review_synthesis','review_assistant',"
    "'interview_invite_drafter','interview_score_prefill',"
    "'yield_risk_scorer','next_best_action_yield',"
    "'credential_normalizer','country_requirement_advisor',"
    "'prospect_prioritizer','territory_optimizer',"
    "'advisor_matcher','sop_interest_extractor','funding_scenario_helper')"
)

_AGENTS_NEW = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'intelligence_digest',"
    "'review_synthesis','review_assistant',"
    "'interview_invite_drafter','interview_score_prefill',"
    "'yield_risk_scorer','next_best_action_yield',"
    "'credential_normalizer','country_requirement_advisor',"
    "'prospect_prioritizer','territory_optimizer',"
    "'advisor_matcher','sop_interest_extractor','funding_scenario_helper',"
    "'strategy','outcome_brief','identity_summary')"
)


def upgrade() -> None:
    op.drop_constraint("ck_ai_turns_agent", "ai_turns", type_="check")
    op.create_check_constraint("ck_ai_turns_agent", "ai_turns", _AGENTS_NEW)


def downgrade() -> None:
    op.drop_constraint("ck_ai_turns_agent", "ai_turns", type_="check")
    op.create_check_constraint("ck_ai_turns_agent", "ai_turns", _AGENTS_OLD)
