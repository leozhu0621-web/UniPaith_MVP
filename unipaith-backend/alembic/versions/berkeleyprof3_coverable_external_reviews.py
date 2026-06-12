"""Berkeley profile repair — coverable external_reviews depth pass

Adds aggregated, cited external_reviews on twelve coverable Berkeley programs
(EECS, CS, data science, economics, ME, chemE, Haas undergrad, MBA, JD, MPP,
MPH, MArch) via ``berkeley_profile.apply()``.

Revision ID: berkeleyprof3
Revises: columbiaprof5
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile

revision = "berkeleyprof3"
down_revision = "columbiaprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    berkeley_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
