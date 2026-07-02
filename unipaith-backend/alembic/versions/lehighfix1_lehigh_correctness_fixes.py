"""Lehigh University - correctness fixes from the #1284 Codex review (re-apply)

#1284 (lehighprof1) shipped Lehigh's 164-program catalog to gold, but four correctness issues
surfaced in the Codex review after it merged. This migration re-applies ``lehigh_profile.apply()``
so the corrected data reaches production (lehighprof1 already recorded as applied, so a module-only
change would not otherwise update the live rows):

  * **Annual graduate tuition.** ``Program.tuition`` is consumed as an ANNUAL figure
    (``program_features`` exposes it as ``tuition_usd_per_year``; the matcher compares it to the
    student's annual budget; the page labels it "tuition / yr"). The prior build stored
    per-credit x whole-degree credits (a program TOTAL), overstating the annual budget signal by
    the number of program years. Now every graduate scalar is the per-credit rate x a 24-credit
    full-time academic year - a true annual figure.
  * **Professional Ed.D.** The Doctor of Education in Educational Leadership is a paid professional
    doctorate, not a funded research Ph.D.; it is now ``degree_type = professional`` with a filled
    per-credit annual tuition and professional (non-research) fit messaging.
  * **One-year MBA duration.** The accelerated one-year full-time MBA (and the ~16-month Executive
    MBA and ~10-month professional M.Eng. tracks) now carry their real published length instead of
    the 24-month master's default.
  * **Stale seed ranking facts.** ``RANKING_DATA`` now overwrites the bulk seed's stale
    ``acceptance_rate`` (0.3698) and ``graduation_rate`` (1.0) with the cited current facts
    (0.2593 / 0.8791) that the institution-browse cards and student match fallback read directly.

Re-derives ``program_preferences`` after apply. Idempotent (replace); the data apply runs inside a
``lock_timeout``-bounded SAVEPOINT and is skipped (logged) rather than hanging container boot.

Revision ID: lehighfix1
Revises: lehighprof1
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

revision = "lehighfix1"
down_revision = "lehighprof1"
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
                        session.flush()
                    backfill_program_preferences(session, institution_id=inst.id)
        session.commit()
    except Exception:  # pragma: no cover - deploy-safety guard
        session.rollback()
        log.exception("lehighfix1: data apply skipped (lock contention or error); chain advances")


def downgrade() -> None:
    pass
