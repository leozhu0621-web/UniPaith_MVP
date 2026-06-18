"""remove Northwestern's machine-synthesized external_reviews batch

Re-applies ``northwestern_profile.apply()`` after northwesternprof7 de-fabrication:
the 48-row ``DEPTH_REVIEWS`` batch (reviews minted one-per-row from program metadata
+ institution rankings — a theme repeated 13–15x, a bare "U.S. News — Northwestern
University" source on 37 rows, several attached to CIP-rollup rows) is removed, so
those programs now persist ``external_reviews = NULL`` and record the gap in
``_standard.omitted``; only hand-gathered program-specific flagship reviews remain.
Also re-writes the last peer-copied field clause (Operations Research → real IEMS).
Idempotent (update-in-place); no-op when Northwestern is absent.

Revision ID: nwprof7
Revises: dukeprof6
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "nwprof7"
down_revision = "dukeprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    northwestern_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
