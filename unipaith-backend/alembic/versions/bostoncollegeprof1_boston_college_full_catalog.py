"""Boston College — institution seed to gold + real 103-program catalog

Takes the bulk-seeded Boston College institution (0 programs, dead feed) to the gold
standard (REPAIR_BACKLOG entry #6 — bulk institution-level seed). This migration fills the
institution's report-card / admissions-funnel (Class of 2029: 39,686 → 5,497 → 2,479) /
diversity / cost-aid / research / campus-life / U.S. News ranking / working feed fields and
creates a verified, real-named 103-program catalog across Boston College's eight schools
(Morrissey College of Arts and Sciences, Carroll School of Management, Lynch School of
Education and Human Development, Connell School of Nursing, School of Social Work, Law
School, Clough School of Theology and Ministry, and Woods College of Advancing Studies).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean), a
program-distinct ``who_its_for`` statement, a real owning ``department``, a ``cip_code``
(resolved from the College Scorecard Field-of-Study CIP list for UNITID 164924 to BC's real
conferred degree name — never the federal CIP title verbatim), a verified
``delivery_format``, a working Localist feed (events.bc.edu RSS + iCal), and published
2024-25 tuition per credential level: the undergraduate sticker ($70,702), the Law J.D.
($69,600), the full-time MBA ($65,080), funded research doctorates (funded=True /
tuition=0), and per-credit-billed graduate rows omitted-with-reason (BC bills graduate
tuition at $2,078/credit with no single published annual full-time figure). All values are
verified-or-omitted in ``boston_college_profile``.

Derives a grounded ``program_preferences`` row for every program after apply
(``backfill_program_preferences``) so the program → student match direction fires; claimed /
first-party rows are never touched.

Head-sync: chains off the current single head ``uwmadzoo1`` so this PR carries exactly one
head (SKILL.md §8 head-sync).

Deploy-safety (adopts the fleet pattern): the idempotent data apply runs inside a SAVEPOINT
bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot
get its locks quickly. The migration still records as applied so the chain advances;
``boston_college_profile.apply()`` is idempotent and the routine re-applies + re-verifies
the live catalog after deploy.

Revision ID: bostoncollegeprof1
Revises: uwmadzoo1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import boston_college_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "bostoncollegeprof1"
down_revision = "uwmadzoo1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            # Drop this institution's DERIVED program-preference rows FIRST so any seed
            # stubs lose their only dependent and ``apply()`` can delete them outright.
            # Claimed / first-party rows are NEVER touched.
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == boston_college_profile.INSTITUTION_NAME
                )
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
            boston_college_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == boston_college_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  bostoncollegeprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
