"""MIT profile repair — description lead, media_credit, coverable reviews.

Re-applies ``unipaith.data.mit_profile.apply()`` so the gold reference institution
leads with private-research-university character, carries verified campus-photo
credit, and eight coverable programs carry aggregated external_reviews.

Revision ID: mitprof2
Revises: yaleprof2
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitprof2"
down_revision = "yaleprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
