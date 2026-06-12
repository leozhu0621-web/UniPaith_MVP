"""Duke profile repair — media_credit, Fuqua MBA depth, coverable reviews

Re-applies ``unipaith.data.duke_profile.apply()`` so the institution gains
verified campus-photo credit, the Fuqua Daytime MBA is deeply enriched
(outcomes, tracks, class profile, cost, admissions), and eight coverable
programs carry aggregated external_reviews.

Revision ID: dukeprof2
Revises: cornellprof2
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile

revision = "dukeprof2"
down_revision = "cornellprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    duke_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
