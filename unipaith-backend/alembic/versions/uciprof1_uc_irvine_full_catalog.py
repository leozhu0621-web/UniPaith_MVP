"""UC Irvine — institution to gold + real ~160-program catalog (empty-description seed repair)

Clears REPAIR_BACKLOG run 87 entry #2 (CRITICAL) for the University of California, Irvine: the
institution entered as a 5-stub US-News seed whose five programs ALL shipped with an EMPTY
``description_text`` and a NULL ``department`` (a blank student page + zero matcher embedding).
This migration takes the institution to gold (filling the seed's missing report-card /
admissions-funnel / diversity / cost-aid / research / rankings / campus-photo-gallery / feed
fields) and REPLACES the five empty stubs with a verified, real-named ~160-program catalog
across UC Irvine's fifteen degree-granting schools (Humanities, Social Sciences, Biological
Sciences, Physical Sciences, the Donald Bren School of Information and Computer Sciences, the
Henry Samueli School of Engineering, the Claire Trevor School of the Arts, Social Ecology, the
Paul Merage School of Business, Education, the Joe C. Wen School of Population and Public
Health, the Sue & Bill Gross School of Nursing, Law, Medicine, and Pharmacy and Pharmaceutical
Sciences).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean —
analyze / frame_stripped(abs150) / template_slot / scrape_debris / machine_artifacts all 0),
a ``who_its_for`` statement, a real owning ``department``, a ``cip_code``, a verified
``delivery_format``, and published tuition per credential level (PUBLIC non-resident scalar for
the undergraduate sticker $49,679 with both rates in the breakdown; the UC non-resident
academic-graduate rate $34,317 for state-supported academic master's; each professional
school's registrar non-resident tuition where verified — J.D. $80,300, M.D. $62,021,
PharmD $72,022, M.S.N. $49,174, M.P.H. $43,957, Full-Time MBA $67,585, LL.M. $60,000;
self-supporting master's whose fee is not on the systemwide schedule omit-with-reason; funded
research doctorates funded=True/tuition=None). Institution gets rankings (U.S. News #32
nationally, #9 public), demographics, cost/aid, research centers, a 5-photo verified
Wikimedia-Commons campus gallery, and the working ``news.uci.edu`` RSS feed (verified to fetch
items). Sourced ``external_reviews`` on the coverable flagships (the J.D., the Full-Time MBA,
and the M.D.). All values are verified-or-omitted in ``uci_profile``.

Also drops this institution's DERIVED ProgramPreference rows for the empty seed stubs (so
``apply()`` can delete the stubs outright) and re-derives them after apply so pref_fields
reflect the now-populated CIP codes (claimed/first-party rows are never touched).

Head-sync: chains off the current single head ``ucdavisprof1`` (SKILL.md §8 head-sync step 1),
so this PR carries exactly one head.

Deploy-safety (adopts the ucdavisprof1/washuprof1 pattern): the idempotent data apply runs
inside a SAVEPOINT bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot
if it cannot get its locks quickly. The migration still records as applied so the chain
advances; ``uci_profile.apply()`` is idempotent and the routine re-applies it (and verifies the
live API content per the SKILL.md §9 verify-live-on-content rule).

Revision ID: uciprof1
Revises: ucdavisprof1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uci_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uciprof1"
down_revision = "ucdavisprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            # Drop this institution's DERIVED program-preference rows FIRST so the five
            # empty-description seed stubs lose their only dependent and ``apply()`` can
            # delete them outright. Claimed / first-party rows are NEVER touched.
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == uci_profile.INSTITUTION_NAME
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
            uci_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == uci_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  uciprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
