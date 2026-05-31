"""spec 06 — programs.feature_version + new ai_turns agent names

Spec 06 §5.4: the rationale cache is keyed by program_version, but the
`programs` table had no version column, so cache invalidation on a program
edit was a dead no-op (call sites read getattr(...,1) → always 1). Adds
`programs.feature_version` (default 1) so a published-program edit can bump
it and invalidate the cached rationales.

Spec 06 §2: two new L2 agents (DraftSummarizerForReview → 'review_summarizer',
AuthenticityRiskScorer → 'authenticity_risk') and the L3 ML scorer's audit
label ('matcher') must be allowed in the ai_turns.agent CHECK constraint.

Idempotent by repo convention (a sibling branch may materialize tables from
current model metadata via create_all(checkfirst=True)), so every statement
is guarded.

Revision ID: a6c1f0d2e3b4
Revises: p3q5r7s9t1u3
Create Date: 2026-05-30 20:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers
revision: str = "a6c1f0d2e3b4"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = "p3q5r7s9t1u3"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_NEW_AGENT_CHECK = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding',"
    "'review_summarizer','authenticity_risk','matcher')"
)
_OLD_AGENT_CHECK = (
    "agent IN ('orchestrator','extractor','validator','feature_emitter',"
    "'rationale','workshop_coach','workshop_judge','embedding')"
)


def upgrade() -> None:
    # ── programs.feature_version (spec 06 §5.4) ──────────────────────────
    op.execute(
        "ALTER TABLE programs ADD COLUMN IF NOT EXISTS feature_version INTEGER NOT NULL DEFAULT 1"
    )

    # ── ai_turns.agent CHECK — widen for the new agents (spec 06 §2) ─────
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_NEW_AGENT_CHECK})")


def downgrade() -> None:
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_agent")
    op.execute(f"ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_agent CHECK ({_OLD_AGENT_CHECK})")
    op.execute("ALTER TABLE programs DROP COLUMN IF EXISTS feature_version")
