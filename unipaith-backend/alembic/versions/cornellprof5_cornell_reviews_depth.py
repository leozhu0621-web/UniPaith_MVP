"""Cornell external_reviews depth pass — 62 coverable programs

Re-applies ``cornell_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 62 remaining coverable programs (73/73 total).
Completes the Cornell coverable review depth pass. Idempotent; no-op when Cornell absent.

Revision ID: cornellprof5
Revises: cmuprof4
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile

revision = "cornellprof5"
down_revision = "cmuprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cornell_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
