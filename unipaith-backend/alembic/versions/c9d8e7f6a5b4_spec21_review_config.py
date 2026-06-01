"""Spec 21 — institution review_config JSONB for blind review + calibration toggles.

Revision ID: c9d8e7f6a5b4
Revises: d1e2f3a4b5c6
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c9d8e7f6a5b4"  # pragma: allowlist secret
down_revision = "d1e2f3a4b5c6"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "institutions",
        sa.Column("review_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("institutions", "review_config")
