"""Boston University external_reviews depth pass — 34 coverable programs

Re-applies ``bu_profile.apply()`` after expanding ``_REVIEWS_BY_SLUG`` from 14 to
34 flagship coverable programs (Questrom MSBA/MS Finance/MSMFT, CDS MSDS, MET
online CS/analytics, engineering, CAS sciences/economics, COM journalism MS,
SHA MS, SSW online, SPH MBA/MPH, MD/MBA). Idempotent; no-op when BU is absent.

Revision ID: buprof3
Revises: stanfordprof5
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof3"
down_revision = "stanfordprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
