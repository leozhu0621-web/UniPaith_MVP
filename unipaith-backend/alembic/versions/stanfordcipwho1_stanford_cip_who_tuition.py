"""Stanford matcher-core cip_code + program-distinct who_its_for + professional tuition.

Re-applies ``stanford_profile.apply()`` after wiring three fields the base Stanford
catalog shipped wrong on the matcher / depth axes (REPAIR_BACKLOG #1 + #4b + #3,
SKILL miss #2 + miss #8):

  * ``cip_code`` — the CIP join key the CPEF matcher resolves to ``ref_majors`` + the
    field-66 vocabulary. The base catalog carried the IPEDS CIP per program (used for the
    breadth cross-check) but never stamped it onto ``Program.cip_code``; all 178 programs
    shipped null, scoring field-blind. This stamps the verified per-program CIP (the
    2-digit family resolves in ``field_canon``), exactly as the cip-complete fillers do.
  * ``who_its_for`` — a universal depth field, now program-DISTINCT (distinct/total = 1.0):
    every program carries a field-specific 1-2 sentence audience statement grounded in its
    real field + credential level, replacing the single shared ``_WHO_BASELINE`` string
    (which had collapsed who_its_for to one template per degree type, REPAIR_BACKLOG #4b).
  * professional-tier ``tuition`` — the J.D. and M.D. programs shipped tuition null; both
    publish a rate, so this stamps the verified 2025-26 published professional tuition
    (J.D. $76,608; M.D. $92,884). Funded PhDs (tuition 0) and per-unit graduate
    certificates stay honestly omitted in ``_standard.omitted``.

Because the populated ``cip_code`` changes the program-side field signal (it was null
before), the unclaimed ``source="derived"`` ProgramPreference rows are re-derived and any
cached MatchResult rows for Stanford programs are marked stale so GET /me/matches rescores
against the corrected data. Direct apply (no lock-bounded skip); verify-live on content.

Revision ID: stanfordcipwho1
Revises: jhucipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "stanfordcipwho1"
down_revision = "jhucipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == stanford_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        prog_ids = session.scalars(
            select(Program.id).where(
                Program.institution_id == inst.id,
                Program.is_claimed.is_(False),
            )
        ).all()
        if prog_ids:
            session.execute(
                delete(ProgramPreference).where(
                    ProgramPreference.program_id.in_(prog_ids),
                    ProgramPreference.source == "derived",
                )
            )
            session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
        if prog_ids:
            session.execute(
                MatchResult.__table__.update()
                .where(MatchResult.program_id.in_(prog_ids))
                .values(is_stale=True)
            )
    session.flush()


def downgrade() -> None:
    pass
