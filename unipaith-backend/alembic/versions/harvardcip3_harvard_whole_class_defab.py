"""Harvard whole-class CIP-title NAME clear + HBS de-fabrication (REPAIR_BACKLOG #1, run 78)

Builds on ``harvardcip2`` (#1095), which dropped only the "Physiology, Pathology
and Related Sciences" certificate. The miss-#2 whole-class rule requires the entire
federal-CIP-title NAME class at ZERO, so this pass clears the rest:

  * Resolved to Harvard's real, web-verified degree (un-conferrable levels dropped):
    "Teacher Education and Professional Development, Specific Levels and Methods" ->
    Teaching and Teacher Leadership (HGSE Ed.M.); "Biochemistry, Biophysics and
    Molecular Biology" -> Chemical and Physical Biology (Harvard College
    concentration, BA only); "Health Professions Education, Ethics, and Humanities"
    -> Bioethics (HMS Center for Bioethics M.S.).
  * Dropped (federal IPEDS mints Harvard does not confer; real degrees already ship
    as flagships): the fabricated HBS cluster (undergraduate business degrees,
    concentration MBAs, certificates) + further federal CIP titles (Intelligence/
    Command Control, Radio-TV, Public Relations, Bilingual Education, Educational
    Administration/Assessment, Legal Research, Research Psychology, Natural Resources
    Conservation, Teacher Education "Specific Subject Areas").
  * Flagship professional-degree names un-doubled ("Master of Arts in Juris Doctor
    (J.D.)" -> "Juris Doctor (J.D.)"; LL.M. / S.J.D. / Ed.L.D. likewise).

Catalog: 271 -> 228 rows (the GSD Master in Real Estate is preserved). Dropped slugs are reconciled out of prod by
``harvard_profile._apply_programs`` (slug no longer canonical -> delete-if-unreferenced
/ unpublish). Re-applies ``harvard_profile.apply()`` and re-derives the matcher's
target-applicant rows.

Revision ID: harvardcip3
Revises: cornellnames2
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardcip3"
down_revision = "cornellnames2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    harvard_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == harvard_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        # Renamed/re-described surviving rows (Bioethics, Chemical and Physical
        # Biology, Teaching and Teacher Leadership, the GSD MRE) keep their slug, so
        # ``backfill_program_preferences`` (insert-missing / fill-empty only) would
        # leave a DERIVED target-applicant still computed from the old CIP-title name.
        # Delete the non-claimed (derived) rows first so the backfill re-derives them
        # from the new names/descriptions; first-party (claimed) rows are untouched.
        prog_ids = select(Program.id).where(Program.institution_id == inst.id).scalar_subquery()
        session.execute(
            delete(ProgramPreference).where(
                ProgramPreference.program_id.in_(prog_ids),
                ProgramPreference.source != "claimed",
            )
        )
        session.flush()
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
