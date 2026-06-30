"""Purdue PhD published tuition backfill.

Clears the remaining Purdue graduate-tier matcher defect after the public-university
nonresident scalar repair: Ph.D. rows still carried ``tuition = 0`` even though Purdue
publishes resident and nonresident graduate tuition. Funding can be represented separately,
but the matcher budget scalar must not be a zero placeholder. Re-apply the Purdue profile
so Ph.D. rows carry the published nonresident graduate scalar while ``cost_data.breakdown``
preserves both resident and nonresident rates.

Revision ID: purduephd1
Revises: ucsdwho1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "purduephd1"
down_revision = "ucsdwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    purdue_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == purdue_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        all_prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        unclaimed_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if unclaimed_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(unclaimed_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
        if all_prog_ids:
            session.execute(
                Program.__table__.update()
                .where(Program.id.in_(all_prog_ids))
                .values(feature_version=Program.feature_version + 1)
            )
            session.execute(
                MatchResult.__table__.update()
                .where(MatchResult.program_id.in_(all_prog_ids))
                .values(is_stale=True)
            )
    session.flush()


def downgrade() -> None:
    pass
