"""Tufts University — institution seed to gold + real 136-program catalog

Takes the bulk-seeded Tufts University institution (0 programs, dead feed) to the gold
standard (REPAIR_BACKLOG entry #6 — bulk institution-level seed). This migration fills the
institution's report-card / admissions-funnel (Class of 2028: 34,400 -> 3,957 -> 1,800) /
diversity / cost-aid / research / campus-life / U.S. News (#36) + QS (#334) ranking /
working feed fields, and creates a verified, real-named 136-program catalog across Tufts'
eight schools (School of Arts and Sciences, School of Engineering, The Fletcher School of
Law and Diplomacy, Friedman School of Nutrition Science and Policy, School of Medicine,
School of Dental Medicine, Cummings School of Veterinary Medicine, and SMFA at Tufts).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean), a
program-distinct ``who_its_for`` statement, a real owning ``department``, a ``cip_code``
(resolved from the College Scorecard Field-of-Study CIP list for UNITID 168148 to Tufts'
real conferred degree name — never the federal CIP title verbatim; concentration tracks
folded into ``tracks``, not split into separate rows), a verified ``delivery_format``, a
working feed (Tufts Now RSS + the official Trumba events.tufts.edu iCal), and published
2025-26 tuition per credential level: the undergraduate sticker ($70,704), M.D. ($74,118),
D.M.D. ($104,601), D.V.M. ($68,908), The Fletcher School master's ($61,450, 2026-27), funded
AS&E/GSAS research doctorates (funded=True / tuition=0), and AS&E / Engineering master's
annualized from the published $1,799/credit graduate rate x degree credits / program-years.
Programs billed at a school-specific rate not verified this pass (Friedman, School of
Medicine public-health / biomedical master's, SMFA) carry an honest cost omission. All
values are verified-or-omitted in ``tufts_profile``.

Derives a grounded ``program_preferences`` row for every program after apply
(``backfill_program_preferences``) so the program -> student match direction fires; claimed /
first-party rows are never touched.

Head-sync: chains off the current single head ``michwhorev1`` so this PR carries exactly one
head (SKILL.md §8 head-sync).

Deploy-safety (adopts the fleet pattern): the idempotent data apply runs inside a SAVEPOINT
bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot
get its locks quickly. The migration still records as applied so the chain advances;
``tufts_profile.apply()`` is idempotent and the routine re-applies + re-verifies the live
catalog after deploy.

Revision ID: tuftsprof1
Revises: michwhorev1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import tufts_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "tuftsprof1"
down_revision = "michwhorev1"
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
                select(Institution).where(Institution.name == tufts_profile.INSTITUTION_NAME)
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
            tufts_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == tufts_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  tuftsprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
