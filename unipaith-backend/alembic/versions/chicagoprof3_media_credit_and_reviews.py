"""UChicago profile repair — description lead, media_credit, coverable reviews.

Re-applies ``unipaith.data.chicago_profile.apply()`` so the institution leads with
private-research-university character, carries verified campus-photo credit, and five
coverable programs (Booth MBA, undergraduate CS, J.D., M.D., Harris MPP) carry
aggregated external_reviews.

Revision ID: chicagoprof3
Revises: mitprof2
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile

revision = "chicagoprof3"
down_revision = "mitprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    chicago_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
