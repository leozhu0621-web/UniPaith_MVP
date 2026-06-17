"""MIT external_reviews depth pass — 16 coverable programs

Re-applies ``mit_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 16 remaining coverable programs (23/23 total).
Completes the MIT coverable review depth pass. Idempotent; no-op when absent.

Revision ID: mitprof4
Revises: caltechprof6
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitprof4"
down_revision = "caltechprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    mit_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
