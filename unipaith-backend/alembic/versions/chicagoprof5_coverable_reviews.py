"""UChicago external_reviews depth pass — coverable programs complete

Re-applies ``unipaith.data.chicago_profile.apply()`` after:
- dropping seven fabricated IPEDS catalog rows (Booth undergrad business,
  Crown B.S. social work, separate chemical/engineering-physics degrees that
  are tracks within Molecular Engineering);
- adding ``external_reviews`` for all remaining fleet-audit coverable programs;
- stamping molecular-engineering tracks and ``ENRICHED_AT`` at 2026-06-16.

Revision ID: chicagoprof5
Revises: mitprof4
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile

revision = "chicagoprof5"
down_revision = "mitprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    chicago_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
