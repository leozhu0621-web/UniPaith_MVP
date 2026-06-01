"""Spec 33 (Interviews Module): async windows, recording, recommendation,
invite notes, interview rubric kind, and two new AI agents.

This revision is additive only:

1. **Extends ``interviews``** with the Spec 33 §5/§7/§8 fields:
   - ``async_window_end`` — submission window end for recorded_async /
     technical_assessment; past-with-no-recording renders "No submission
     received" (§8) in the response (no cron needed).
   - ``recording_url`` — link to the async / live recording (§7).
   - ``recommendation`` — denormalized latest recommend/neutral/not_recommend
     mirrored from ``interview_scores`` so the §4 KPI table avoids a join.
   - ``notes_to_student`` — invite notes (§5), mirrored into the Inbox body.
   Plus widens ``interview_type`` to 30 chars to admit the longest spec value
   (``technical_assessment`` / ``third_party_platform``).
2. **Extends ``rubrics``** with ``rubric_kind`` ('application' default,
   'interview' for the interviewing rubric, §6).
3. **Widens ``ck_ai_turns_agent``** to admit ``interview_invite_drafter``
   (Haiku) + ``interview_score_prefill`` (Sonnet), §9.

Chains off ``s3132merge1b2c`` (the merged Spec 31/32 head) so the graph stays a
single linear head (``test_alembic_has_single_head``). All operations are
guarded with ``_has_table`` / ``_has_column`` so the revision is a safe no-op
against a dev/test DB built from the models via ``create_all``.

Revision ID: d33a1b2c4e5f
Revises: s3132merge1b2c
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d33a1b2c4e5f"  # pragma: allowlist secret
down_revision = "s3132merge1b2c"  # pragma: allowlist secret
branch_labels = None
depends_on = None


# Full post-Spec-33 vocabulary (adds the two interview agents on top of the
# Spec 31 intelligence_digest + Spec 32 review-assist agents).
_AGENT_CHECK_NEW = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest',"
    "'interview_invite_drafter','interview_score_prefill')"
)
# Prior state (post Spec 31/32 — includes the review-assist + intelligence_digest
# agents, not yet the interview agents).
_AGENT_CHECK_OLD = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier',"
    "'review_synthesis','review_assistant','intelligence_digest')"
)


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {c["name"] for c in _inspector().get_columns(table)}


def upgrade() -> None:
    # ── 1. extend interviews with the Spec 33 §5/§7/§8 shape ──
    if _has_table("interviews"):
        # Widen interview_type to fit the longest spec value.
        op.execute("ALTER TABLE interviews ALTER COLUMN interview_type TYPE varchar(30)")
        if not _has_column("interviews", "async_window_end"):
            op.add_column(
                "interviews",
                sa.Column("async_window_end", sa.DateTime(timezone=True), nullable=True),
            )
        if not _has_column("interviews", "recording_url"):
            op.add_column(
                "interviews", sa.Column("recording_url", sa.String(length=1000), nullable=True)
            )
        if not _has_column("interviews", "recommendation"):
            op.add_column(
                "interviews", sa.Column("recommendation", sa.String(length=20), nullable=True)
            )
        if not _has_column("interviews", "notes_to_student"):
            op.add_column("interviews", sa.Column("notes_to_student", sa.Text(), nullable=True))

    # ── 1b. interview_scores gets a created_at for chronological ordering ──
    if _has_table("interview_scores") and not _has_column("interview_scores", "created_at"):
        op.add_column(
            "interview_scores",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    # ── 2. extend rubrics with the interview-vs-application kind (§6) ──
    if _has_table("rubrics") and not _has_column("rubrics", "rubric_kind"):
        op.add_column(
            "rubrics",
            sa.Column(
                "rubric_kind",
                sa.String(length=20),
                nullable=False,
                server_default="application",
            ),
        )

    # ── 3. widen ck_ai_turns_agent for the two interview agents (§9) ──
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

    if _has_table("rubrics") and _has_column("rubrics", "rubric_kind"):
        op.drop_column("rubrics", "rubric_kind")

    if _has_table("interview_scores") and _has_column("interview_scores", "created_at"):
        op.drop_column("interview_scores", "created_at")

    if _has_table("interviews"):
        for col in ("notes_to_student", "recommendation", "recording_url", "async_window_end"):
            if _has_column("interviews", col):
                op.drop_column("interviews", col)
