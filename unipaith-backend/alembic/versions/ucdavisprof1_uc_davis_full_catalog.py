"""UC Davis — institution to gold + real 151-program catalog (empty-description seed repair)

Clears REPAIR_BACKLOG run 86 entry #2 (CRITICAL) for the University of California, Davis: the
institution entered as a 5-stub US-News seed whose five programs ALL shipped with an EMPTY
``description_text`` and a NULL ``department`` (a blank student page + zero matcher embedding).
This migration takes the institution to gold (filling the seed's missing report-card /
admissions-funnel / diversity / cost-aid / campus-resources / rankings / campus-photo-gallery /
feed fields) and REPLACES the five empty stubs with a verified, real-named 151-program catalog
across UC Davis's eleven degree-granting colleges and schools (the College of Agricultural and
Environmental Sciences, the College of Biological Sciences, the College of Engineering, the
College of Letters and Science, the Graduate School of Management, the School of Education, the
School of Law, the School of Medicine, the UC Davis Weill School of Veterinary Medicine, the
Betty Irene Moore School of Nursing, and Graduate Studies).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean),
a ``who_its_for`` statement, a real owning ``department``, a ``cip_code`` (from the
IPEDS/Scorecard CIP families for UNITID 110644), a verified ``delivery_format``, published
tuition per credential level (PUBLIC non-resident scalar for the undergraduate sticker $50,974,
the UCOP 2025-26 graduate-academic non-resident rate for academic master's, each professional
school's published non-resident tuition where verified — J.D. $72,115, M.D. $60,525,
D.V.M. $42,695, LL.M. $65,879 — programs whose exact all-in figure could not be verified
omit-with-reason recording the verified UCOP Professional Degree Supplemental Tuition, and
funded research doctorates funded=True/tuition=None), working UC Davis news feeds (the
institution-wide ``ucdavis.edu/news/all/feed`` and the UC Davis Health feed for the
health-system schools, both verified to fetch items), a 5-photo verified Wikimedia-Commons
campus gallery, and sourced ``external_reviews`` on the coverable flagships (the #1-ranked
D.V.M., the M.B.A., the J.D., and the M.D.). All values are verified-or-omitted in
``ucdavis_profile``.

Also drops this institution's DERIVED ProgramPreference rows for the empty seed stubs (so
``apply()`` can delete the stubs outright) and re-derives them after apply so pref_fields
reflect the now-populated CIP codes (claimed/first-party rows are never touched).

Head-sync: chains off the current single head ``uncprof1`` (re-pointed from ``uvaprof1`` after
the concurrent UNC seed repair #1176 merged), so this PR carries exactly one head
(SKILL.md §8 head-sync step 2).

Deploy-safety (adopts the uvaprof1/washuprof1 pattern): the idempotent data apply runs inside a
SAVEPOINT bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it
cannot get its locks quickly. The migration still records as applied so the chain advances;
``ucdavis_profile.apply()`` is idempotent and the routine re-applies it.

Revision ID: ucdavisprof1
Revises: uncprof1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucdavis_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ucdavisprof1"
down_revision = "uncprof1"
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
                    Institution.name == ucdavis_profile.INSTITUTION_NAME
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
            ucdavis_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == ucdavis_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  ucdavisprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
