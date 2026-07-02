"""Lehigh - part-time-null fix + unify dual head (lehighfix3 + casewesttuition1)

Merge migration that (a) unifies the dual alembic head created when #1288 (``lehighfix3``) and
#1286 (``casewesttuition1``) auto-merged concurrently off the same base, and (b) re-applies
``lehigh_profile.apply()`` to ship one correctness fix from the #1288 Codex review:

  * **part_time_available null, not False.** #1288 wrote ``part_time_available = False`` for every
    on-campus Lehigh program. The matcher projects any non-null value into its sparse vector and
    reads a stored ``False`` as an unmet hard want for ``wants_part_time`` students - so on-campus
    programs with no explicit negative schedule evidence became hard misses instead of "unknown".
    ``apply()`` now sets ``True`` only for verified part-time-friendly rows (online/hybrid + the
    part-time professional Ed.D.) and leaves the rest ``None``.

The columns this data apply touches - ``programs.part_time_available`` (``aimig01typedfit``) and
``programs.is_claimed`` (``aiclaim01``) - are already ancestors in the single linear chain (both are
long applied in production), so this re-apply cannot be ordered before them and cannot self-skip on
a missing column. (A ``depends_on`` on those revisions is redundant AND breaks alembic's merge
head-tracking, so it is intentionally omitted.)

Re-derives ``program_preferences`` (unclaimed programs only). Idempotent (replace); the data apply
runs inside a ``lock_timeout``-bounded SAVEPOINT and is skipped (logged) rather than hanging boot.

Revision ID: lehighfix4
Revises: lehighfix3, casewesttuition1
Create Date: 2026-07-02
"""

from __future__ import annotations

import logging

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import lehigh_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "lehighfix4"
down_revision = ("lehighfix3", "casewesttuition1")
branch_labels = None
depends_on = None

log = logging.getLogger("alembic.runtime.migration")


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    try:
        session.execute(text("SET LOCAL lock_timeout = '30s'"))
        with session.begin_nested():
            applied = lehigh_profile.apply(session)
            if applied:
                inst = session.scalar(
                    select(Institution).where(Institution.name == lehigh_profile.INSTITUTION_NAME)
                )
                if inst is not None:
                    unclaimed_ids = session.scalars(
                        select(Program.id).where(
                            Program.institution_id == inst.id,
                            Program.is_claimed.is_(False),
                        )
                    ).all()
                    if unclaimed_ids:
                        session.execute(
                            delete(ProgramPreference).where(
                                ProgramPreference.program_id.in_(unclaimed_ids),
                                ProgramPreference.source == "derived",
                            )
                        )
                        session.flush()
                    backfill_program_preferences(session, institution_id=inst.id)
        session.commit()
    except Exception:  # pragma: no cover - deploy-safety guard
        session.rollback()
        log.exception("lehighfix4: data apply skipped (lock contention or error); chain advances")


def downgrade() -> None:
    pass
