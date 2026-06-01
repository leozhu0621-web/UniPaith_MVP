"""Spec 35 — Enrollment Confirmation & Yield.

Extends the thin ``enrollment_records`` placeholder into the §5 state machine
(``accepted → intent_confirmed → deposit_recorded → enrollment_confirmed →
enrolled`` ↘ ``withdrew`` / ``deferred``), adds waitlist ranking to
``applications`` (§3.3), and widens ``ck_ai_turns_agent`` for the two new
enrollment/yield intelligence agents (``yield_risk_scorer`` +
``next_best_action_yield``, §6).

Every change is additive and guarded (``IF NOT EXISTS`` / column-presence
checks) so it is a safe no-op against a dev/test DB built from the models via
``create_all`` (those columns already exist there).

Revision ID: t35a1b2c3d4e
Revises: d33a1b2c4e5f
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "t35a1b2c3d4e"  # pragma: allowlist secret
# Rebased onto the Spec 33 head (d33a1b2c4e5f, the current single head) so the
# migration graph stays single-headed (test_alembic_has_single_head). Originally
# chained off a32revwork1b2c before Spec 31/32/33 merged ahead of this branch.
down_revision = "d33a1b2c4e5f"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Full post-Spec-35 agent vocabulary (chains off Spec 33, which already added
# intelligence_digest + the two interview agents).
_AGENT_CHECK_NEW = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest',"
    "'interview_invite_drafter','interview_score_prefill',"
    "'yield_risk_scorer','next_best_action_yield')"
)
# Prior state (post Spec 33 — the down_revision's vocabulary).
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest',"
    "'interview_invite_drafter','interview_score_prefill')"
)


def _has_table(name: str) -> bool:
    return name in sa.inspect(op.get_bind()).get_table_names()


def _columns(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    # 1) enrollment_records — §5 state machine columns (additive).
    if _has_table("enrollment_records"):
        cols = _columns("enrollment_records")
        if "offer_id" not in cols:
            op.add_column(
                "enrollment_records",
                sa.Column("offer_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                "fk_enrollment_records_offer_id",
                "enrollment_records",
                "offer_letters",
                ["offer_id"],
                ["id"],
                ondelete="SET NULL",
            )
        if "state" not in cols:
            op.add_column(
                "enrollment_records",
                sa.Column("state", sa.String(24), server_default="accepted", nullable=False),
            )
        if "deposit_status" not in cols:
            op.add_column(
                "enrollment_records",
                sa.Column("deposit_status", sa.String(10), server_default="none", nullable=False),
            )
        for name, col in (
            ("deposit_amount", sa.Column("deposit_amount", sa.Integer(), nullable=True)),
            (
                "intent_confirmed_at",
                sa.Column("intent_confirmed_at", sa.DateTime(timezone=True), nullable=True),
            ),
            (
                "enrollment_confirmed_at",
                sa.Column("enrollment_confirmed_at", sa.DateTime(timezone=True), nullable=True),
            ),
            ("decline_reason", sa.Column("decline_reason", sa.Text(), nullable=True)),
            ("deferral", sa.Column("deferral", postgresql.JSONB(), nullable=True)),
            ("checklist", sa.Column("checklist", postgresql.JSONB(), nullable=True)),
            (
                "created_at",
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False,
                ),
            ),
            (
                "updated_at",
                sa.Column(
                    "updated_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False,
                ),
            ),
        ):
            if name not in cols:
                op.add_column("enrollment_records", col)

    # 2) applications — waitlist ranking (§3.3).
    if _has_table("applications"):
        cols = _columns("applications")
        if "waitlist_rank" not in cols:
            op.add_column("applications", sa.Column("waitlist_rank", sa.Integer(), nullable=True))
        if "waitlisted_at" not in cols:
            op.add_column(
                "applications",
                sa.Column("waitlisted_at", sa.DateTime(timezone=True), nullable=True),
            )

    # 3) ai_turns — widen the agent CHECK for the two new yield agents (§6).
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

    if _has_table("applications"):
        cols = _columns("applications")
        for name in ("waitlisted_at", "waitlist_rank"):
            if name in cols:
                op.drop_column("applications", name)

    if _has_table("enrollment_records"):
        cols = _columns("enrollment_records")
        # IF EXISTS — the FK may carry an auto-generated name on DBs built via
        # create_all rather than this migration; never let its absence abort.
        op.execute(
            "ALTER TABLE enrollment_records "
            "DROP CONSTRAINT IF EXISTS fk_enrollment_records_offer_id"
        )
        for name in (
            "updated_at",
            "created_at",
            "checklist",
            "deferral",
            "decline_reason",
            "enrollment_confirmed_at",
            "intent_confirmed_at",
            "deposit_amount",
            "deposit_status",
            "state",
            "offer_id",
        ):
            if name in cols:
                op.drop_column("enrollment_records", name)
