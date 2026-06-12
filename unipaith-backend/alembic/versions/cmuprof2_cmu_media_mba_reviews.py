"""Carnegie Mellon profile repair — media_credit, MBA depth, coverable reviews

Re-applies ``unipaith.data.carnegie_mellon_profile.apply()`` so the institution
gains verified campus-photo credit, the Tepper Full-Time MBA is deeply enriched
(outcomes, tracks, class profile, cost, admissions), and eight coverable programs
carry aggregated external_reviews.

Revision ID: cmuprof2
Revises: stanfordprof2
Create Date: 2026-06-12
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile

revision = "cmuprof2"
down_revision = "stanfordprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    carnegie_mellon_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
