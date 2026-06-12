"""Cornell profile repair — coverable external_reviews on 13 programs

Adds aggregated external_reviews on economics, Dyson AEM, ECE M.Eng., and
mechanical engineering (alongside the existing nine coverable programs), and
refreshes conformance stamps via ``cornell_profile.apply()``.

Revision ID: cornellprof3
Revises: stanfordprof3
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile

revision = "cornellprof3"
down_revision = "stanfordprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    cornell_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
