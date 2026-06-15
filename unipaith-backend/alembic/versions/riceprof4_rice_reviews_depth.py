"""Rice external_reviews depth pass — 51 coverable programs

Re-applies ``rice_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 51 remaining coverable programs (57/57 total).
Completes the Rice coverable review depth pass. Idempotent; no-op when Rice absent.

Revision ID: riceprof4
Revises: yaleprof5
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile

revision = "riceprof4"
down_revision = "yaleprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    rice_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
