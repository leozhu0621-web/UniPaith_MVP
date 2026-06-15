"""Berkeley external_reviews depth pass — 59 coverable programs

Re-applies ``berkeley_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 59 remaining coverable programs (70/70 total).
Completes the Berkeley coverable review depth pass. Idempotent; no-op when Berkeley absent.

Revision ID: berkeleyprof6
Revises: cornellprof5
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile

revision = "berkeleyprof6"
down_revision = "cornellprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    berkeley_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
