"""NYU matcher-core cip_code + program-distinct who_its_for.

Re-applies ``nyu_profile.apply()`` after wiring two matcher fields the base NYU catalog
shipped wrong (REPAIR_BACKLOG #1 + #4a, SKILL miss #2 + miss #8):

  * ``cip_code`` — the CIP join key the CPEF matcher resolves to ``ref_majors`` + the
    field-66 vocabulary. All 502 programs shipped null, scoring field-blind. This stamps
    the verified NCES CIP family per program from ``nyu_cip_who`` — no code invented.
  * ``who_its_for`` — a universal depth field, now program-DISTINCT (distinct/total ≈
    1.0): every program carries a field-specific audience statement grounded in its real
    field + credential level, replacing the prior hard-null in apply() (#4a).

Because the populated ``cip_code`` / ``who_its_for`` change the program-side match signal,
the unclaimed ``source="derived"`` ProgramPreference rows are re-derived and any cached
MatchResult rows for NYU programs are marked stale so GET /me/matches rescores against
the corrected data. Direct apply (no lock-bounded skip).

Revision ID: nyucipwho1
Revises: harvardcipwho1
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

revision = "nyucipwho1"
down_revision = "harvardcipwho1"
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
                Program.claimed.is_(False),
            )
        ).all()
        if unclaimed_ids:
            session.execute(
                delete(ProgramPreference).where(ProgramPreference.program_id.in_(unclaimed_ids))
            )
            backfill_program_preferences(session, institution_id=inst.id)
        if all_prog_ids:
            session.execute(
                delete(MatchResult).where(MatchResult.program_id.in_(all_prog_ids))
            )
    session.flush()


def downgrade() -> None:
    pass
