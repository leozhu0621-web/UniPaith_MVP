"""spec15 application workspace fields

Revision ID: b2cc633aba88
Revises: a1f7c93d2e64
Create Date: 2026-05-31 12:32:15.433535

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2cc633aba88"  # pragma: allowlist secret
down_revision: str | None = "a1f7c93d2e64"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Spec 15 · Applications — per-application workspace fields."""
    op.add_column(
        "applications",
        sa.Column(
            "submission_mode",
            sa.String(length=20),
            server_default="internal",
            nullable=False,
        ),
    )
    op.add_column("applications", sa.Column("readiness_pct", sa.Integer(), nullable=True))
    op.add_column("applications", sa.Column("intent_picker", sa.String(length=30), nullable=True))
    op.add_column("applications", sa.Column("intent_rationale", sa.Text(), nullable=True))
    op.add_column("applications", sa.Column("fit_band", sa.String(length=10), nullable=True))
    op.add_column(
        "applications",
        sa.Column("guardrail_blockers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("applications", "guardrail_blockers")
    op.drop_column("applications", "fit_band")
    op.drop_column("applications", "intent_rationale")
    op.drop_column("applications", "intent_picker")
    op.drop_column("applications", "readiness_pct")
    op.drop_column("applications", "submission_mode")
