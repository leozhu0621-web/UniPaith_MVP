"""Boston University external_reviews depth pass — 30 more coverable programs

Re-applies ``bu_profile.apply()`` after expanding ``_REVIEWS_BY_SLUG`` from 34 to
64 flagship coverable programs (engineering MS/MEng/PhD, GRS CS/MA economics, CDS
PhD, law JD/MBA/JD/MPH and specialty LLMs, MD/JD, SPH MPH concentrations, Questrom
PhD, MET MSCIS/economics, MS/MBA product design). Idempotent; no-op when BU absent.

Revision ID: buprof4
Revises: buprof3
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof4"
down_revision = "buprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
