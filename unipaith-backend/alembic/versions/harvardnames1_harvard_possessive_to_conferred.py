"""Harvard possessive-mint names → conferred degree designations (REPAIR BACKLOG #2)

Resolves Harvard's ~53% possessive-mint program names ("Bachelor's in {field}" /
"Master's in {field}") to the institution's conferred designations — Bachelor of
Arts/Science, Master of Arts/Science, Doctor of Philosophy, Graduate Certificate —
the gold-MIT naming form (SKILL miss #2 / REPAIR_BACKLOG run 64). Drops residual
federal rollup buckets (Area Studies, Foods/Accounting and Related Services) and
breadth rows that duplicate explicit flagships (MBA, M.P.H.). Re-applies
``harvard_profile.apply()`` and re-derives target-applicant rows for the matcher.

Revision ID: harvardnames1
Revises: dukecolmerge1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardnames1"
down_revision = "dukecolmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    harvard_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == harvard_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
