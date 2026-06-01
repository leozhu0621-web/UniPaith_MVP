"""spec 31 — admissions intake: digest agent + integrity resolution

Spec 31 §9 / §11: the intelligence-digest narrator (Sonnet, migrated off
GPT-4o per 45 §11) logs to ``ai_turns`` under the agent name
``intelligence_digest``, so that name must be allowed by the
``ck_ai_turns_agent`` CHECK constraint.

Spec 31 §6: the integrity-signal resolve workflow records WHICH outcome the
reviewer chose (acceptable | requires_clarification | reject_application) on a
new ``integrity_signals.resolution`` column.

Idempotent by repo convention (a sibling branch may materialize tables from
current model metadata via create_all(checkfirst=True)), so every statement is
guarded.

Revision ID: b31a1c2d3e4f
Revises: a3029merge1b2c
Create Date: 2026-06-01 13:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers
revision: str = "b31a1c2d3e4f"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "a3029merge1b2c"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_AGENTS_PRE = (
    "'orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher','query_interpreter',"
    "'inbox_reply_drafter','connect_ranker','event_recommender',"
    "'campaign_copy','document_parse_triage','segment_builder_nl',"
    "'institution_reply_drafter','inbound_intent_classifier'"
)
_NEW_AGENT_CHECK = f"agent IN ({_AGENTS_PRE},'intelligence_digest')"
_OLD_AGENT_CHECK = f"agent IN ({_AGENTS_PRE})"


def upgrade() -> None:
    # ── ai_turns.agent CHECK — allow the dashboard digest narrator (§9) ──
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_NEW_AGENT_CHECK})")

    # ── integrity_signals.resolution — reviewer's resolution outcome (§6) ──
    op.execute("ALTER TABLE integrity_signals ADD COLUMN IF NOT EXISTS resolution VARCHAR(30)")


def downgrade() -> None:
    op.execute("ALTER TABLE integrity_signals DROP COLUMN IF EXISTS resolution")
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_OLD_AGENT_CHECK})")
