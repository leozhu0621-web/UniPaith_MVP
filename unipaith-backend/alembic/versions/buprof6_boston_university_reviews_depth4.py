"""Boston University external_reviews depth pass — 30 more coverable programs

Re-applies ``bu_profile.apply()`` after expanding ``_REVIEWS_BY_SLUG`` from 94 to
124 coverable programs (engineering materials/systems PhD, GRS economics MA/PhD and
energy-environment MBA dual, CAS combined economics/math and physics/CS degrees, MET
accelerated CS, remaining SPH MPH concentrations and MSW/MPH duals, SSW macro/PhD
and dual degrees, law accelerated/two-year LLM and JD/MA programs, GMS biomedical
forensic/mental-health/virology, SDM dental public health). Idempotent; no-op when
BU absent.

Revision ID: buprof6
Revises: buprof5
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof6"
down_revision = "buprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
