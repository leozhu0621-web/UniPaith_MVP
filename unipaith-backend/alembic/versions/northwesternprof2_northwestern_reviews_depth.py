"""Northwestern external_reviews depth pass — 48 coverable programs

Re-applies ``northwestern_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 48 remaining coverable programs (55/55 total).
Completes the Northwestern coverable review depth pass. Idempotent; no-op when absent.

Revision ID: northwesternprof2
Revises: harvardprof6
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "northwesternprof2"
down_revision = "harvardprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    northwestern_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
