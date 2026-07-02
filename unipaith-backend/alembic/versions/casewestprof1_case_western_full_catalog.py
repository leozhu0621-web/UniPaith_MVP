"""Case Western Reserve University — institution seed to gold + real 206-program catalog

Clears REPAIR_BACKLOG entry #6 (bulk institution-level seeds) for Case Western Reserve:
CWRU entered as a bare US-News seed with 0 programs, a dead feed, and a junk student-body
size, though its 5 verified Wikimedia Commons campus photos were already seeded. This
migration takes the institution to gold (rankings, College Scorecard report-card +
admissions funnel + diversity, scale/campus facts, research centers, the working CWRU
Newsroom RSS + University Events iCal feeds) and adds a real, bulletin-verified 206-program
catalog across CWRU's eight degree-granting schools: the College of Arts and Sciences, the
Case School of Engineering, the Weatherhead School of Management, the School of Medicine
(including the Cleveland Clinic Lerner College of Medicine), the Frances Payne Bolton School
of Nursing, the School of Dental Medicine, the School of Law, and the Jack, Joseph and Morton
Mandel School of Applied Social Sciences.

Every program carries a researched, field-specific ``description_text`` (anti-stub clean, all
metrics 0), a program-distinct ``who_its_for`` (206/206), a real owning ``department``, a
``cip_code`` (IPEDS UNITID 201645), and a verified ``delivery_format``. Bachelor's carry CWRU's
published undergraduate sticker ($68,660); research PhDs are funded (0); academic master's carry
the School of Graduate Studies full-time annual rate; named-school/professional programs carry
their own published per-credit or annual rates (MD, DMD, JD, MSW, MBA, MSN, DNP, LL.M., …), with
the Cleveland Clinic Lerner MD tuition-free. Postdoctoral M.S.D. dental specialties, the PA
program (fees-blended figure only), Weatherhead MBAI/MSLOC, and the specialized non-J.D./LL.M.
School of Law master's record tuition omitted-with-reason (verify-or-omit). Six flagship
programs (J.D., MBA, M.S.W., M.D., M.S.N., B.S.E. Biomedical Engineering) carry gathered→cited
``external_reviews`` (≥2 independent domains, cautions included); the rest omit-with-reason
(coverage-gated). QS/THE world ranks, a single university-wide placement rate, and per-school
leadership/faculty are omitted-with-reason. All values are verified-or-omitted in
``case_western_profile``.

Re-derives ``program_preferences`` after apply so the program -> student match fires on the new
catalog (claimed/first-party rows are never touched).

Deploy-safety: the idempotent data apply runs inside a SAVEPOINT bounded by ``lock_timeout`` and
is SKIPPED (logged) rather than hanging container boot if it cannot get its locks quickly; the
migration still records as applied so the chain advances, and ``case_western_profile.apply()`` is
idempotent.

Revision ID: casewestprof1
Revises: lmuprof1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import case_western_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "casewestprof1"
down_revision = "lmuprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            inst = session.scalar(
                select(Institution).where(Institution.name == case_western_profile.INSTITUTION_NAME)
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
            case_western_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == case_western_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(f"  casewestprof1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
