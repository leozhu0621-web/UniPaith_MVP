"""Harvard external_reviews depth pass — 49 coverable programs

Re-applies ``harvard_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 49 remaining coverable programs (60/60 total).
Completes the Harvard coverable review depth pass. Idempotent; no-op when Harvard absent.

Revision ID: harvardprof6
Revises: riceprof4
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof6"
down_revision = "riceprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    harvard_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
