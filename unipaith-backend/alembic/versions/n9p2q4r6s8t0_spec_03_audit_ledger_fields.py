"""spec 03 — audit ledger fields + match rationale prompt_version

Spec §8: every Claude call writes provider, success/failure_reason,
consent_mask, and explicit request_started_at / request_completed_at to
the ai_turns ledger. Also merges the two open alembic heads
(ac252aa411c3 + 1499ba1b4c8a) into one chain so deploys can roll forward.

Spec §12: cache invalidation must trigger on prompt_version change.
Extends match_rationales PK with prompt_version (default 1) so a prompt
iteration forces re-derivation without dropping prior rows.

Backfill rule: legacy rows get provider='anthropic' (true historically —
no other provider existed before this migration) and success=true (the
old code only logged successful calls; failures raised before reaching
_log_turn). failure_reason stays NULL for historical rows.

Revision ID: n9p2q4r6s8t0
Revises: ac252aa411c3, 1499ba1b4c8a
Create Date: 2026-05-30 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers
revision: str = "n9p2q4r6s8t0"
down_revision: str | Sequence[str] | None = ("ac252aa411c3", "1499ba1b4c8a")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Idempotent by repo convention: a sibling branch runs
    # `Base.metadata.create_all(checkfirst=True)` (d3f4a5b6c7d8) which can
    # materialize ai_turns / match_rationales from the *current* model
    # metadata — already including these columns, check constraints, and
    # index. Guarding every statement makes this migration safe regardless
    # of which branch alembic applies first.

    # ── ai_turns: spec §8 fields ─────────────────────────────────────────
    op.execute(
        "ALTER TABLE ai_turns ADD COLUMN IF NOT EXISTS "
        "provider VARCHAR(20) NOT NULL DEFAULT 'anthropic'"
    )
    op.execute(
        "ALTER TABLE ai_turns ADD COLUMN IF NOT EXISTS success BOOLEAN NOT NULL DEFAULT TRUE"
    )
    op.execute("ALTER TABLE ai_turns ADD COLUMN IF NOT EXISTS failure_reason VARCHAR(40)")
    op.execute("ALTER TABLE ai_turns ADD COLUMN IF NOT EXISTS consent_mask JSONB")
    op.execute("ALTER TABLE ai_turns ADD COLUMN IF NOT EXISTS request_started_at TIMESTAMPTZ")
    op.execute("ALTER TABLE ai_turns ADD COLUMN IF NOT EXISTS request_completed_at TIMESTAMPTZ")

    # Check constraints — Postgres lacks ADD CONSTRAINT IF NOT EXISTS, so
    # guard on pg_constraint. provider ∈ anthropic|openai|bedrock|rule_based.
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_ai_turns_provider') THEN "
        "ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_provider "
        "CHECK (provider IN ('anthropic','openai','bedrock','rule_based')); "
        "END IF; END $$;"
    )
    # failure_reason enum (NULL allowed for historical/success rows).
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_constraint "
        "WHERE conname = 'ck_ai_turns_failure_reason') THEN "
        "ALTER TABLE ai_turns ADD CONSTRAINT ck_ai_turns_failure_reason "
        "CHECK (failure_reason IS NULL OR failure_reason IN ("
        "'parse_error','timeout','guardrail_trip','provider_5xx',"
        "'rule_based_fallback','consent_denied','cost_cap','unknown')); "
        "END IF; END $$;"
    )
    # Composite index for cost dashboards: (provider, agent, created_at).
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ai_turns_provider_agent_created "
        "ON ai_turns (provider, agent, created_at)"
    )

    # ── match_rationales: spec §12 prompt_version in cache key ───────────
    op.execute(
        "ALTER TABLE match_rationales ADD COLUMN IF NOT EXISTS "
        "prompt_version INTEGER NOT NULL DEFAULT 1"
    )
    # Rebuild the PK to include prompt_version only if it isn't there yet —
    # create_all may have already built the 5-column PK from the model.
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM information_schema.key_column_usage "
        "WHERE constraint_name = 'match_rationales_pkey' "
        "AND column_name = 'prompt_version') THEN "
        "ALTER TABLE match_rationales DROP CONSTRAINT match_rationales_pkey; "
        "ALTER TABLE match_rationales ADD CONSTRAINT match_rationales_pkey "
        "PRIMARY KEY (student_id, program_id, profile_version, program_version, prompt_version); "
        "END IF; END $$;"
    )


def downgrade() -> None:
    # match_rationales: revert PK (guarded so a partial state is safe).
    op.execute(
        "DO $$ BEGIN "
        "IF EXISTS (SELECT 1 FROM information_schema.key_column_usage "
        "WHERE constraint_name = 'match_rationales_pkey' "
        "AND column_name = 'prompt_version') THEN "
        "ALTER TABLE match_rationales DROP CONSTRAINT match_rationales_pkey; "
        "ALTER TABLE match_rationales ADD CONSTRAINT match_rationales_pkey "
        "PRIMARY KEY (student_id, program_id, profile_version, program_version); "
        "END IF; END $$;"
    )
    op.execute("ALTER TABLE match_rationales DROP COLUMN IF EXISTS prompt_version")

    # ai_turns: drop new columns + constraints + index.
    op.execute("DROP INDEX IF EXISTS ix_ai_turns_provider_agent_created")
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_failure_reason")
    op.execute("ALTER TABLE ai_turns DROP CONSTRAINT IF EXISTS ck_ai_turns_provider")
    op.execute("ALTER TABLE ai_turns DROP COLUMN IF EXISTS request_completed_at")
    op.execute("ALTER TABLE ai_turns DROP COLUMN IF EXISTS request_started_at")
    op.execute("ALTER TABLE ai_turns DROP COLUMN IF EXISTS consent_mask")
    op.execute("ALTER TABLE ai_turns DROP COLUMN IF EXISTS failure_reason")
    op.execute("ALTER TABLE ai_turns DROP COLUMN IF EXISTS success")
    op.execute("ALTER TABLE ai_turns DROP COLUMN IF EXISTS provider")
