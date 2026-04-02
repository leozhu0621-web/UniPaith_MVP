"""Seed active heuristic model when none exists (cold-start ops / inference).

Revision ID: d4e8a2b1c901
Revises: c3a7f9e1d502
Create Date: 2026-04-02

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e8a2b1c901"
down_revision: str | None = "c3a7f9e1d502"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO model_registry (
            id,
            model_version,
            architecture,
            hyperparameters,
            performance_metrics,
            is_active,
            trained_at,
            promoted_at,
            created_at
        )
        SELECT
            gen_random_uuid(),
            'heuristic-default',
            'heuristic_ensemble',
            '{"ensemble": {"weights": [0.166666, 0.166666, 0.166666, 0.166666, 0.166666, 0.16667], "bias": 0.0, "calibration_a": -1.0, "calibration_b": 0.0}}'::jsonb,
            '{"source": "alembic_bootstrap", "note": "Cold-start default; replace via training promotion."}'::jsonb,
            true,
            NOW(),
            NOW(),
            NOW()
        WHERE NOT EXISTS (SELECT 1 FROM model_registry WHERE is_active = true)
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM model_registry
        WHERE model_version = 'heuristic-default'
        """
    )
