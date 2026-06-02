"""Spec 42 — Prompt Library + Story Bank (canonical signal schema).

Adds the behavioral-prompt layer (Spec 42 §3.19–§3.20 / §8): the platform
``behavioral_prompts`` catalog, ``student_stories`` (story bank), and
``student_behavioral_responses`` (per-prompt responses + STAR/impact flags),
all carrying the universal record metadata (§5 ``SignalRecordMixin``). Widens
``ck_ai_turns_agent`` for the new deterministic ``prompt_coach`` agent (§4.17).

Every table create is guarded (``_has_table``) so the migration is a safe no-op
against a dev/test DB built from the models via ``create_all`` (conftest path).

Revision ID: p42a1b2c3d4e
Revises: r40a1b2c3d4e
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "p42a1b2c3d4e"  # pragma: allowlist secret
# Rebased onto the current single head after Spec 41 (Graduate & PhD Admissions,
# g41a1b2c3d4e, #237) merged ahead of this branch. Spec 41 chains off the Spec
# 12 backfill (b12c0de5f7a9) and adds three graduate agents to ck_ai_turns_agent,
# so the agent CHECK constants below extend the post-Spec-41 vocabulary. Chaining
# off g41 keeps the graph single-headed (test_alembic_has_single_head).
down_revision = "g41a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Post-Spec-42 agent vocabulary (adds the deterministic prompt_coach to the
# post-Spec-41 set).
_AGENT_CHECK_NEW = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest',"
    "'interview_invite_drafter','interview_score_prefill',"
    "'yield_risk_scorer','next_best_action_yield',"
    "'credential_normalizer','country_requirement_advisor',"
    "'prospect_prioritizer','territory_optimizer',"
    "'advisor_matcher','sop_interest_extractor','funding_scenario_helper',"
    "'prompt_coach')"
)
# Prior state (the down_revision's vocabulary — post-Spec-41 set).
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest',"
    "'interview_invite_drafter','interview_score_prefill',"
    "'yield_risk_scorer','next_best_action_yield',"
    "'credential_normalizer','country_requirement_advisor',"
    "'prospect_prioritizer','territory_optimizer',"
    "'advisor_matcher','sop_interest_extractor','funding_scenario_helper')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _ts_cols() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def _signal_cols() -> list[sa.Column]:
    """Spec 42 §5 — universal record-metadata columns (SignalRecordMixin)."""
    return [
        sa.Column("source", sa.String(32), nullable=False, server_default="student-typed"),
        sa.Column("confidence", sa.Integer(), nullable=False, server_default="70"),
        sa.Column("value_normalized", postgresql.JSONB(), nullable=True),
        sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("raw_input_ref", sa.String(255), nullable=True),
        sa.Column(
            "provenance_chain",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    ]


_SOURCE_CHECK = (
    "source IN ('student-typed','student-uploaded','student-link','student-derived',"
    "'institution-supplied','system-derived','system-extracted','third-party-verified')"
)


def upgrade() -> None:
    # 1) behavioral_prompts — platform catalog (no student FK).
    if not _has_table("behavioral_prompts"):
        op.create_table(
            "behavioral_prompts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("prompt_key", sa.String(80), nullable=False, unique=True),
            sa.Column("title", sa.Text(), nullable=False),
            sa.Column("intent_tag", sa.String(20), nullable=False),
            sa.Column("target_channel", sa.String(16), nullable=False, server_default="interview"),
            sa.Column("time_limit_seconds", sa.Integer(), nullable=True),
            sa.Column("word_limit", sa.Integer(), nullable=True),
            sa.Column("format_required", sa.String(10), nullable=False, server_default="STAR"),
            sa.Column(
                "evidence_required_flag", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column(
                "allowed_attachments_flag", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column("language_option", sa.String(8), nullable=False, server_default="en"),
            sa.Column(
                "confidentiality_scope", sa.String(20), nullable=False, server_default="private"
            ),
            sa.Column("reuse_allowed_flag", sa.String(16), nullable=False, server_default="core"),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
            sa.CheckConstraint(
                "intent_tag IN ('leadership','conflict','failure','impact','ethics','learning',"
                "'motivation','fit','vision','curiosity','resilience','service','teamwork',"
                "'communication','identity')",
                name="ck_behavioral_prompts_intent",
            ),
            sa.CheckConstraint(
                "target_channel IN ('interview','essay','short_answer','video')",
                name="ck_behavioral_prompts_channel",
            ),
            sa.CheckConstraint(
                "format_required IN ('STAR','CAR','freeform')",
                name="ck_behavioral_prompts_format",
            ),
            sa.CheckConstraint(
                "confidentiality_scope IN ('private','shareable','recommender_facing')",
                name="ck_behavioral_prompts_confidentiality",
            ),
            sa.CheckConstraint(
                "reuse_allowed_flag IN ('core','school_specific')",
                name="ck_behavioral_prompts_reuse",
            ),
            *_ts_cols(),
        )
        op.create_index(
            "ix_behavioral_prompts_active_sort", "behavioral_prompts", ["is_active", "sort_order"]
        )
        op.create_index("ix_behavioral_prompts_intent", "behavioral_prompts", ["intent_tag"])

    # 2) student_stories (referenced by student_behavioral_responses.linked_story_id).
    if not _has_table("student_stories"):
        op.create_table(
            "student_stories",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "student_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("primary_competency", sa.String(20), nullable=True),
            sa.Column("secondary_competency", sa.String(20), nullable=True),
            sa.Column(
                "competency_tags",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column(
                "context_tags",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column("role_type", sa.String(16), nullable=True),
            sa.Column("stakeholder_type", sa.String(16), nullable=True),
            sa.Column("conflict_type", sa.String(16), nullable=True),
            sa.Column("difficulty_tier", sa.Integer(), nullable=True),
            sa.Column("recency", sa.Date(), nullable=True),
            sa.Column("duration", sa.String(80), nullable=True),
            sa.Column("scale_tier", sa.Integer(), nullable=True),
            sa.Column("evidence_link", sa.String(500), nullable=True),
            sa.Column(
                "referenceable_contact_flag", sa.Boolean(), nullable=False, server_default="false"
            ),
            *_signal_cols(),
            sa.CheckConstraint(
                "primary_competency IS NULL OR primary_competency IN ('leadership','teamwork',"
                "'impact','resilience','creativity','analytical','communication','initiative')",
                name="ck_student_stories_primary_competency",
            ),
            sa.CheckConstraint(
                "secondary_competency IS NULL OR secondary_competency IN ('leadership','teamwork',"
                "'impact','resilience','creativity','analytical','communication','initiative')",
                name="ck_student_stories_secondary_competency",
            ),
            sa.CheckConstraint(
                "role_type IS NULL OR role_type IN ('leader','contributor','founder','observer')",
                name="ck_student_stories_role_type",
            ),
            sa.CheckConstraint(
                "stakeholder_type IS NULL OR stakeholder_type IN ('peers','authority','clients',"
                "'public','self')",
                name="ck_student_stories_stakeholder_type",
            ),
            sa.CheckConstraint(
                "conflict_type IS NULL OR conflict_type IN ('interpersonal','resource','ethical',"
                "'technical','time','none')",
                name="ck_student_stories_conflict_type",
            ),
            sa.CheckConstraint(
                "difficulty_tier IS NULL OR (difficulty_tier BETWEEN 1 AND 5)",
                name="ck_student_stories_difficulty_tier",
            ),
            sa.CheckConstraint(
                "scale_tier IS NULL OR (scale_tier BETWEEN 1 AND 5)",
                name="ck_student_stories_scale_tier",
            ),
            sa.CheckConstraint(_SOURCE_CHECK, name="ck_student_stories_source"),
            *_ts_cols(),
        )
        op.create_index("ix_student_stories_student", "student_stories", ["student_id"])
        op.create_index(
            "ix_student_stories_student_competency",
            "student_stories",
            ["student_id", "primary_competency"],
        )

    # 3) student_behavioral_responses.
    if not _has_table("student_behavioral_responses"):
        op.create_table(
            "student_behavioral_responses",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "student_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("prompt_key", sa.String(80), nullable=False),
            sa.Column("response_text", sa.Text(), nullable=True),
            sa.Column("draft_status", sa.String(12), nullable=False, server_default="none"),
            sa.Column("last_edited", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("confidence_self_rating", sa.Integer(), nullable=True),
            sa.Column(
                "authenticity_confidence_flag", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column("needs_feedback_flag", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column(
                "reviewer_feedback_received_flag",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            ),
            sa.Column(
                "star_situation_present", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column("star_task_present", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("star_action_present", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column("star_result_present", sa.Boolean(), nullable=False, server_default="false"),
            sa.Column(
                "star_reflection_present", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column(
                "impact_metric_present", sa.Boolean(), nullable=False, server_default="false"
            ),
            sa.Column("impact_metric_type", sa.String(10), nullable=True),
            sa.Column("impact_metric_value_band", sa.String(40), nullable=True),
            sa.Column(
                "linked_story_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("student_stories.id", ondelete="SET NULL"),
                nullable=True,
            ),
            *_signal_cols(),
            sa.UniqueConstraint(
                "student_id",
                "prompt_key",
                name="uq_student_behavioral_responses_student_prompt",
            ),
            sa.CheckConstraint(
                "draft_status IN ('none','draft','revised','final')",
                name="ck_student_behavioral_responses_draft",
            ),
            sa.CheckConstraint(
                "confidence_self_rating IS NULL OR (confidence_self_rating BETWEEN 1 AND 5)",
                name="ck_student_behavioral_responses_self_rating",
            ),
            sa.CheckConstraint(
                "impact_metric_type IS NULL OR impact_metric_type IN ('count','percent','dollar',"
                "'time','scale')",
                name="ck_student_behavioral_responses_impact_type",
            ),
            sa.CheckConstraint(_SOURCE_CHECK, name="ck_student_behavioral_responses_source"),
            *_ts_cols(),
        )
        op.create_index(
            "ix_student_behavioral_responses_student",
            "student_behavioral_responses",
            ["student_id"],
        )
        op.create_index(
            "ix_student_behavioral_responses_student_status",
            "student_behavioral_responses",
            ["student_id", "draft_status"],
        )

    # 4) ai_turns — widen the agent CHECK for the deterministic prompt_coach (§4.17).
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

    for tbl in (
        "student_behavioral_responses",
        "student_stories",
        "behavioral_prompts",
    ):
        if _has_table(tbl):
            op.drop_table(tbl)
