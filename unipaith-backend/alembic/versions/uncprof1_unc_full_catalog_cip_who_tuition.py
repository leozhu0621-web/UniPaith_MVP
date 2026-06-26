"""UNC-Chapel Hill — institution to gold + real 89-program catalog (empty-description seed repair)

Clears REPAIR_BACKLOG run 86 entry #2 (CRITICAL) for the University of North Carolina at
Chapel Hill: the institution entered as a 5-stub US-News seed whose five programs ALL shipped
with an EMPTY ``description_text`` and a NULL ``department`` (a blank student page + zero
matcher embedding). This migration takes the institution to gold (filling the seed's missing
report-card / admissions-funnel / diversity / cost-aid / campus-resources / rankings / feed
fields and adding a verified 4th campus photo) and REPLACES the five empty stubs with a
verified, real-named 89-program catalog across UNC's thirteen degree-granting schools (College
of Arts & Sciences, School of Data Science and Society, Hussman School of Journalism and Media,
Kenan-Flagler Business School, Gillings School of Global Public Health, School of Nursing,
Eshelman School of Pharmacy, Adams School of Dentistry, School of Medicine, School of Law,
School of Education, School of Information and Library Science, and School of Social Work).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean),
a ``who_its_for`` statement, a real owning ``department``, a ``cip_code``, a verified
``delivery_format``, and published 2025-26 tuition per credential level (PUBLIC non-resident
scalar for the matcher, BOTH the NC-resident and non-resident rates preserved in
``cost_data.breakdown``), working UNC news feeds (the institution feed plus the College,
Hussman, Gillings, and Law school feeds), and sourced ``external_reviews`` on the coverable
flagships (the Kenan-Flagler MBA and the J.D.). All values are verified-or-omitted in
``unc_profile``.

Also drops this institution's DERIVED ProgramPreference rows for the empty seed stubs (so
``apply()`` can delete the stubs outright) and re-derives them after apply so pref_fields
reflect the now-populated CIP codes (claimed/first-party rows are never touched).

Head-sync: chains off the current single head ``uvaprof1`` so this PR carries exactly one
head (SKILL.md §8 head-sync).

Deploy-safety (adopts the washuprof1 / uvaprof1 pattern): the idempotent data apply runs
inside a SAVEPOINT bounded by ``lock_timeout`` and is SKIPPED rather than hanging container
boot if it cannot get its locks quickly. The migration still records as applied so the chain
advances; ``unc_profile.apply()`` is idempotent and the routine re-applies it.

Revision ID: uncprof1
Revises: uvaprof1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import unc_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uncprof1"
down_revision = "uvaprof1"
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
                    Institution.name == unc_profile.INSTITUTION_NAME
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
            unc_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == unc_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  uncprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
