"""Johns Hopkins external_reviews depth pass — 34 coverable programs

Re-applies ``jhu_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 34 remaining coverable programs (43/43 total).
Completes the JHU coverable review depth pass. Idempotent; no-op when absent.

Revision ID: jhuprof3
Revises: columbiaprof8
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile

revision = "jhuprof3"
down_revision = "columbiaprof8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    jhu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
