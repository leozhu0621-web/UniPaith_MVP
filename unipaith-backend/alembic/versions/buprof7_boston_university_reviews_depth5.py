"""Boston University external_reviews depth pass — final 35 coverable programs

Re-applies ``bu_profile.apply()`` after expanding ``_REVIEWS_BY_SLUG`` from 124 to
159 coverable programs (literary-translation BA/MFA pathways, anthropology
health-medicine, statistics-CS and math-CS combined degrees, GRS art-history and
sociology-social-work, remaining law JD/LLM and JD/MA duals, GMS biomedical-research
and MD/PhD pathways, SDM dental specialty DScD/MSD programs, SAR BS-to-MPH). Completes
the BU coverable review depth pass (154/154). Idempotent; no-op when BU absent.

Revision ID: buprof7
Revises: buprof6
Create Date: 2026-06-15
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof7"
down_revision = "buprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
