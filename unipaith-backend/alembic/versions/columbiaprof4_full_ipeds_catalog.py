"""Columbia profile repair — full IPEDS/Scorecard program catalog

Re-applies ``unipaith.data.columbia_profile.apply()`` so the breadth-first
College Scorecard Field-of-Study catalog (UNITID 190150, ~260 CIP+credential rows)
merges with the curated explicit flagships — finishing the in-flight Columbia repair.

Revision ID: columbiaprof4
Revises: caltechprof3
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof4"
down_revision = "caltechprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    columbia_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
