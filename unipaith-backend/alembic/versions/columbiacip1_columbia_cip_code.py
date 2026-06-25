"""Columbia matcher-core cip_code (REPAIR_BACKLOG #1)

One matcher-core repair for Columbia University (UNITID 190150), from already-in-module
verified figures — no fabrication:

* #1 — stamps the verified NCES CIP-2020 ``cip_code`` on all 167 programs (the CIP join
  key the CPEF matcher reads, 2-digit family, for the field/interest signal). The codes
  were already carried in the module's specs to gate catalog breadth; the enrichment
  apply now assigns ``p.cip_code`` so the program → student match is no longer field-blind.

Columbia is a PRIVATE university, so its single published tuition sticker is already the
correct flat budget scalar (no resident/non-resident split) — this migration changes only
``cip_code``. Graduate tuition is unchanged: it stays verified-where-published and
omitted-with-reason for funded Ph.D./J.S.D. and per-credit-only DrPH rows.

Idempotent: re-applies ``columbia_profile.apply()`` and re-derives program-preference rows.

Revision ID: columbiacip1
Revises: berkeleycip1
Create Date: 2026-06-25
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "columbiacip1"
down_revision = "berkeleycip1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    # Run the (idempotent) data re-apply inside a SAVEPOINT bounded by the lock_timeout
    # set in env.py. If it can't get its locks quickly — because the already-running
    # task's scheduler is writing these same tables during the rolling deploy — DON'T
    # hang the container boot (a hanging boot froze prod once: ECS health-check timeout →
    # rollback → no backend could ship). Skip the data re-apply, record the migration as
    # applied so the chain advances and the deploy ships; columbia_profile.apply() is
    # idempotent and the enrichment routine re-applies it on its next run.
    try:
        with session.begin_nested():
            columbia_profile.apply(session)
            inst = session.scalar(
                select(Institution).where(Institution.name == columbia_profile.INSTITUTION_NAME)
            )
            if inst is not None:
                # backfill_program_preferences only INSERTS missing rows + fills EMPTY keys;
                # it never recomputes pref_fields/pref_levels on the derived rows the
                # fleet-wide progprefbf1 backfill created while cip_code was still NULL. So
                # delete this institution's stale DERIVED rows first and re-derive them, so
                # pref_fields (= fields_offered_for_program(cip_code=...)) reflects the
                # now-populated CIP codes. Claimed / first-party rows are NEVER touched.
                # (Mirrors berkeleycip1 / gatechcip1.)
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
        print(f"  columbiacip1: data re-apply skipped ({type(exc).__name__}: {str(exc)[:140]})")


def downgrade() -> None:
    pass
