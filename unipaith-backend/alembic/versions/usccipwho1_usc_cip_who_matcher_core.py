"""USC matcher-core cip_code + program-distinct who_its_for.

Re-applies ``usc_profile.apply()`` after wiring two matcher fields the base USC catalog
shipped wrong (REPAIR_BACKLOG #1 + #4a):

  * ``cip_code`` — the CIP join key the CPEF matcher resolves to ``ref_majors`` + the
    field-66 vocabulary. All 511 programs shipped null, scoring field-blind. This stamps
    the verified NCES CIP family per program from ``usc_cip_who`` — no code invented.
  * ``who_its_for`` — a universal depth field, now program-DISTINCT (distinct/total ≈
    1.0): every program carries a field-specific audience statement grounded in its real
    field + credential level, replacing the prior hard-null in apply() (#4a).

Because the populated ``cip_code`` / ``who_its_for`` change the program-side match signal,
the unclaimed ``source="derived"`` ProgramPreference rows are re-derived and any cached
MatchResult rows for USC programs are marked stale so GET /me/matches rescores against
the corrected data.

Revision ID: usccipwho1
Revises: nyucipwho2
Create Date: 2026-06-28
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "usccipwho1"
down_revision = "nyucipwho2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    usc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == usc_profile.INSTITUTION_NAME)
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
