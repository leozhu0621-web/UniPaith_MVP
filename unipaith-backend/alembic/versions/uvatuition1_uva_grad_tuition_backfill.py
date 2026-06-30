"""UVA — backfill published master's tuition (matcher budget signal)

Clears REPAIR_BACKLOG entry #1 (HIGH, matcher-core) for the University of Virginia: the
bachelor's tier was ~100% covered but the MASTER'S tier shipped 8 of 16 programs (50% — the
worst master's null fraction in the live fleet) with a null ``tuition``, so the CPEF matcher
scored those programs' budget-fit blind. Seven of the eight nulls publish a verified flat
ANNUAL non-resident rate stated in UVA's 2025-26 Board of Visitors tuition & fee rate sheet
(the same first-party source the module already cites — every existing constant round-trips to
it). They were omitted only because the earlier reason wrongly assumed engineering /
architecture / nursing master's "publish no flat annual figure"; the Board of Visitors sheet
lists one for each (the per-credit rate is the part-time alternative, now noted):

  * M.S. in Computer Science          → $39,926 (CS master's, distinct higher rate)
  * M.S. in Systems Engineering       → $34,822 (School of Engineering master's)
  * M.S. in Biomedical Engineering    → $34,822 (School of Engineering master's)
  * M.S. in Nursing                   → $35,832 (School of Nursing master's; == DNP rate)
  * Master of Architecture            → $36,730 (Graduate School of Architecture master's)
  * Master of Urban & Env. Planning   → $36,730 (Graduate School of Architecture master's)
  * Master of Landscape Architecture  → $36,730 (Graduate School of Architecture master's)

Master's coverage therefore moves 8/16 → 15/16. The one remaining null (the fully ONLINE M.S.
in Data Science) is billed only per credit hour ($1,467, resident and non-resident alike) with
no flat annual figure published, so it stays honestly omitted-with-reason (never estimated).
PhD tiers remain funded=True/tuition=None; the professional tier (M.D./J.D./D.N.P.) was already
fully covered. The public scalar carries the NON-RESIDENT rate (run-83 rule); each cost_note
preserves the Virginia-resident rate and the per-credit part-time rate.

This is an idempotent data re-apply of ``uva_profile.apply()`` (which now carries the seven
verified annual rates) plus ``backfill_program_preferences`` so derived preference rows stay
covered; claimed / first-party rows are never touched.

Deploy-safety (adopts the washutuition1 pattern): the data apply runs inside a SAVEPOINT bounded
by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it cannot get its locks
quickly. The migration still records as applied so the chain advances; ``uva_profile.apply()``
is idempotent and the routine re-applies + verifies live.

Revision ID: uvatuition1
Revises: washutuition1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uva_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uvatuition1"
down_revision = "washutuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
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
            f"  uvatuition1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
