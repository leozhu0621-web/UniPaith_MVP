"""Princeton profile repair — coverable external_reviews + research lab links

Adds aggregated external_reviews on 17 coverable programs (SPIA MPA/AB, CS flagship
and M.S.E., core engineering options, and key sciences/humanities majors), completes
institution research lab_links (Andlinger Center, Princeton Materials Institute), and
refreshes conformance stamps via ``princeton_profile.apply()``.

Revision ID: princetonprof3
Revises: berkeleyprof3
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof3"
down_revision = "berkeleyprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    princeton_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
