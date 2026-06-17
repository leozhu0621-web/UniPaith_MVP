"""Repair USC profile: content_sources, program names, descriptions, reviews.

- Adds verified USC Today RSS (today.usc.edu/feed/) + university calendar iCal to
  institution/school/program content_sources so Events & Updates populate.
- Disambiguates 613 program names (Bachelor of Arts in Physics vs bare "Physics").
- Replaces classification-stub descriptions with field-specific clauses + credential
  suffixes; adds external_reviews for all 227 coverable programs.
- Idempotent via ``unipaith.data.usc_profile.apply()``.

Revision ID: uscprof2
Revises: buprof10
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile

revision = "uscprof2"
down_revision = "buprof10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    usc_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
