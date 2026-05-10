"""Phase A — split match_score into fitness_score + confidence_score.

Per spec, Match (Stage 2) surfaces TWO numbers: Fitness (match strength) and
Confidence (calibration — how sure we are given profile completeness). One
score collapses both signals and confuses users; we ship two with a tooltip
explaining the relationship.

Migration is additive only: new columns are added nullable, backfilled from
the legacy `match_score`, then altered to NOT NULL. The original
`match_score` column STAYS — it gets dropped in Phase E only after dual
scores have been live for at least one release. This preserves a rollback
path without data loss.

Backfill rule:
  fitness_score        = match_score                   (preserve existing)
  confidence_score     = 0.5                           (neutral baseline)
  fitness_breakdown    = COALESCE(score_breakdown,{})
  confidence_breakdown = {"reason":"legacy_backfill"}

Revision ID: bd5c6e3f2a1b
Revises: ac4b8e2f1d3c
Create Date: 2026-05-09 17:30:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "bd5c6e3f2a1b"  # pragma: allowlist secret
down_revision = "ac4b8e2f1d3c"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1 — add new columns nullable.
    op.add_column(
        "match_results",
        sa.Column("fitness_score", sa.Numeric(5, 4), nullable=True),
    )
    op.add_column(
        "match_results",
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=True),
    )
    op.add_column(
        "match_results",
        sa.Column("fitness_breakdown", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "match_results",
        sa.Column("confidence_breakdown", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "match_results",
        sa.Column("rationale_text", sa.Text, nullable=True),
    )
    op.add_column(
        "match_results",
        sa.Column(
            "rationale_generated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "match_results",
        sa.Column(
            "strategy_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_strategies.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_match_results_strategy_version",
        "match_results",
        ["strategy_version_id"],
    )

    # Step 2 — backfill from legacy match_score for any existing rows.
    op.execute(
        """
        UPDATE match_results
        SET fitness_score = COALESCE(match_score, 0),
            confidence_score = 0.5,
            fitness_breakdown = COALESCE(score_breakdown, '{}'::jsonb),
            confidence_breakdown = '{"reason": "legacy_backfill", "value": 0.5}'::jsonb
        """
    )

    # Step 3 — alter score columns to NOT NULL. Breakdown columns stay
    # nullable (caller may not have one yet).
    op.alter_column("match_results", "fitness_score", nullable=False)
    op.alter_column("match_results", "confidence_score", nullable=False)

    # Step 4 — CHECK constraints to keep both scores in [0,1].
    op.create_check_constraint(
        "ck_match_results_fitness_score_range",
        "match_results",
        "fitness_score >= 0 AND fitness_score <= 1",
    )
    op.create_check_constraint(
        "ck_match_results_confidence_score_range",
        "match_results",
        "confidence_score >= 0 AND confidence_score <= 1",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_match_results_confidence_score_range",
        "match_results",
        type_="check",
    )
    op.drop_constraint(
        "ck_match_results_fitness_score_range",
        "match_results",
        type_="check",
    )
    op.drop_index("ix_match_results_strategy_version", table_name="match_results")
    op.drop_column("match_results", "strategy_version_id")
    op.drop_column("match_results", "rationale_generated_at")
    op.drop_column("match_results", "rationale_text")
    op.drop_column("match_results", "confidence_breakdown")
    op.drop_column("match_results", "fitness_breakdown")
    op.drop_column("match_results", "confidence_score")
    op.drop_column("match_results", "fitness_score")
