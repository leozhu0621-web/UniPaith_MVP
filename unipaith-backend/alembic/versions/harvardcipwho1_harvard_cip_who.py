"""Harvard matcher-core cip_code + program-distinct who_its_for.

Re-applies ``harvard_profile.apply()`` after wiring two matcher fields the base Harvard
catalog shipped wrong (REPAIR_BACKLOG #1 + #4b, SKILL miss #2 + miss #8):

  * ``cip_code`` — the CIP join key the CPEF matcher resolves to ``ref_majors`` + the
    field-66 vocabulary. The base catalog carried the verified IPEDS CIP on its breadth
    rows but never stamped it onto ``Program.cip_code``; all 228 programs shipped null,
    scoring field-blind. This stamps the verified per-program CIP — the spec's own CIP
    for IPEDS breadth rows, ``harvard_cip_who.CIP_BY_SLUG`` for the curated
    professional/flagship rows, and the IPEDS field→CIP map for flagship academic rows
    (``field_canon`` reads the 2-digit family, so no code is invented).
  * ``who_its_for`` — a universal depth field, now program-DISTINCT (distinct/total ≈
    0.99): every program carries a field-specific 1-2 sentence audience statement
    grounded in its real field + credential level, replacing the single ``_WHO_BY_TYPE``
    template per degree type (which had collapsed who_its_for to ~one string per degree
    type, distinct/total ≈ 0.13, REPAIR_BACKLOG #4b).

Because the populated ``cip_code`` changes the program-side field signal (it was null
before), the unclaimed ``source="derived"`` ProgramPreference rows are re-derived and any
cached MatchResult rows for Harvard programs are marked stale so GET /me/matches rescores
against the corrected data. Direct apply (no lock-bounded skip); verify-live on content.

Revision ID: harvardcipwho1
Revises: bucipwho2
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.models.matching import MatchResult
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardcipwho1"
down_revision = "bucipwho2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    harvard_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == harvard_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        # apply() rewrote matcher-/rationale-feeding fields (cip_code, who_its_for), so
        # invalidation spans the whole catalog.
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
