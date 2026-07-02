"""Loyola Marymount University — institution seed to gold + real 101-program catalog

Clears REPAIR_BACKLOG entry #6 (bulk institution-level seeds) for Loyola Marymount University:
LMU entered as a bare US-News seed with 0 programs, 0 campus photos, a dead feed, and no
report-card / cost / description content. This migration takes the institution to gold (rankings,
College Scorecard report-card + admissions + diversity, endowment/enrollment/campus facts, a
verified Wikimedia Commons campus gallery, and the working LMU Newsroom RSS feed) and adds a real,
bulletin-verified 101-program catalog across LMU's seven colleges/schools: the Bellarmine College
of Liberal Arts, the Frank R. Seaver College of Science and Engineering, the College of Business
Administration, the College of Communication and Fine Arts, the School of Education, the School of
Film and Television, and LMU Loyola Law School.

Every program carries a researched, field-specific ``description_text`` (anti-stub clean), a
program-distinct ``who_its_for``, a real owning ``department``, a ``cip_code`` (IPEDS UNITID
117946), and a verified ``delivery_format``. LMU is private with a single published undergraduate
tuition sticker; its graduate, doctoral, and professional tiers are billed per-unit with no single
annual figure, so those record tuition omitted-with-reason (verify-or-omit). LMU confers a limited
set of doctorates (the professional Ed.D. and D.B.A. plus the J.D.) and NO research Ph.D.s, so none
are invented. All values are verified-or-omitted in ``lmu_profile``.

Re-derives ``program_preferences`` after apply so the program -> student match fires on the new
catalog (claimed/first-party rows are never touched).

Deploy-safety: the idempotent data apply runs inside a SAVEPOINT bounded by ``lock_timeout`` and is
SKIPPED (logged) rather than hanging container boot if it cannot get its locks quickly; the
migration still records as applied so the chain advances, and ``lmu_profile.apply()`` is idempotent.

Revision ID: lmuprof1
Revises: ucsbprof1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import lmu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "lmuprof1"
down_revision = "ucsbprof1"
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
        print(f"  lmuprof1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
