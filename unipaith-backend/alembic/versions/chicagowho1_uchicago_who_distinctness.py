"""UChicago program-distinct who_its_for (REPAIR_BACKLOG #3b / SKILL.md miss #8)

A single depth repair on the University of Chicago's already-real 89-program catalog
(names, departments, field-specific descriptions, ``cip_code`` 100%, per-credential
tuition tiers, ``external_reviews`` on the coverable flagships, the 5-photo campus gallery,
and the live feeds were already gold; structure and every other dimension are untouched):

  ``who_its_for`` was TYPE-GAMED — only two of 89 programs carried a field-specific
  statement and the rest fell through to the degree-type baselines (one "Academically
  driven…" template on every bachelor's, one "Graduate and professional students seeking a
  top-ranked University of Chicago degree…" template on every master's/professional), so a
  CS Ph.D. and a Public-Policy M.A. read identically (distinct/total ≈ 0.10). This fills
  ``_WHO_BY_SLUG`` with a program-distinct 1–2 sentence statement for every one of the 89
  programs — subject, who it fits, typical next step — derived from each program's own
  published audience/fit material, so the baseline fallback is never reached and
  distinct/total = 1.0. No value is fabricated; each statement is grounded in the program's
  field and credential level.

Idempotent: re-applies ``chicago_profile.apply()`` (replace) and re-derives DERIVED program
preferences so ``pref_*`` reflect the catalog; claimed/first-party rows are never touched.

Revision ID: chicagowho1
Revises: gatechrev2
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "chicagowho1"
down_revision = "gatechrev2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    chicago_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == chicago_profile.INSTITUTION_NAME)
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
