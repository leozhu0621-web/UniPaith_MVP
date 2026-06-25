"""enrich Vanderbilt: matcher-core cip_code + who_its_for + graduate tuition (data-only)

Re-applies ``unipaith.data.vanderbilt_profile.apply()`` to take Vanderbilt's already-clean
107-program catalog the rest of the way to gold:

* **cip_code** on all 107 programs (the matcher's CIP join key — REPAIR_BACKLOG #1; was null);
* **who_its_for** on all 107 programs (the universal-depth field — REPAIR_BACKLOG #4; was null),
  field+level-specific per program;
* **graduate tuition** for the master's / professional residual (REPAIR_BACKLOG #3): the Owen
  specialized master's (EMBA/MSF/MAcc/MMarketing/MMHC at the flat $74,500/yr rate, Master of
  Management at its published $76,700 program tuition), the School of Medicine MPH / MSCI / MGC /
  Au.D. at their published (front-loaded → average-annual) rates, and the Peabody online Ed.D. at
  its published per-credit rate — leaving only the brand-new online M.S. in AI honestly omitted
  (no tuition published yet); and
* three additional coverable ``external_reviews`` (M.S.N., Master of Marketing, MMHC) gathered
  from program-specific third-party coverage.

Then re-derives ``program_preferences`` so the refreshed cip_code feeds the program -> student
match. No schema (DDL) changes. Idempotent; no-op when Vanderbilt University is absent.

Revision ID: vandycip1
Revises: berkeleycip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import vanderbilt_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "vandycip1"
down_revision = "berkeleycip1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    # Run the (idempotent) data re-apply inside a SAVEPOINT bounded by the lock_timeout
    # set in env.py. If it can't get its locks quickly — because the already-running
    # task's scheduler is writing these same tables during the rolling deploy — DON'T
    # hang the container boot (that froze prod once: boot never finished migrating →
    # ECS health-check timeout → rollback → no backend could ship). Skip the data
    # re-apply, let the migration record as applied so the chain advances and the deploy
    # ships; vanderbilt_profile.apply() is idempotent and the enrichment routine re-applies
    # it on its next run. (Mirrors the berkeleycip1 deploy-hang fix.)
    try:
        with session.begin_nested():
            if vanderbilt_profile.apply(session):
                inst = session.scalar(
                    select(Institution).where(
                        Institution.name == vanderbilt_profile.INSTITUTION_NAME
                    )
                )
                if inst is not None:
                    # backfill_program_preferences only INSERTS missing rows + fills EMPTY
                    # keys; it never recomputes pref_fields on the DERIVED rows the
                    # fleet-wide progprefbf1 backfill created while cip_code was still NULL.
                    # So delete this institution's stale DERIVED rows first and re-derive
                    # them, so pref_fields (= fields_offered_for_program(cip_code=...))
                    # reflects the now-populated CIP codes. Claimed / first-party rows are
                    # NEVER touched. (Mirrors berkeleycip1.)
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
        # The savepoint already rolled back; the outer (alembic) transaction stays clean
        # so this migration still records as applied.
        print(f"  vandycip1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
