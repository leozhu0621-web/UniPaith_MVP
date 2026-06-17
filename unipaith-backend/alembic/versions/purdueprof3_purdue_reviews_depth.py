"""Purdue external_reviews depth pass — 56 coverable programs

Re-applies ``purdue_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 56 remaining coverable programs (64/64 total).
Completes the Purdue coverable review depth pass. Idempotent; no-op when Purdue absent.

Revision ID: purdueprof3
Revises: berkeleyprof6
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile

revision = "purdueprof3"
down_revision = "berkeleyprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    purdue_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
