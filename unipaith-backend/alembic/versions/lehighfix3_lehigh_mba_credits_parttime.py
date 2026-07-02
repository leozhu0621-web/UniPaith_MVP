"""Lehigh University - MBA credit count, part-time availability, claimed-pref guard (re-apply)

Three refinements from the #1287 Codex review (which auto-merged before they could be addressed).
Re-applies ``lehigh_profile.apply()`` so the corrected data reaches production:

  * **Full-time MBA credit count.** The accelerated one-year MBA is a 42-credit curriculum (27 core
    + 15 electives, per Lehigh's Full-Time MBA curriculum page), not 36. Since the accelerated
    annual scalar is per-credit x full degree credits, its annual tuition corrects to $58,800
    (42 x $1,400) from $50,400.
  * **Part-time availability.** ``Program.part_time_available`` drives the matcher's schedule-
    flexibility fit (a ``wants_part_time`` student gets a hard miss when it is falsy). Online/hybrid
    programs and the part-time professional Ed.D. (modeled for working administrators) are now
    flagged available.
  * **Claimed-program preference guard.** The derived-``ProgramPreference`` delete below now
    EXCLUDES claimed programs, so a claim-before-edit program (whose pref is still ``source =
    derived``) keeps its program-side matching signals - ``backfill_program_preferences`` already
    skips claimed programs, so deleting their derived rows would have left them with none.

Idempotent (replace); the data apply runs inside a ``lock_timeout``-bounded SAVEPOINT and is skipped
(logged) rather than hanging container boot. ``apply()`` itself still rewrites curated fields for
UNCLAIMED rows only in spirit (Lehigh has no claimed rows today; an is_claimed-aware apply() is a
fleet-wide app-code concern).

Revision ID: lehighfix3
Revises: lehighfix2
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

revision = "lehighfix3"
down_revision = "lehighfix2"
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
                    # Only refresh derived prefs on UNCLAIMED programs: a claimed program may still
                    # carry a derived pref (claim-before-edit), and backfill skips claimed programs,
                    # so deleting it would strip that program's program-side match signals.
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
        log.exception("lehighfix3: data apply skipped (lock contention or error); chain advances")


def downgrade() -> None:
    pass
