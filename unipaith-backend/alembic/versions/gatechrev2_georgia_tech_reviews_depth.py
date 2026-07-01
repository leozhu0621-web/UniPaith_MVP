"""Georgia Tech external_reviews depth pass (REPAIR_BACKLOG #5 / SKILL.md miss #8)

A single depth repair on Georgia Tech's already-real 143-program catalog (names, departments,
descriptions, ``cip_code``, per-credential tuition tiers, ``who_its_for``, photos, and feeds
were already gold; structure and every other dimension are untouched):

  ``external_reviews`` (coverage-gated depth pass, run-65 rule; unblocked now that structure is
  clean fleet-wide, structure-before-depth). The four original hand-gathered flagship reviews
  (OMSCS, Online MS Analytics, Scheller Full-Time MBA, undergraduate Computer Science) are
  joined by 13 more program-specific reviews across the coverable flagship set — BS/MS
  Industrial Engineering, BS/MS Aerospace Engineering, BS Biomedical Engineering, MS Mechanical
  Engineering, MS Electrical & Computer Engineering, MS Quantitative & Computational Finance,
  the residential MS in Analytics, the Executive MBA in Management of Technology, MS
  Human-Computer Interaction, the Online MS in Cybersecurity, and MS Supply Chain Engineering.
  Each was hand-gathered from real program-specific third-party coverage (U.S. News specialty
  ranks, official employment reports, QuantNet, Financial Times, Poets&Quants, OMSCentral course
  reviews, College Factual, College Confidential), pairs praise with the common cautions, and
  carries resolvable program-specific sources — never synthesized from metadata (miss #8). The
  reviewed slugs drop from each program's ``_standard.omitted`` automatically. Programs with no
  verifiable program-specific coverage (residential MSCS/MS-Cybersecurity, MCRP, MS Public
  Policy, research MS/PhD tail) stay honestly omitted.

Idempotent: re-applies ``georgia_tech_profile.apply()`` (replace) and re-derives DERIVED program
preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched.

Revision ID: gatechrev2
Revises: ufwhodistinct1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gatechrev2"
down_revision = "ufwhodistinct1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    georgia_tech_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == georgia_tech_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        prog_ids = session.scalars(
            select(Program.id).where(Program.institution_id == inst.id)
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
    session.flush()


def downgrade() -> None:
    pass
