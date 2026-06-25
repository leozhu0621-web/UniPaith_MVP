"""Dartmouth — finish the Guarini catalog + matcher-core cip_code + universal who_its_for

Finishes the in-flight Dartmouth deferral and clears its open REPAIR_BACKLOG entries:

  * BREADTH (#2 in-flight): adds the full Guarini graduate catalog the prior pass deferred
    — Math / Earth Sciences / EEES / MCB / QBS / Computational Science & Modeling /
    Integrative Neuroscience / Health Policy & Clinical Practice PhDs; Chemistry MS,
    Comparative Literature MA, Earth Sciences MS, MFA in Sonic Practice; the five
    Geisel-based health-sciences master's (Epidemiology, Health Data Science, Healthcare
    Research, Implementation Science, Medical Informatics); and the Master of Energy
    Transition — taking the catalog from 43 to 61 real, distinctly-named programs.
  * cip_code (#1): stamps the IPEDS CIP family on EVERY program (the matcher's interest/
    field join key), previously null fleet-wide for Dartmouth.
  * who_its_for (#4): a field-specific audience statement on EVERY program (universal-depth
    field), previously null.
  * external_reviews (#5): adds a sourced Geisel M.D. review alongside the Tuck MBA.
  * tuition: the new Guarini full-time research master's carry the published $95,596 rate;
    the per-credit/online Geisel master's + the new MET are honest omit-with-reason; PhDs
    stay funded-omit. Never the undergrad sticker copied down.

All values are verified-or-omitted and stamped in ``dartmouth_profile``.

Deploy-safety (adopts the berkeleycip1 / FLAG follow-up pattern): the idempotent data
re-apply runs inside a SAVEPOINT bounded by ``lock_timeout`` (set in env.py, and re-set
locally here so this migration is safe even on an env.py that predates it). If it cannot
get its locks quickly — because the already-running task's scheduler writes these same
tables during the rolling deploy — it is SKIPPED rather than hanging container boot (the
incident that froze prod on berkeleycip1). The migration still records as applied so the
chain advances and the deploy ships; ``dartmouth_profile.apply()`` is idempotent and the
enrichment routine re-applies it next run.

Revision ID: dartfinish1
Revises: columbiadualmerge1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import dartmouth_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "dartfinish1"
down_revision = "columbiadualmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        # Bound any lock wait so a contended table never hangs container boot.
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            dartmouth_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(
                    Institution.name == dartmouth_profile.INSTITUTION_NAME
                )
            )
            if inst is not None:
                # The fleet-wide progprefbf1 backfill created derived ProgramPreference
                # rows while Dartmouth's cip_code was still NULL, so pref_fields was
                # derived without the CIP signal. Delete this institution's stale DERIVED
                # rows and re-derive so pref_fields reflects the now-populated CIP codes;
                # claimed / first-party rows are NEVER touched. (Mirrors berkeleycip1.)
                prog_ids = session.scalars(
                    select(Program.id).where(Program.institution_id == inst.id)
                ).all()
                if prog_ids:
                    session.execute(
                        delete(ProgramPreference).where(
                            ProgramPreference.program_id.in_(prog_ids),
                            ProgramPreference.source == "derived",
                        )
                    )
                backfill_program_preferences(session, institution_id=inst.id)
        session.flush()
    except Exception as exc:  # noqa: BLE001 — never let a data re-apply freeze the deploy
        print(
            f"  dartfinish1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
