"""Loyola Marymount University — fill matcher-core graduate tuition + expand campus gallery

Repairs REPAIR_BACKLOG entry #1 (matcher-core master's/professional-tier tuition residual) for
Loyola Marymount University. LMU shipped from #1276 with its entire graduate tree tuition-null —
all 39 master's, the J.D., and the two paid professional doctorates (D.B.A., Ed.D.) — so the CPEF
matcher scored every LMU graduate program's budget-fit BLIND (a whole master's/professional tier at
0% is matcher starvation, not an honest omission; master's/professional programs publish a per-unit
rate and are rarely funded — SKILL §"Measure tuition coverage PER CREDENTIAL LEVEL").

This re-applies ``lmu_profile`` with each graduate program now carrying its DISTINCT LMU-published
full-time annual tuition (per-unit rate × the program's standard annual unit load), read off the LMU
Graduate Cost of Attendance schedule and the Loyola Law School Tuition & Fees / Cost of Attendance
schedule (2026-27): Bellarmine $20,664 · Seaver $21,768 · Business $22,824 · Education $21,864 ·
Entertainment Leadership $45,648 · Film/TV & MFT $43,536 · MFA Writing / Performance Pedagogy
$32,652 · D.B.A. $58,569 · Ed.D. $27,240 · J.D. & LL.M. $73,000 · Tax LL.M. / M.L.S. $38,400 — none
equal to the $62,357 undergraduate sticker (no copy-down). Also adds a third verified Wikimedia
Commons campus photo (the historic LMU Sunken Garden, CC BY 2.0).

Re-derives ``program_preferences`` after apply so the program -> student match keeps firing
(claimed/first-party rows are never touched).

Deploy-safety: the idempotent data apply runs inside a SAVEPOINT bounded by ``lock_timeout`` and is
SKIPPED (logged) rather than hanging container boot if it cannot get its locks quickly; the
migration still records as applied so the chain advances, and ``lmu_profile.apply()`` is idempotent.

Revision ID: lmutuition1
Revises: casewestprof1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import lmu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "lmutuition1"
down_revision = "casewestprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            inst = session.scalar(
                select(Institution).where(Institution.name == lmu_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                seed_ids = session.scalars(
                    select(Program.id).where(Program.institution_id == inst.id)
                ).all()
                if seed_ids:
                    session.execute(
                        delete(ProgramPreference).where(
                            ProgramPreference.program_id.in_(seed_ids),
                            ProgramPreference.source == "derived",
                        )
                    )
            lmu_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == lmu_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(f"  lmutuition1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
