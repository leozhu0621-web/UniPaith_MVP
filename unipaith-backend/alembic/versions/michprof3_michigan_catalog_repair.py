"""Repair Michigan profile: catalogue descriptions for all 379 programs, real
college departments, anti-stub clean; remove synthesized external_reviews.

Revision ID: michprof3
Revises: uiucprof3
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile

revision = "michprof3"
down_revision = "uiucprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
