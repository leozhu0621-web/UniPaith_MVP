"""Notre Dame external_reviews depth pass (REPAIR_BACKLOG #5 / SKILL.md miss #8)

A single depth repair on Notre Dame's already-real 113-program catalog (conferred names, real
owning departments, per-credential field-specific descriptions, ``cip_code``, per-tier tuition,
program-distinct ``who_its_for``, a 5-photo verified gallery, and feeds were already gold;
structure and every other dimension are untouched):

  ``external_reviews`` (coverage-gated depth pass, run-65 rule; unblocked because structure is
  clean fleet-wide, structure-before-depth). The three original hand-gathered flagship reviews
  (Mendoza MBA, MS Business Analytics, the Law School J.D.) are joined by twelve more
  program-specific reviews across the coverable flagship set — the Mendoza MS in Accountancy and
  MS in Finance, the undergraduate Accountancy and Finance majors, the School of Architecture
  B.Arch and M.Arch, the Keough Master of Global Affairs, the Philosophy and Theology Ph.D.s,
  ESTEEM, the Program of Liberal Studies, and the Kroc Institute Peace Studies Ph.D. Each was
  hand-gathered from real program-specific third-party or official coverage (Poets&Quants and
  Poets&Quants-for-Undergrads, U.S. News, the QS World University Rankings, the Philosophical
  Gourmet Report, and official Mendoza/Keough/Kroc employment and outcomes reports), pairs praise
  with the common cautions, and carries resolvable program-specific sources — never synthesized
  from metadata (miss #8). The reviewed slugs drop from each program's ``_standard.omitted``
  automatically. Programs with no verifiable program-specific coverage (niche language M.A.s and
  the research M.S./Ph.D. tail) stay honestly omitted.

Idempotent: re-applies ``notre_dame_profile.apply()`` (replace) and re-derives DERIVED program
preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched.

Revision ID: ndreviews1
Revises: chicagowho1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import notre_dame_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ndreviews1"
down_revision = "chicagowho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    notre_dame_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == notre_dame_profile.INSTITUTION_NAME)
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
