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

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers
revision: str = "n9p2q4r6s8t0"
down_revision: str | Sequence[str] | None = ("ac252aa411c3", "1499ba1b4c8a")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── ai_turns: spec §8 fields ─────────────────────────────────────────
    op.add_column(
        "ai_turns",
        sa.Column(
            "provider",
            sa.String(20),
            nullable=False,
            server_default="anthropic",
        ),
    )
    op.add_column(
        "ai_turns",
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "ai_turns",
        sa.Column("failure_reason", sa.String(40), nullable=True),
    )
    op.add_column(
        "ai_turns",
        sa.Column("consent_mask", JSONB(), nullable=True),
    )
    op.add_column(
        "ai_turns",
        sa.Column("request_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "ai_turns",
        sa.Column("request_completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Provider check constraint: anthropic | openai | bedrock | rule_based
    op.create_check_constraint(
        "ck_ai_turns_provider",
        "ai_turns",
        "provider IN ('anthropic','openai','bedrock','rule_based')",
    )
    # failure_reason enum: parse_error | timeout | guardrail_trip |
    # provider_5xx | rule_based_fallback | consent_denied | cost_cap
    op.create_check_constraint(
        "ck_ai_turns_failure_reason",
        "ai_turns",
        "failure_reason IS NULL OR failure_reason IN ("
        "'parse_error','timeout','guardrail_trip','provider_5xx',"
        "'rule_based_fallback','consent_denied','cost_cap','unknown')",
    )
    # Composite index for cost dashboards: (provider, agent, created_at)
    op.create_index(
        "ix_ai_turns_provider_agent_created",
        "ai_turns",
        ["provider", "agent", "created_at"],
    )

    # ── match_rationales: spec §12 prompt_version in cache key ───────────
    # Drop the old PK, add prompt_version, recreate PK including it.
    op.add_column(
        "match_rationales",
        sa.Column(
            "prompt_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.drop_constraint("match_rationales_pkey", "match_rationales", type_="primary")
    op.create_primary_key(
        "match_rationales_pkey",
        "match_rationales",
        ["student_id", "program_id", "profile_version", "program_version", "prompt_version"],
    )


def downgrade() -> None:
    # match_rationales: revert PK
    op.drop_constraint("match_rationales_pkey", "match_rationales", type_="primary")
    op.drop_column("match_rationales", "prompt_version")
    op.create_primary_key(
        "match_rationales_pkey",
        "match_rationales",
        ["student_id", "program_id", "profile_version", "program_version"],
    )

    # ai_turns: drop new columns + constraints
    op.drop_index("ix_ai_turns_provider_agent_created", table_name="ai_turns")
    op.drop_constraint("ck_ai_turns_failure_reason", "ai_turns", type_="check")
    op.drop_constraint("ck_ai_turns_provider", "ai_turns", type_="check")
    op.drop_column("ai_turns", "request_completed_at")
    op.drop_column("ai_turns", "request_started_at")
    op.drop_column("ai_turns", "consent_mask")
    op.drop_column("ai_turns", "failure_reason")
    op.drop_column("ai_turns", "success")
    op.drop_column("ai_turns", "provider")
