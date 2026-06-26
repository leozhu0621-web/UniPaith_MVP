"""Cornell matcher-core cip_code + program-distinct who_its_for + real professional names.

Re-applies ``cornell_profile.apply()`` after wiring three fields the base Cornell catalog
shipped wrong on the matcher / depth / name axes (REPAIR_BACKLOG #1 + #4b + #5a, SKILL
miss #2 + miss #8):

  * ``cip_code`` — the CIP join key the CPEF matcher resolves to ``ref_majors`` + the
    field-66 vocabulary. The base catalog carried the verified IPEDS CIP per program (used
    for the breadth cross-check) but never stamped it onto ``Program.cip_code``; all 221
    programs shipped null, scoring field-blind. This stamps the verified per-program CIP
    (``field_canon`` reads the 2-digit family), exactly as the cip-complete fillers do.
  * ``who_its_for`` — a universal depth field, now program-DISTINCT (distinct/total ≈ 1.0):
    every program carries a field-specific 1-2 sentence audience statement grounded in its
    real field + credential level, replacing the two shared ``_WHO_BASELINE`` /
    ``_WHO_GRAD_BASELINE`` templates (which had collapsed who_its_for to one string per
    degree type, REPAIR_BACKLOG #4b).
  * professional NAMES — two breadth professional rows shipped the generic "{DegreeType}
    program in {field}" placeholder (REPAIR_BACKLOG #5a). "Professional program in
    Veterinary Medicine" was a duplicate of the curated D.V.M. flagship (de-duped away);
    "Professional program in Music" is resolved to Cornell's verified conferred designation,
    "Doctor of Musical Arts (D.M.A.)" (the Field of Music's professional doctorate).

Because the populated ``cip_code`` changes the program-side field signal (it was null
before), the unclaimed ``source="derived"`` ProgramPreference rows are re-derived and any
cached MatchResult rows for Cornell programs are marked stale so GET /me/matches rescores
against the corrected data. Direct apply (no lock-bounded skip); verify-live on content.

Revision ID: cornellcipwho1
Revises: stanfordmrg1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellcipwho1"
down_revision = "stanfordmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    cornell_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == cornell_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # apply() rewrote matcher-/rationale-feeding fields (cip_code, who_its_for) and
        # dropped one redundant professional row, so invalidation spans the whole catalog.
        all_prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
        ).all()
        # Preference re-derivation must NOT touch first-party (claimed) rows.
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
            # Bump feature_version so the rationale cache (keyed on program_version) and
            # the lazy embedding rebuild (embedding_version != feature_version) both
            # invalidate against the corrected cip_code / who_its_for. Then mark every
            # cached MatchResult stale so GET /me/matches rescore against fresh data.
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
