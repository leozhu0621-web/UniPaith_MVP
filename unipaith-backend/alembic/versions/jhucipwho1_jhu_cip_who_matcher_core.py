"""Johns Hopkins matcher-core cip_code + universal who_its_for.

Re-applies ``jhu_profile.apply()`` after wiring two matcher-core / depth fields that the
base JHU catalog shipped null on all 244 programs (REPAIR_BACKLOG #1 + #4a, SKILL miss #2 +
miss #8):

  * ``cip_code`` — the CIP join key the CPEF matcher resolves to ``ref_majors`` + the
    field-66 vocabulary. The base catalog already carried the College Scorecard 4-digit CIP
    per program; this upgrades each to its verified NCES CIP-2020 6-digit code (every code
    present in ``data/reference/ref_majors.jsonl``; the 2-digit field family is preserved,
    so the matcher signal is unchanged, with one documented exception — Data Science maps to
    its dedicated ``30.7001`` and is name-aliased in ``field_canon``, so its field signal is
    preserved).
  * ``who_its_for`` — a universal depth field, program-DISTINCT (distinct/total = 1.0): a
    field-specific lead + a credential-appropriate tail, so a field's credential siblings
    (BA / MS / certificate / PhD) read differently.

Because the populated ``cip_code`` changes the program-side field signal (it was null
before), the unclaimed ``source="derived"`` ProgramPreference rows are re-derived and any
cached MatchResult rows for JHU programs are marked stale so GET /me/matches rescores
against the corrected data. Direct apply (no lock-bounded skip); verify-live on content.

Revision ID: jhucipwho1
Revises: cmucip2
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "jhucipwho1"
down_revision = "cmucip2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    jhu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == jhu_profile.INSTITUTION_NAME)
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
