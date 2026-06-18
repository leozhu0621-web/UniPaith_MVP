"""Repair UW profile: catalogue descriptions for all 365 programs, real
college departments, anti-stub clean; remove synthesized external_reviews.

Revision ID: uwprof2
Revises: seed300b3
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile

revision = "uwprof2"
down_revision = "seed300b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
