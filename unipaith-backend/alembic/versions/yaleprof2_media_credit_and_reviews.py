"""Yale profile repair — description lead, media_credit, coverable reviews.

Re-applies ``unipaith.data.yale_profile.apply()`` so the institution leads with
private-research-university character, carries verified campus-photo credit,
and eight coverable programs carry aggregated external_reviews.

Revision ID: yaleprof2
Revises: harvardprof4
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile

revision = "yaleprof2"
down_revision = "harvardprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    yale_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    pass
