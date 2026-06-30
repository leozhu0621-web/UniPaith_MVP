"""UCSD program-distinct who_its_for backfill.

Re-applies ``ucsd_profile.apply()`` after adding universal ``who_its_for`` coverage for
the live UCSD catalog. The catalog already had real program names, non-empty descriptions,
content sources, reviews where sourced, and full CIP coverage; the live acute gap was that
all 136 published programs had null ``who_its_for``. The new statements are generated from
each program's real credential name, field, and verified description, and are checked at
import time for 136/136 coverage and distinctness.

Because ``who_its_for`` feeds program rationale and derived preferences, delete only
unclaimed ``source='derived'`` ProgramPreference rows before re-deriving, then mark cached
match results stale for UCSD programs.

Revision ID: ucsdwho1
Revises: pubtuitscalar1
Create Date: 2026-06-29
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ucsdwho1"
down_revision = "pubtuitscalar1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucsd_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucsd_profile.INSTITUTION_NAME)
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
