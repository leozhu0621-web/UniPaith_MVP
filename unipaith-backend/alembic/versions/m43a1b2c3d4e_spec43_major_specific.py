"""Spec 43 — Major-Specific Field Catalog (canonical signal store).

Adds ``student_major_specific_signals`` (Spec 42 §3.18 / §8): one row per
``(student, track_key)`` holding the per-discipline signal subdocument as JSONB,
carrying the universal record metadata (§5 ``SignalRecordMixin``). Migrates the
pre-spec ``student_major_readiness`` scaffold (raw 6-track store, no provenance)
into the new table with a track-key remap, then drops it. Widens
``ck_ai_turns_agent`` for the new deterministic ``major_track_coach`` (§4.18).

Every table create + the legacy migrate/drop is guarded (``_has_table``) so the
migration is a safe no-op against a dev/test DB built from the models via
``create_all`` (conftest path), where the legacy table no longer exists.

Revision ID: m43a1b2c3d4e
Revises: p42a1b2c3d4e
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "m43a1b2c3d4e"  # pragma: allowlist secret
down_revision = "p42a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Post-Spec-43 agent vocabulary (adds the deterministic major_track_coach to the
# post-Spec-42 set).
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
    "'prompt_coach','major_track_coach')"
)
# Prior state (the down_revision's vocabulary — post-Spec-42 set, ends prompt_coach).
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
    "'advisor_matcher','sop_interest_extractor','funding_scenario_helper',"
    "'prompt_coach')"
)

# Pre-spec 6-track scaffold names → Spec 43 track_keys (3 differ, 3 pass through).
_TRACK_REMAP_SQL = (
    "CASE track "
    "WHEN 'cs' THEN 'cs_data_ai' "
    "WHEN 'arts' THEN 'arts_design' "
    "WHEN 'humanities' THEN 'humanities_social_sciences' "
    "ELSE track END"
)
# Reverse, for the downgrade (only the 6 legacy tracks are representable).
_TRACK_UNMAP_SQL = (
    "CASE track_key "
    "WHEN 'cs_data_ai' THEN 'cs' "
    "WHEN 'arts_design' THEN 'arts' "
    "WHEN 'humanities_social_sciences' THEN 'humanities' "
    "ELSE track_key END"
)
_LEGACY_TRACK_KEYS = (
    "'cs_data_ai','arts_design','humanities_social_sciences','engineering','business','health'"
)

_SOURCE_CHECK = (
    "source IN ('student-typed','student-uploaded','student-link','student-derived',"
    "'institution-supplied','system-derived','system-extracted','third-party-verified')"
)
_TRACK_KEY_CHECK = (
    "track_key IN ('cs_data_ai','engineering','business','health','arts_design',"
    "'performing_arts','humanities_social_sciences','law_policy','education_counseling',"
    "'journalism_communications','math_physics_chemistry_sciences','comp_engineering_robotics',"
    "'environmental_sustainability','language_linguistics','entrepreneurship_product')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    # 1) student_major_specific_signals — the canonical per-(student, track) store.
    if not _has_table("student_major_specific_signals"):
        op.create_table(
            "student_major_specific_signals",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "student_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("track_key", sa.String(40), nullable=False),
            sa.Column(
                "signals",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            # SignalRecordMixin (§5).
            sa.Column("source", sa.String(32), nullable=False, server_default="student-typed"),
            sa.Column("confidence", sa.Integer(), nullable=False, server_default="95"),
            sa.Column("value_normalized", postgresql.JSONB(), nullable=True),
            sa.Column("record_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("raw_input_ref", sa.String(255), nullable=True),
            sa.Column(
                "provenance_chain",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint(
                "student_id", "track_key", name="uq_student_major_specific_student_track"
            ),
            sa.CheckConstraint(_TRACK_KEY_CHECK, name="ck_student_major_specific_track"),
            sa.CheckConstraint(_SOURCE_CHECK, name="ck_student_major_specific_source"),
        )
        op.create_index(
            "ix_student_major_specific_student",
            "student_major_specific_signals",
            ["student_id"],
        )

    # 2) Migrate the pre-spec scaffold into the new store (track-key remap), then
    #    drop it. Guarded — absent in the conftest create_all path.
    if _has_table("student_major_readiness"):
        op.execute(
            "INSERT INTO student_major_specific_signals "
            "(id, student_id, track_key, signals, source, confidence, record_version, "
            "provenance_chain, created_at, updated_at) "
            f"SELECT id, student_id, {_TRACK_REMAP_SQL}, readiness_data, 'student-typed', 95, 1, "
            "'[]'::jsonb, created_at, updated_at FROM student_major_readiness "
            "ON CONFLICT (student_id, track_key) DO NOTHING"
        )
        op.drop_table("student_major_readiness")

    # 3) ai_turns — widen the agent CHECK for the deterministic major_track_coach.
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

    # Recreate the pre-spec scaffold and copy back the representable 6 tracks.
    if not _has_table("student_major_readiness"):
        op.create_table(
            "student_major_readiness",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "student_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("track", sa.String(30), nullable=False),
            sa.Column("readiness_data", postgresql.JSONB(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.UniqueConstraint("student_id", "track", name="uq_major_readiness_student_track"),
        )
        if _has_table("student_major_specific_signals"):
            op.execute(
                "INSERT INTO student_major_readiness "
                "(id, student_id, track, readiness_data, created_at, updated_at) "
                f"SELECT id, student_id, {_TRACK_UNMAP_SQL}, signals, created_at, updated_at "
                "FROM student_major_specific_signals "
                f"WHERE track_key IN ({_LEGACY_TRACK_KEYS}) "
                "ON CONFLICT (student_id, track) DO NOTHING"
            )

    if _has_table("student_major_specific_signals"):
        op.drop_table("student_major_specific_signals")
