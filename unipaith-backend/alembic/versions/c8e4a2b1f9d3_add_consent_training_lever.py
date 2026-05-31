"""Add consent_training lever to student_data_consent (Spec 46 §2 / 08 §16).

The Universal Profile Data tab surfaces the 4 consent levers from Master
Paper Appendix A: {matching, outreach, analytics, training}. The DB already
has matching/outreach + `consent_research` (the analytics lever). This adds
the 4th — `training` — governing inclusion in any future UniPaith
fine-tuning corpus. Opt-in (server default false). No inference-time agent
gates on it, so the column is behaviour-neutral for existing accounts.

Revision ID: c8e4a2b1f9d3
Revises: b7d3f1a9c2e4
Create Date: 2026-05-30 23:55:00.000000

"""

import sqlalchemy as sa

from alembic import op

revision = "c8e4a2b1f9d3"  # pragma: allowlist secret
down_revision = "b7d3f1a9c2e4"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_data_consent",
        sa.Column(
            "consent_training",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("student_data_consent", "consent_training")
