"""Georgetown external_reviews depth pass — verified third-party coverage on coverable programs.

Adds ``external_reviews`` (MBAn shape: summary + themes + resolvable sources + disclaimer)
to fourteen additional Georgetown programs that carry genuine, program-specific third-party
coverage, taking the catalog from 6 to 20 reviewed programs. Every review is gathered and
paraphrased from public third-party sources that were fetched and verified first-hand — no
synthesized, institution-level, or fabricated reviews:

* Georgetown Law LL.M.s scored against U.S. News specialty rankings (via TaxProf Blog):
  Taxation (#2), International Legal Studies (#3-tie), Environmental & Energy (#14-tie),
  National & Global Health Law (#8).
* McDonough: Flex/part-time MBA (U.S. News #11 + Poets & Quants), M.S. Finance (QS #11 U.S.),
  M.S. Management (QS #4 U.S.), and the undergraduate international-business concentration
  (Poets & Quants top-10 + U.S. News #2 international business).
* Walsh SFS: M.A. Security Studies (SSP) and M.A. Latin American Studies (MALAS 98% employment),
  plus the BSFS International Politics major (Foreign Policy #1 undergraduate IR, 2024).
* Health/tech: BSN (Nursing Schools Almanac #31, 97% NCLEX), M.S. Nursing (GradReports 4.3),
  and M.S. Computer Science (TechGuide #15, 2025).

Every other program keeps ``external_reviews.summary`` in its ``_standard.omitted`` with a
reason — reviews are coverage-gated and honestly omitted where no program-specific third-party
coverage exists. Re-applies ``georgetown_profile.apply()`` (idempotent, ``replace``-style) and
re-derives ``program_preferences`` so the program -> student match reads the updated data.
Idempotent and safe on a fresh/CI database (no-op if Georgetown is absent).

Revision ID: gtownreviews1
Revises: caltechwho1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgetown_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gtownreviews1"
down_revision = "caltechwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    georgetown_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == georgetown_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
