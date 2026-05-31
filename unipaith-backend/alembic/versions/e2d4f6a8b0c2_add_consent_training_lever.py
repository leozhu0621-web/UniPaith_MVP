"""add consent_training lever + consent_change_log to student_data_consent

Spec 10 §22.7 / 43 §2 / gap G-AI3 — the Data Rights tab exposes four consent
levers (matching, outreach, analytics/research, training). The first three
already exist; this adds ``consent_training`` (opt-in, defaults FALSE) plus a
``consent_change_log`` JSONB so each toggle can surface "Last changed" + a
change-history link.

Idempotent (ADD COLUMN IF NOT EXISTS) so it is safe whether or not the live
schema already has the columns.

Revises: p3q5r7s9t1u3
"""

from __future__ import annotations

from alembic import op

# revision identifiers
revision = "e2d4f6a8b0c2"  # pragma: allowlist secret
down_revision = "p3q5r7s9t1u3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE student_data_consent "
        "ADD COLUMN IF NOT EXISTS consent_training BOOLEAN NOT NULL DEFAULT FALSE"
    )
    op.execute("ALTER TABLE student_data_consent ADD COLUMN IF NOT EXISTS consent_change_log JSONB")


def downgrade() -> None:
    op.execute("ALTER TABLE student_data_consent DROP COLUMN IF EXISTS consent_change_log")
    op.execute("ALTER TABLE student_data_consent DROP COLUMN IF EXISTS consent_training")
