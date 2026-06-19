"""Columbia real-catalog de-fabrication — drop fabricated certificates + Harvard contamination.

Follow-up to the concurrently-merged columbiadefab1 (#867), which conferred real names and
real departments but LEFT two defects this re-application fixes:
  * 2 descriptions still imported PEER-institution units — Harvard's Nieman Foundation,
    Carpenter Center, and Visual & Environmental Studies program (a no-fabrication
    violation, SKILL.md miss #8) — removed
  * 74 IPEDS×award-level "Graduate Certificate in {field}" rows (Columbia's academic
    departments do not award per-field graduate certificates; the federal list reports
    embedded sub-award completions) dropped, matching the certified UCSD/Chicago model
Re-applies ``columbia_profile.apply()`` over the now-real 167-program catalog (conferred
names, real owning departments incl. the added Graduate School of Arts and Sciences and
College of Dental Medicine, per-credential field-specific descriptions) and re-derives
``program_preferences`` for every program (skips claimed rows). Idempotent.

Revision ID: columbiadefab2
Revises: colyalemerge1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "columbiadefab2"
down_revision = "colyalemerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    columbia_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == columbia_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
