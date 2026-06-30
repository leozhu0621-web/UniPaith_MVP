"""WashU — backfill published master's tuition (matcher budget signal)

Clears REPAIR_BACKLOG entry #1 (HIGH, matcher-core) for Washington University in St. Louis:
the bachelor's tier was ~100% covered but the MASTER'S tier shipped 6 of 10 programs with a
null ``tuition``, so the CPEF matcher scored those programs' budget-fit blind. Four of the six
nulls publish a verified ANNUAL rate stated verbatim in WashU's 2025-26 "The Source" tuition
release (the same first-party source the module already cites) — they were omitted only because
the earlier reason wrongly assumed the figure was "not separately stated in the university
tuition release":

  * Brown School Master of Public Health  → $43,710
  * School of Law Master of Laws (LL.M.)  → $72,792 (Law J.D./J.S.D./LL.M./M.L.S. share one rate)
  * Sam Fox Master of Architecture        → $60,975
  * Sam Fox Master of Fine Arts           → $50,680

Master's coverage therefore moves 4/10 → 8/10. The two remaining nulls (Olin MS in Finance,
Olin MS in Business Analytics) are Olin specialized master's billed at a flat PROGRAM rate
published only on the Olin program pages — no verifiable 2025-26 annual figure — so they stay
honestly omitted-with-reason (never estimated). PhD tiers remain funded=True/tuition=None.

This is an idempotent data re-apply of ``washu_profile.apply()`` (which now carries the four
verified rates) plus ``backfill_program_preferences`` so derived preference rows stay covered;
claimed / first-party rows are never touched.

Deploy-safety (adopts the dartfinish1/washuprof1 pattern): the data apply runs inside a
SAVEPOINT bounded by ``lock_timeout`` and is SKIPPED rather than hanging container boot if it
cannot get its locks quickly. The migration still records as applied so the chain advances;
``washu_profile.apply()`` is idempotent and the routine re-applies + verifies live.

Revision ID: washutuition1
Revises: gtowntuition1
Create Date: 2026-06-30
"""

from __future__ import annotations

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import washu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "washutuition1"
down_revision = "gtowntuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
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
            f"  washutuition1: data re-apply skipped "
            f"({type(exc).__name__}: {str(exc)[:140]})"
        )


def downgrade() -> None:
    pass
