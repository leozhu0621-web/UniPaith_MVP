"""UC Santa Barbara — institution to gold + real ~169-program catalog (bare-seed enrichment)

Takes the University of California-Santa Barbara from a bare US-News institution-level seed
(0 real programs, a stub description, a null website, no working feed) to gold: real
report-card / admissions-funnel / diversity / cost-aid / research / rankings / campus-photo-
gallery / feed fields, plus a verified, real-named ~169-program catalog across UCSB's five
colleges/schools — the College of Letters and Science, the Robert Mehrabian College of
Engineering, the College of Creative Studies, the Bren School of Environmental Science &
Management, and the Gevirtz Graduate School of Education.

Every program name, degree designation, and owning department is confirmed against a
catalog.ucsb.edu program page; every program carries a researched, field-specific
``description_text`` (anti-stub clean — analyze / frame_stripped(abs150) / template_slot /
scrape_debris / machine_artifacts all 0), a distinct ``who_its_for`` (169/169 distinct), a real
owning ``department``, a ``cip_code``, a verified ``delivery_format``, and published tuition per
credential level. Because UCSB is PUBLIC the flat ``tuition`` scalar is the NON-RESIDENT
undergraduate rate ($54,858, 2026-27) with both rates in ``cost_data.breakdown``; state-supported
academic master's carry the UC non-resident academic-graduate rate ($30,922, 2025-26); funded
research doctorates carry funded=True / tuition=None; self-supporting professional master's (MESM,
MEDS, MTM) omit tuition with a reason. Institution gets U.S. News #41 national / #14 public, QS
#179, THE #72, R1 / WSCUC, the Fall-2025 first-year funnel (110,178 / 42,170 / 38.3%), College
Scorecard report-card stats, a verified 5-photo Wikimedia-Commons campus gallery, and the working
``news.ucsb.edu/all/feed`` RSS (verified to fetch items). external_reviews are recorded in each
program's ``_standard.omitted`` pending a later gathered-coverage depth pass (no fabricated review
ships). All values are verified-or-omitted in ``ucsb_profile``.

Also drops this institution's DERIVED ProgramPreference rows for the seed stubs (so ``apply()``
can delete them) and re-derives them after apply so pref_fields reflect the populated CIP codes
(claimed/first-party rows are never touched).

Head-sync: chains off the current single head ``nyureviews1`` (SKILL.md §8 head-sync step 1),
so this PR carries exactly one head.

Deploy-safety (adopts the uciprof1/ucdavisprof1 pattern): the idempotent data apply runs inside a
SAVEPOINT bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it
cannot get its locks quickly. The migration still records as applied so the chain advances;
``ucsb_profile.apply()`` is idempotent and the routine re-applies it (and verifies the live API
content per the SKILL.md §9 verify-live-on-content rule).

Revision ID: ucsbprof1
Revises: nyureviews1
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
down_revision = "nyureviews1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == ucsb_profile.INSTITUTION_NAME
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
            ucsb_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == ucsb_profile.INSTITUTION_NAME
                )
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
