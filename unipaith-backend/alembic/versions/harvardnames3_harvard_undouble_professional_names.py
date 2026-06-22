"""Harvard: un-double the remaining professional-degree flagship names (run-78 follow-up)

Live verification of #1096 surfaced 12 flagship professional degrees whose
``program_name`` was DOUBLED by the generic ``_conferred_program_name`` (it prepends
"Master of Arts in …" to a name that is already the conferred designation), e.g.
"Master of Arts in Master of Architecture (M.Arch)", "Master of Science in Doctor of
Medicine (M.D.)". #1096 cleared only the law/education subset; this clears the WHOLE
doubling class (re-scanned live → 0 remaining):

  harvard-md, harvard-dmd, harvard-mph, harvard-mpp, harvard-mpa, harvard-march,
  harvard-mla, harvard-mup, harvard-mdes, harvard-mdiv, harvard-mts, harvard-alm

Each slug is pinned in ``harvard_profile._FULL_NAME_BY_SLUG`` to its real conferred
designation (Doctor of Medicine (M.D.), Master of Architecture (M.Arch), Master of
Public Health (M.P.H.), …). Idempotent: re-applies ``harvard_profile.apply()`` (no
catalog/structure change — only the persisted ``program_name`` of these flagships).

Revision ID: harvardnames3
Revises: yalegradtuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardnames3"
down_revision = "yalegradtuition1"
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
        # Renamed flagships keep their slug, so backfill (insert-missing / fill-empty
        # only) would leave a DERIVED target-applicant computed from the old doubled
        # name. Delete the non-claimed rows first so they re-derive from the new names;
        # first-party (claimed) rows are untouched (same pattern as harvardcip3).
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
