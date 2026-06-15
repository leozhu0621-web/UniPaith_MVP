"""UCSD external_reviews depth pass — 28 coverable programs

Re-applies ``ucsd_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 28 remaining coverable programs (36/36 total).
Completes the UCSD coverable review depth pass. Idempotent; no-op when absent.

Revision ID: ucsdprof3
Revises: stanfordprof6
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile

revision = "ucsdprof3"
down_revision = "stanfordprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ucsd_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
