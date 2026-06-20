"""Cornell possessive-mint names → conferred degree designations (REPAIR BACKLOG #7)

Resolves Cornell's ~54% possessive-mint program names ("Bachelor's in {field}" /
"Master's in {field}") to the institution's conferred designations — Bachelor of
Arts/Science, Master of Arts/Science, Doctor of Philosophy — the gold-MIT naming
form (SKILL miss #2 / REPAIR_BACKLOG run 64). Drops residual federal rollup buckets
(Culinary Arts, HR PhD at Johnson) and resolves ORIE / Human Development /
Nutritional Sciences rollups to real Cornell degree names. Re-applies
``cornell_profile.apply()`` and re-derives target-applicant rows for the matcher.

Revision ID: cornellnames1
Revises: harvcoldukem1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellnames1"
down_revision = "harvcoldukem1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    cornell_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == cornell_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
