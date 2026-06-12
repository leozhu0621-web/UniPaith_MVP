"""Caltech profile repair — full IPEDS/Scorecard program catalog

Re-applies ``unipaith.data.caltech_profile.apply()`` so the breadth-first
College Scorecard Field-of-Study catalog (UNITID 110404, ~74 CIP+credential rows)
merges with the curated explicit options — finishing the in-flight Caltech repair.

Revision ID: caltechprof3
Revises: caltechprof2
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import caltech_profile

revision = "caltechprof3"
down_revision = "caltechprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    caltech_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
