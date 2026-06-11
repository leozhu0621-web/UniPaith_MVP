"""Caltech profile repair — content_sources on every node + media_credit

Re-applies ``unipaith.data.caltech_profile.apply()`` so every division and program
carries keyword-filtered Caltech News RSS + campus-events feeds (not just the CS
flagship), plus institution media_credit and expanded research lab links.

Revision ID: caltechprof2
Revises: princetonprof2
Create Date: 2026-06-11
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import caltech_profile

revision = "caltechprof2"
down_revision = "princetonprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    caltech_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
