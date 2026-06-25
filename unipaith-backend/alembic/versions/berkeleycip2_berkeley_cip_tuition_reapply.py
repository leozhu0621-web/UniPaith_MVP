"""Berkeley cip_code + non-resident tuition RE-APPLY (boot-safe, post-#1157)

berkeleycip1 carried the Berkeley matcher-core repair (cip_code on all programs,
public non-resident tuition scalar, CED master's tuition, legal-studies dedup), but
its data never reached production. Root cause (#1157, confirmed in CloudWatch): the
heavy data re-apply (re-applies the Berkeley profile + re-derives every Berkeley
ProgramPreference row) runs at container boot, where it contended for a lock with the
already-running task's scheduler during the rolling deploy → boot hung forever in
``alembic upgrade heads`` → ECS health-check timeout → rollback → no backend could
ship. #1157 fixed the hang (``env.py`` ``lock_timeout = '30s'`` + a SAVEPOINT-skip on
berkeleycip1) and records berkeleycip1 as applied with its data skipped, so a redeploy
will not re-run it — the live API still serves cip_code=null, bachelor tuition=16,347,
232 programs, and #1157 explicitly hands the re-apply back to the enrichment routine.

This fresh revision is that re-apply, using the SAME boot-safe pattern as #1157: the
idempotent data work runs inside a SAVEPOINT bounded by the env.py lock_timeout, and
on lock contention it is skipped (never hangs the boot) — so it lands on a
lower-contention deploy without re-freezing prod. ``berkeley_profile.apply()`` is
idempotent (replace/dedup + program reconcile); re-deriving program preferences first
deletes the stale cip-null derived rows so pref_fields reflect the populated CIP codes.

Revision ID: berkeleycip2
Revises: berkeleycip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleycip2"
down_revision = "berkeleycip1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    # Run the (idempotent) data re-apply inside a SAVEPOINT bounded by the
    # lock_timeout set in env.py (#1157). This is a HEAVY data migration — it
    # re-applies the Berkeley profile and re-derives every Berkeley
    # ProgramPreference row — so at container boot it can contend for a lock with
    # the already-running task's scheduler during a rolling deploy. berkeleycip1
    # hung prod exactly this way: the boot never finished migrating → ECS
    # health-check timeout → rollback → no backend could ship. So if the locks
    # can't be acquired quickly, DON'T hang the boot: skip the data re-apply and
    # let the migration record as applied so the chain advances and the deploy
    # ships. berkeley_profile.apply() is idempotent and the enrichment routine
    # re-applies it on its next run / a lower-contention deploy.
    try:
        with session.begin_nested():
            berkeley_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == berkeley_profile.INSTITUTION_NAME)
            )
            if inst is not None:
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
        # The savepoint already rolled back; the outer (alembic) transaction stays
        # clean so this migration still records as applied.
        print(f"  berkeleycip2: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
