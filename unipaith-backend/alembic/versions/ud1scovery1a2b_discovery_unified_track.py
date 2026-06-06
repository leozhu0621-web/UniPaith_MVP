"""Widen discovery_sessions.track CHECK to allow the unified 'discovery' track.

The Uni redesign runs one track-less conversation backed by a single session
with track='discovery'. Additive: only widens the CHECK; existing rows + the
profile/goals/needs paths are unaffected.

Revision ID: ud1scovery1a2b
Revises: p65embed1a2b3
Create Date: 2026-06-06
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "ud1scovery1a2b"  # pragma: allowlist secret
down_revision = "p65embed1a2b3"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_NAME = "ck_discovery_sessions_track"
_TABLE = "discovery_sessions"


def upgrade() -> None:
    op.drop_constraint(_NAME, _TABLE, type_="check")
    op.create_check_constraint(_NAME, _TABLE, "track IN ('profile','goals','needs','discovery')")


def downgrade() -> None:
    op.drop_constraint(_NAME, _TABLE, type_="check")
    op.create_check_constraint(_NAME, _TABLE, "track IN ('profile','goals','needs')")
