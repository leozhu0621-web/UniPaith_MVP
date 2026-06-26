"""Boston University matcher-core cip_code + program-distinct who_its_for + dental tuition.

Re-applies ``bu_profile.apply()`` after wiring three fields the base BU catalog shipped
wrong on the matcher / depth axes (REPAIR_BACKLOG #1 + #4a + #3, SKILL miss #8):

  * ``cip_code`` — the CIP join key the CPEF matcher resolves to ``ref_majors`` + the
    field-66 vocabulary. The base catalog never stamped it; all 402 programs shipped null,
    scoring field-blind. This stamps the verified NCES CIP family per program from
    ``bu_cip_who`` (``field_canon`` reads the 2-digit family), exactly as the cip-complete
    fillers do — no code invented.
  * ``who_its_for`` — a universal depth field, now program-DISTINCT (distinct/total ≈ 1.0):
    every program carries a field-specific 1-2 sentence audience statement grounded in its
    real field + credential level (``bu_cip_who.WHO_BY_FIELD`` + ``LEVEL_TAIL`` + a real
    name-derived distinguisher), replacing the prior catalog-wide null (#4a).
  * dental tuition — the seven Goldman SDM advanced-education specialty master's rows (plus
    their certificate / clinical-doctorate siblings) shipped a null matcher tuition behind a
    "no single annual figure" omit; BU in fact publishes ONE uniform postdoctoral rate
    ($101,630, 2025-26, BUMC OSFS), so it is stamped as the program's real published rate
    (REPAIR_BACKLOG #3). The fully-funded MD/PhD and research-PhD rows remain honest
    omit-with-reason.

Because the populated ``cip_code`` / ``who_its_for`` / ``tuition`` change the program-side
match signal, the unclaimed ``source="derived"`` ProgramPreference rows are re-derived and
any cached MatchResult rows for BU programs are marked stale so GET /me/matches rescores
against the corrected data. Direct apply (no lock-bounded skip).

Revision ID: bucipwho1
Revises: cornellcipwho1
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

revision = "bucipwho1"
down_revision = "cornellcipwho1"
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
            # Bump feature_version so the rationale cache (keyed on program_version) and the
            # lazy embedding rebuild (embedding_version != feature_version) both invalidate
            # against the corrected cip_code / who_its_for / tuition, then mark every cached
            # MatchResult stale so GET /me/matches rescores against fresh data.
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
