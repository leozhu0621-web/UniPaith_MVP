"""Georgia Tech external_reviews depth pass — 58 coverable programs

Re-applies ``georgia_tech_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 58 remaining coverable programs (62/62 total).
Completes the Georgia Tech coverable review depth pass. Idempotent; no-op when absent.

Revision ID: gatechprof2
Revises: aiclaim01
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile

revision = "gatechprof2"
down_revision = "aiclaim01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    georgia_tech_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
