"""NYU cip/who re-apply after nyucipwho1 migration bug fix.

The initial ``nyucipwho1`` migration referenced ``Program.claimed`` (nonexistent) after
``nyu_profile.apply()``, which raised ``AttributeError`` and caused the deploy entrypoint's
alembic retry/stamp recovery to mark ``nyucipwho1`` applied WITHOUT running the data write.
This re-applies ``nyu_profile.apply()`` with the corrected preference backfill (``is_claimed``)
so all 502 NYU programs receive ``cip_code`` + ``who_its_for`` live.

Revision ID: nyucipwho2
Revises: nyucipwho1
Create Date: 2026-06-28
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyucipwho2"
down_revision = "nyucipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    nyu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == nyu_profile.INSTITUTION_NAME)
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
                delete(MatchResult).where(MatchResult.program_id.in_(all_prog_ids))
            )
    session.flush()


def downgrade() -> None:
    pass
