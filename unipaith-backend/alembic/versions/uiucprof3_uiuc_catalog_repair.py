"""Repair UIUC profile: catalogue descriptions for all 419 programs, real
college departments, anti-stub clean; remove synthesized external_reviews.

Revision ID: uiucprof3
Revises: nwuscmrg1
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile

revision = "uiucprof3"
down_revision = "nwuscmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uiuc_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
