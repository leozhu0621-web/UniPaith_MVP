"""UW-Seattle fee-based tuition — matcher-core budget coverage (REPAIR_BACKLOG #1)

A single matcher-core repair on UW-Seattle's already-real 360-program catalog (names,
departments, descriptions, ``cip_code``, ``who_its_for``, casing, photos, feeds, and the
state-supported/professional tuition tiers were already gold; structure and every other
dimension are untouched):

  ``tuition`` (matcher-core budget scalar, run-74 per-tier coverage rule): UW's master's tier
  shipped 14 nulls and its professional/bachelor's tiers 1 each — all self-sustaining, fee-based
  programs the ``_tuition_for`` scalar returned ``None`` for because they bill a program-specific
  per-credit rate rather than the state-supported Tier I sticker. But each of the 14 fee-based
  programs PUBLISHES its own residency-independent per-credit rate + credits-to-degree, so a real
  annual figure is knowable — omit-never-guess requires the published number, not a matcher-blind
  null. ``_FEE_BASED_TUITION`` now carries each program's verified per-credit rate × credits,
  annualized over the program's published length and stamped as the flat scalar + cost card
  (in-state == out-of-state, no residency split), each cited to the program's own cost page
  (e.g. MSME $1,330/cr × 42 = $55,860 → $27,930/yr; MSIM $1,132/cr × 65 = $73,580 → $36,790/yr;
  MHA $950/cr × 76 = $72,200 → $36,100/yr). Master's tuition coverage 138/152 → 152/152.

Only TWO programs keep ``cost_data.tuition_usd`` omitted-with-reason (recorded in
``_standard.omitted``, never a silent null): the Doctor of Audiology (variable graduate-tier
schedule, no single published annual figure) and the online BA in Integrated Social Sciences
(a per-credit degree-completion program with no fixed credits-to-degree total). No names,
departments, descriptions, or programs changed — this is a cost-field-only fill.

Idempotent: re-applies ``uw_profile.apply()`` (updates existing rows by slug; no programs added
or removed) and re-derives DERIVED program preferences so ``pref_*`` stay consistent; claimed /
first-party rows are never touched. Direct apply (no lock-timeout SAVEPOINT) — the update is a
plain per-row cost rewrite, so the apply genuinely runs in prod (avoids the self-skipping-
migration stranding, FLAG #1).

Revision ID: uwfeetuition1
Revises: princetonwho1
Create Date: 2026-07-01
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile
from unipaith.models.institution import Institution, Program, ProgramPreference
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwfeetuition1"
down_revision = "princetonwho1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uw_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uw_profile.INSTITUTION_NAME)
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
    session.flush()


def downgrade() -> None:
    pass
