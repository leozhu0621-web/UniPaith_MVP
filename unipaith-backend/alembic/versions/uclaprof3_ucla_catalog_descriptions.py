"""Repair UCLA profile: catalogue descriptions for all 373 programs, real
college departments, anti-stub clean; remove synthesized external_reviews.

Revision ID: uclaprof3
Revises: utaprof2
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile

revision = "uclaprof3"
down_revision = "utaprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
