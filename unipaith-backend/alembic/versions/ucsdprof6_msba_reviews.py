"""UCSD external_reviews — Business Analytics minor + MSBA coverable programs

Re-applies ``ucsd_profile.apply()`` after merging MSBA and Business Analytics
minor reviews into ``DEPTH_REVIEWS`` (38/38 coverable programs reviewed).
Completes the UCSD fleet repair queue. Idempotent; no-op when absent.

Revision ID: ucsdprof6
Revises: gatechprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile

revision = "ucsdprof6"
down_revision = "gatechprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ucsd_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
