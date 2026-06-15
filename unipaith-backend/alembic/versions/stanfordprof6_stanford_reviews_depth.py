"""Stanford external_reviews depth pass — 28 coverable programs

Re-applies ``stanford_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 28 remaining coverable programs (38/38 total).
Completes the Stanford coverable review depth pass. Idempotent; no-op when absent.

Revision ID: stanfordprof6
Revises: jhuprof3
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof6"
down_revision = "jhuprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    stanford_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
