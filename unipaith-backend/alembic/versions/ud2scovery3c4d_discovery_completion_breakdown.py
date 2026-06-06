"""Add discovery_sessions.completion_breakdown for per-track handoff gating.

The unified track='discovery' session stores completion_pct as the mean of the
basic/goals/needs validators. That single value can't express a per-track gap,
so the handoff gate could read match-ready while goals/needs are still weak.
This adds a nullable JSONB column holding the per-track split. Additive only;
existing rows stay NULL and fall back to the average.

Revision ID: ud2scovery3c4d
Revises: ud1scovery1a2b
Create Date: 2026-06-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "ud2scovery3c4d"  # pragma: allowlist secret
down_revision = "ud1scovery1a2b"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_TABLE = "discovery_sessions"
_COLUMN = "completion_breakdown"


def upgrade() -> None:
    op.add_column(_TABLE, sa.Column(_COLUMN, JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column(_TABLE, _COLUMN)
