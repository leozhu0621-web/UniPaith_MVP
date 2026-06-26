"""WashU — institution to gold + real catalog (empty-description seed repair)

Clears REPAIR_BACKLOG run 85 entry #2 (CRITICAL) for Washington University in St. Louis:
the institution entered as a 5-stub US-News seed whose five programs ALL shipped with an
EMPTY ``description_text`` (a blank student page + zero matcher embedding). This migration
takes the institution to gold (filling the seed's missing report-card / admissions-funnel /
diversity / cost-aid / campus-resources fields and adding a verified 4th campus photo) and
REPLACES the empty stubs with a verified, real-named 58-program catalog across WashU's
degree-granting schools (College of Arts & Sciences, McKelvey School of Engineering, Olin
Business School, Sam Fox School of Design & Visual Arts, Brown School, School of Law, School
of Medicine, Graduate School of Arts & Sciences).

Every program carries a researched, field-specific ``description_text`` (anti-stub clean),
a ``who_its_for`` statement, a real owning ``department``, a ``cip_code``, a verified
``delivery_format``, published tuition per credential level (funded PhDs carry funded=True/
tuition=None; programs whose annual figure is not separately published omit-with-reason),
working WashU news feeds, and sourced ``external_reviews`` on the coverable flagships (Olin
MBA, Brown School MSW, J.D., M.D.). All values are verified-or-omitted in ``washu_profile``.

Also drops this institution's DERIVED ProgramPreference rows for the empty seed stubs (so
``apply()`` can delete the stubs outright) and re-derives them after apply so pref_fields
reflects the now-populated CIP codes (claimed/first-party rows are never touched).

Deploy-safety (adopts the dartfinish1 pattern): the idempotent data apply runs inside a
SAVEPOINT bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if
it cannot get its locks quickly. The migration still records as applied so the chain
advances; ``washu_profile.apply()`` is idempotent and the routine re-applies it.

Revision ID: washuprof1
Revises: headmerge13a1
Create Date: 2026-06-26
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import washu_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "washuprof1"
down_revision = "headmerge13a1"
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
                    Institution.name == washu_profile.INSTITUTION_NAME
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
            washu_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == washu_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  washuprof1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
