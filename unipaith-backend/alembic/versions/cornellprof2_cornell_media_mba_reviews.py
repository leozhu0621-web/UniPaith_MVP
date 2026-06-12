"""Cornell profile repair — media_credit, MBA depth, coverable reviews

Re-applies ``unipaith.data.cornell_profile.apply()`` so the institution gains
verified campus-photo credit, the Johnson Two-Year MBA is deeply enriched
(outcomes, tracks, class profile, cost, admissions), and eight coverable
programs carry aggregated external_reviews.

Revision ID: cornellprof2
Revises: cmuprof2
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile

revision = "cornellprof2"
down_revision = "cmuprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    cornell_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
