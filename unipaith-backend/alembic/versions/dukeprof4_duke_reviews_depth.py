"""Duke external_reviews depth pass — 42 coverable programs

Re-applies ``duke_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 42 remaining coverable programs (49/49 total).
Completes the Duke coverable review depth pass. Idempotent; no-op when absent.

Revision ID: dukeprof4
Revises: pennprof7
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile

revision = "dukeprof4"
down_revision = "pennprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    duke_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
