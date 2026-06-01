"""Add consent_training to student_data_consent (4th consent dimension).

Master Paper Appendix A / gap audit G-AI3: the no-training consent dimension.
When False, the student's data must be excluded from any model-training corpus.

Revision ID: s3traincons01
Revises: r9s0t1u2v3w4
Create Date: 2026-06-01 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "s3traincons01"
down_revision: str | None = "r9s0t1u2v3w4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Idempotent (matches the e4a5b6c7d8e9 column-sync convention): on a fresh DB
# the sync migration may have already added the column from the model.
def upgrade() -> None:
    op.execute(
        "ALTER TABLE student_data_consent "
        "ADD COLUMN IF NOT EXISTS consent_training BOOLEAN NOT NULL DEFAULT TRUE"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE student_data_consent DROP COLUMN IF EXISTS consent_training")
