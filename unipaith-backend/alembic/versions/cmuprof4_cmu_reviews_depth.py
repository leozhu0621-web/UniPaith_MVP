"""Carnegie Mellon external_reviews depth pass — 66 coverable programs

Re-applies ``carnegie_mellon_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 66 remaining coverable programs (71/71 total).
Completes the CMU coverable review depth pass. Idempotent; no-op when CMU absent.

Revision ID: cmuprof4
Revises: buprof7
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmuprof4"
down_revision = "buprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    carnegie_mellon_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
