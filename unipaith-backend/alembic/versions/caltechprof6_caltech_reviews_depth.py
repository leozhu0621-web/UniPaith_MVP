"""Caltech external_reviews depth pass — 21 coverable programs

Re-applies ``caltech_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 21 remaining coverable programs (31/31 total).
Completes the Caltech coverable review depth pass. Idempotent; no-op when absent.

Revision ID: caltechprof6
Revises: ucsdprof3
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import caltech_profile

revision = "caltechprof6"
down_revision = "ucsdprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    caltech_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
