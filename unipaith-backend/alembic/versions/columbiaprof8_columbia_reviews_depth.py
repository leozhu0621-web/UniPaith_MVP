"""Columbia external_reviews depth pass — 37 coverable programs

Re-applies ``columbia_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 37 remaining coverable programs (46/46 total).
Completes the Columbia coverable review depth pass. Idempotent; no-op when absent.

Revision ID: columbiaprof8
Revises: dukeprof4
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof8"
down_revision = "dukeprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columbia_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
