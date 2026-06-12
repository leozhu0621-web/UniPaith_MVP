"""Harvard profile repair — full IPEDS catalog, media_credit, coverable reviews.

Re-applies ``unipaith.data.harvard_profile.apply()`` so the institution gains verified
campus-photo credit, the description leads with private-research-university character,
research lab links and campus-life resources, the program catalog expands to the full
College Scorecard Field-of-Study set (~290 rows), and eight coverable programs carry
aggregated external_reviews.

Revision ID: harvardprof4
Revises: riceprof2
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof4"
down_revision = "riceprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    harvard_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
