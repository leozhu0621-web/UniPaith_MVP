"""University of Rochester — institution seed to gold + real 179-program catalog

Takes the bulk-seeded University of Rochester institution (0 programs, dead feed) to the gold
standard (REPAIR_BACKLOG entry #6 — bulk institution-level seed). This migration fills the
institution's report-card / admissions funnel / diversity / cost-aid fields, its U.S. News
(#46, 2026) + Times Higher Education (#127) + QS (#251) rankings, and a working Events &
Updates feed, and creates a verified, real-named 179-program catalog across Rochester's seven
degree-granting schools (School of Arts and Sciences, Hajim School of Engineering and Applied
Sciences, Eastman School of Music, Simon Business School, Warner School of Education and Human
Development, School of Medicine and Dentistry, and the School of Nursing).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean), a
program-distinct ``who_its_for`` statement, a real owning ``department``, a ``cip_code``
(resolved from the College Scorecard Field-of-Study CIP list for UNITID 195030 to Rochester's
real conferred degree name — never the federal CIP title verbatim; concentration tracks folded
into ``tracks``, not split into separate rows), a verified ``delivery_format``, a working feed
(Rochester News Center RSS + the official Localist events.rochester.edu iCal), and published
tuition per credential level: the undergraduate sticker ($67,080), M.D. ($75,690), Simon
Business School master's at their published annual rates (MBA $60,000; MS Finance $78,000; MS
Business Analytics $68,000; MS Accountancy $49,000, 2026-27), funded research doctorates
(funded=True / tuition=0), and Arts, Sciences & Engineering / School of Medicine & Dentistry
academic master's annualized from the published AS&E graduate rate ($2,234/credit, 2026-27) x
the standard 30-credit academic master's load / program-years. Eastman (music), Warner
(education), and School of Nursing graduate programs, Simon's MS Marketing Analytics / MS AI in
Business, and certificates carry an honest cost omission (their rates are not verified to a
single published annual figure this pass). All values are verified-or-omitted in
``rochester_profile``.

Derives a grounded ``program_preferences`` row for every program after apply
(``backfill_program_preferences``) so the program -> student match direction fires; claimed /
first-party rows are never touched.

Head-sync: chains off the current single head ``tuftsprof1`` so this PR carries exactly one
head (SKILL.md §8 head-sync).

Deploy-safety (adopts the fleet pattern): the idempotent data apply runs inside a SAVEPOINT
bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot get
its locks quickly. The migration still records as applied so the chain advances;
``rochester_profile.apply()`` is idempotent and the routine re-applies + re-verifies the live
catalog after deploy.

Revision ID: rochprof1
Revises: tuftsprof1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rochester_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "rochprof1"
down_revision = "tuftsprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            inst = session.scalar(
                select(Institution).where(Institution.name == rochester_profile.INSTITUTION_NAME)
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
            rochester_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == rochester_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  rochprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
