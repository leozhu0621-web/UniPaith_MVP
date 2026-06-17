"""Boston University external_reviews depth pass — 30 more coverable programs

Re-applies ``bu_profile.apply()`` after expanding ``_REVIEWS_BY_SLUG`` from 64 to
94 coverable programs (MEng materials/systems, CAS BA/MS CS and economics, MET CS
specializations, Questrom BSBA-to-MSBA/MSDT/mathematical-finance PhD, GRS MA/MBA
economics and IR, SPH MD/MPH and nine MPH concentrations, law LLM/tax programs,
SHA hospitality communication, BUSM MD/PhD, CAS BA-to-MPH). Idempotent; no-op when
BU absent.

Revision ID: buprof5
Revises: buprof4
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof5"
down_revision = "buprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
