"""UC Davis external_reviews depth pass (REPAIR_BACKLOG #5 / SKILL.md miss #8).

A single depth repair on UC Davis's already-real 151-program catalog (conferred names, real
owning departments/colleges, per-credential field-specific descriptions, ``cip_code``,
per-tier non-resident tuition, program-distinct ``who_its_for``, a verified campus-photo
gallery, and working feeds were already gold; structure and every other dimension are
untouched):

  ``external_reviews`` (coverage-gated depth pass, run-65 rule; unblocked because structure is
  clean fleet-wide, structure-before-depth). The four original hand-gathered flagship reviews
  (the D.V.M., the Graduate School of Management M.B.A., the School of Law J.D., and the School
  of Medicine M.D.) are joined by twelve more program-specific reviews across the coverable
  flagship set — the M.S. and B.S. in Viticulture and Enology, the Ecology Ph.D., the
  Agricultural and Resource Economics Ph.D., the Entomology Ph.D., the Plant Biology Ph.D., the
  Animal Science and Food Science B.S. majors, the GSM M.S. in Business Analytics, the M.P.H.,
  the M.F.A. in Creative Writing, and the School of Law LL.M. Each was hand-gathered from real
  program-specific third-party or official coverage (UC Davis's QS and U.S. News Best Global
  Universities subject rankings, QS business-master's rankings, and the official
  department/school pages), pairs praise with the common cautions, and carries resolvable
  program-specific sources — never synthesized from metadata (miss #8). The reviewed slugs drop
  from each program's ``_standard.omitted`` automatically. Programs with no verifiable
  program-specific coverage stay honestly omitted.

Idempotent: re-applies ``ucdavis_profile.apply()`` (replace) and re-derives DERIVED program
preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched.

Revision ID: ucdreviews1
Revises: ndreviews1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucdavis_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ucdreviews1"
down_revision = "ndreviews1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    ucdavis_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucdavis_profile.INSTITUTION_NAME)
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
