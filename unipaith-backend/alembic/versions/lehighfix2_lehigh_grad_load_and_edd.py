"""Lehigh University - graduate full-time load + Ed.D. degree-family fixes (re-apply)

Two matcher-correctness issues from the #1285 Codex review (which merged before they could be
addressed). This re-applies ``lehigh_profile.apply()`` so the corrected data reaches production
(the prior migrations already recorded as applied, so a module-only change would not update the
live rows):

  * **Graduate full-time load.** #1285 annualized graduate tuition at 24 credits/year, but Lehigh's
    registrar defines graduate full-time enrollment as 9 credits per fall/spring semester (18
    credits/year). ``Program.tuition`` feeds ``tuition_usd_per_year`` and the annual-budget matcher,
    so the 24-credit basis overstated every Lehigh graduate program's annual tuition by ~33% (e.g.
    Engineering/CAS $39,840 -> $29,880). Now the annual scalar is the per-credit rate x 18 credits.
  * **Ed.D. degree family.** #1285 changed the Doctor of Education to ``degree_type = professional``
    to fix its funding/framing, but that gave it zero degree-level fit for Ed.D./doctoral searches
    (``target_education_level("EdD")`` canonicalizes to ``doctoral``; ``fit_degree_level`` has no
    professional<->doctoral adjacency). It is now kept in the ``phd`` (doctoral) family - so an
    Ed.D. search matches - while still being treated as a PAID professional doctorate (a filled
    per-credit annual tuition, not funded, with professional non-research fit messaging). The Ed.D.
    also carries an explicit 48-month duration so it does not inherit the research-Ph.D. 60-month
    default.
  * **Accelerated programs.** Programs that finish inside one academic year (<=12 months - the
    one-year MBA and the 10-month M.Eng. tracks) charge their FULL degree credits that year, so
    their annual tuition is the whole program (e.g. one-year MBA $50,400, 10-month M.Eng. $49,800)
    rather than the 18-credit multi-year full-time load.

Re-derives ``program_preferences`` after apply. Idempotent (replace); the data apply runs inside a
``lock_timeout``-bounded SAVEPOINT and is skipped (logged) rather than hanging container boot.

Claimed-row note: ``lehigh_profile.apply()`` rewrites curated fields unconditionally, matching the
whole enrichment fleet's modules (only ``backfill_program_preferences`` skips claimed rows). Lehigh
was seeded and enriched today with no claimed programs/schools, so this re-apply cannot clobber
first-party edits; the general is_claimed-aware apply() is a fleet-wide, app-code concern.

Revision ID: lehighfix2
Revises: lehighfix1
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

revision = "lehighfix2"
down_revision = "lehighfix1"
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
        log.exception("lehighfix2: data apply skipped (lock contention or error); chain advances")


def downgrade() -> None:
    pass
