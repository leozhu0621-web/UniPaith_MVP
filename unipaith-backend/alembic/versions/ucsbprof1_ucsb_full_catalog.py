"""UC Santa Barbara — institution seed to gold + real 142-program catalog

Takes the bulk-seeded University of California, Santa Barbara institution (0 programs, dead
feed) to the gold standard (REPAIR_BACKLOG entry #6 — bulk institution-level seed). This
migration fills the institution's report-card / admissions funnel / diversity / cost-aid
fields (College Scorecard UNITID 110705 + UC Admissions fall-2025 first-year funnel), its
U.S. News (#41 national, #14 public, 2026) + QS (#179, 2026) rankings, Carnegie R1 + WSCUC
accreditation, a verified 5-photo Wikimedia Commons campus gallery (author + license confirmed
via the Commons API), and a working Events & Updates feed (UCSB news RSS + UCSB Campus Calendar
iCal, both verified live), and creates a verified, real-named 142-program catalog across UCSB's
five degree-granting colleges/schools (College of Letters and Science; Robert Mehrabian College
of Engineering; College of Creative Studies; Bren School of Environmental Science and
Management; Gevirtz Graduate School of Education).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean:
verbatim-shared / shared-leading-body / frame-stripped / template-slot / scrape-debris /
machine-artifact all 0), a program-distinct ``who_its_for`` statement (142/142 distinct), a
real owning ``department``, a ``cip_code`` (resolved from the College Scorecard Field-of-Study
CIP list for UNITID 110705 to UCSB's real conferred degree name — never the federal CIP title
verbatim; e.g. CIP 26.07 "Zoology/Animal Biology" -> "Zoology", CIP 16.01 -> "Linguistics"), a
verified ``delivery_format``, a working feed, and — because UCSB is a public university — a
matcher ``tuition`` scalar set to the NON-RESIDENT rate (undergraduate $50,614; academic-
graduate $30,246) with the cost breakdown carrying BOTH resident and non-resident rates.
Research doctorates are funded (funded=True / tuition=0). The self-supporting / professional-fee
master's (Technology Management M.T.M.; Bren M.E.S.M. and M.E.D.S.) carry an honest cost
omission (billed on a program-specific schedule with no single annual figure on the academic
basis). All values are verified-or-omitted in ``ucsb_profile``.

Derives a grounded ``program_preferences`` row for every program after apply
(``backfill_program_preferences``) so the program -> student match direction fires; claimed /
first-party rows are never touched.

Head-sync: chains off the current single head ``rochprof1`` so this PR carries exactly one head
(SKILL.md §8 head-sync).

Deploy-safety (adopts the fleet pattern): the idempotent data apply runs inside a SAVEPOINT
bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot get
its locks quickly. The migration still records as applied so the chain advances;
``ucsb_profile.apply()`` is idempotent and the routine re-applies + re-verifies the live catalog
after deploy.

Revision ID: ucsbprof1
Revises: rochprof1
Create Date: 2026-07-02
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsb_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ucsbprof1"
down_revision = "rochprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            inst = session.scalar(
                select(Institution).where(Institution.name == ucsb_profile.INSTITUTION_NAME)
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
            ucsb_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == ucsb_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  ucsbprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
