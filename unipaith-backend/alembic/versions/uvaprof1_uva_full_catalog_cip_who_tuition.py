"""UVA — institution to gold + real 100-program catalog (empty-description seed repair)

Clears REPAIR_BACKLOG run 86 entry #2 (CRITICAL) for the University of Virginia: the
institution entered as a 5-stub US-News seed whose five programs ALL shipped with an EMPTY
``description_text`` (a blank student page + zero matcher embedding). This migration takes
the institution to gold (filling the seed's missing report-card / admissions-funnel /
diversity / cost-aid / campus-resources / rankings / feed fields) and REPLACES the five
empty stubs with a verified, real-named 100-program catalog across UVA's twelve
degree-granting schools (College of Arts & Sciences, Engineering and Applied Science,
McIntire Commerce, Architecture, Nursing, Education and Human Development, Data Science,
Batten Leadership and Public Policy, Darden Business, Law, Medicine, and the Graduate School
of Arts & Sciences).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean),
a ``who_its_for`` statement, a real owning ``department``, a ``cip_code`` (from the
IPEDS/Scorecard CIP list for UNITID 234076), a verified ``delivery_format``, published
tuition per credential level (PUBLIC non-resident scalar for the undergraduate sticker, the
Board-of-Visitors non-resident annual rate for each professional/graduate program that
publishes one, per-credit-billed programs omit-with-reason recording the per-credit rate,
and funded research doctorates funded=True/tuition=None), working UVA news feeds, and
sourced ``external_reviews`` on the coverable flagships (Darden MBA, the J.D., the M.D., the
McIntire Commerce B.S., the Batten M.P.P., and the Data Science M.S.). All values are
verified-or-omitted in ``uva_profile``.

Also drops this institution's DERIVED ProgramPreference rows for the empty seed stubs (so
``apply()`` can delete the stubs outright) and re-derives them after apply so pref_fields
reflect the now-populated CIP codes (claimed/first-party rows are never touched).

Head-sync: chains off the current single head ``togetherprov1`` (which itself now chains
off ``washuprof1`` after the upstream dual-head fix), so this PR carries exactly one head
(SKILL.md §8 head-sync).

Deploy-safety (adopts the washuprof1 pattern): the idempotent data apply runs inside a
SAVEPOINT bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if
it cannot get its locks quickly. The migration still records as applied so the chain
advances; ``uva_profile.apply()`` is idempotent and the routine re-applies it.

Revision ID: uvaprof1
Revises: togetherprov1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uva_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uvaprof1"
down_revision = "togetherprov1"
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
                    Institution.name == uva_profile.INSTITUTION_NAME
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
            uva_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == uva_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  uvaprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
