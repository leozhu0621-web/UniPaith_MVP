"""Penn external_reviews depth pass — 46 coverable programs

Re-applies ``penn_profile.apply()`` after merging ``DEPTH_REVIEWS``
into ``_REVIEWS_BY_SLUG`` for all 46 remaining coverable programs (58/58 total).
Completes the Penn coverable review depth pass. Idempotent; no-op when absent.

Revision ID: pennprof7
Revises: uwmadisonprof3
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof7"
down_revision = "uwmadisonprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    penn_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
