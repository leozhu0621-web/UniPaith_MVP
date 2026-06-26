"""Boston University review follow-up — dental CIP join codes + SDM tuition scope.

Re-applies ``bu_profile.apply()`` after two correctness fixes from the #1206 review
(Codex P2), neither of which changes the cip/who coverage that #1206 shipped:

  * dental-specialty CIP codes — the eight Goldman SDM specialty programs were stamped
    with NCES 6-digit codes (51.0403 endodontics, 51.0405 orthodontics, …) that are NOT
    in the seeded ``ref_majors`` vocabulary, so the documented ``Program.cip_code`` ->
    ``ref_majors`` join (``ReferenceService.get_major``, exact match) returned None for
    them. Remapped to the seeded dental family ``51.04`` — matcher-equivalent (the matcher
    reads the 2-digit family) AND resolvable in ``ref_majors``.
  * SDM specialty tuition scope — the billed postdoctoral rate ($101,630) is now stamped
    ONLY on the SDM specialty MASTER'S tier (the REPAIR_BACKLOG #3 residual). SDM research
    doctorates (Oral Biology PhD, DSc) are funded and now correctly fall to the
    research-doctorate omit; SDM specialty certificates fall to the per-credit certificate
    omit — so a funded/per-credit row is never inflated with the billed specialty rate.

Re-derives unclaimed ProgramPreference rows and marks BU MatchResults stale so matches
rescore against the corrected cip codes. Direct apply (no lock-bounded skip).

Revision ID: bucipwho2
Revises: bucipwho1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "bucipwho2"
down_revision = "bucipwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
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
