"""Yale external_reviews depth pass — 54 coverable programs

Re-applies ``yale_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 54 remaining coverable programs (60/60 total).
Completes the Yale coverable review depth pass. Idempotent; no-op when Yale absent.

Revision ID: yaleprof5
Revises: purdueprof3
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile

revision = "yaleprof5"
down_revision = "purdueprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    yale_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
