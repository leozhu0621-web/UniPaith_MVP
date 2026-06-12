"""Stanford profile repair — full IPEDS/Scorecard program catalog

Re-applies ``unipaith.data.stanford_profile.apply()`` so the breadth-first
College Scorecard Field-of-Study catalog (UNITID 243744, ~179 CIP+credential rows)
merges with the curated explicit options, and content_sources populate on every
school and program node.

Revision ID: stanfordprof2
Revises: columbiaprof4
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof2"
down_revision = "columbiaprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
