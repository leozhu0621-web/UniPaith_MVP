"""Widen discovery_sessions.track CHECK to allow the unified 'discovery' track.

The Uni redesign runs one track-less conversation backed by a single session
with track='discovery'. Additive: only widens the CHECK; existing rows + the
profile/goals/needs paths are unaffected.

Revision ID: ud1scovery1a2b
Revises: mitprof1a2b3c
Create Date: 2026-06-06

Re-pointed onto the concurrently-merged `mitprof1a2b3c` (MIT profile enrichment)
to keep a single Alembic head — it had forked off the same `p65embed1a2b3` base.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "ud1scovery1a2b"  # pragma: allowlist secret
down_revision = "mitprof1a2b3c"  # pragma: allowlist secret
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
