"""UW-Madison external_reviews depth pass — 47 coverable programs

Re-applies ``uw_madison_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 47 remaining coverable programs (57/57 total).
Completes the UW-Madison coverable review depth pass. Idempotent; no-op when absent.

Revision ID: uwmadisonprof3
Revises: northwesternprof2
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile

revision = "uwmadisonprof3"
down_revision = "northwesternprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    uw_madison_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
