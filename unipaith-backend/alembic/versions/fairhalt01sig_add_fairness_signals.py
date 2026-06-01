"""Add fairness_signals + programs.matching_halted/fairness_threshold_override.

Gap audit G-I5 / G-D4 (Spec 43 §6): per-program disparate-impact tracking and
the matching auto-halt flag.

Revision ID: fairhalt01sig
Revises: s3traincons01
Create Date: 2026-06-01 00:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "fairhalt01sig"
down_revision: str | None = "s3traincons01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Idempotent (matches the e4a5b6c7d8e9 / d3f4a5b6c7d8 sync convention): on a
# fresh DB the metadata-sync migrations may already have created the table and
# columns from the model.
def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fairness_signals (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
            protected_attribute VARCHAR(40) NOT NULL,
            week_start DATE NOT NULL,
            reference_group VARCHAR(120),
            disadvantaged_group VARCHAR(120),
            reference_rate DOUBLE PRECISION,
            disadvantaged_rate DOUBLE PRECISION,
            disparate_impact_ratio DOUBLE PRECISION,
            disparate_impact_delta DOUBLE PRECISION,
            sample_size INTEGER NOT NULL DEFAULT 0,
            breached BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_fairness_program_attr_week
                UNIQUE (program_id, protected_attribute, week_start)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_fairness_program_week "
        "ON fairness_signals (program_id, week_start)"
    )
    op.execute(
        "ALTER TABLE programs ADD COLUMN IF NOT EXISTS "
        "matching_halted BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE programs ADD COLUMN IF NOT EXISTS "
        "fairness_threshold_override DOUBLE PRECISION"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE programs DROP COLUMN IF EXISTS fairness_threshold_override")
    op.execute("ALTER TABLE programs DROP COLUMN IF EXISTS matching_halted")
    op.execute("DROP TABLE IF EXISTS fairness_signals")
