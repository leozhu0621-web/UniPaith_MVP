"""Harvard published graduate-tier tuition — clear master's 17% (REPAIR_BACKLOG #2)

Stamps each Harvard school's published 2025-26 annual master's tuition on the
88 null master's rows (Griffin GSAS / OIRA Fact Book + school financial-aid
pages). HMS master's (program-specific COA) and Extension A.L.M. stay omitted-
with-reason. Re-applies ``harvard_profile.apply()`` and re-derives matcher
ProgramPreference rows.

Revision ID: harvardgradtuition1
Revises: penncipnames1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardgradtuition1"
down_revision = "penncipnames1"
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
