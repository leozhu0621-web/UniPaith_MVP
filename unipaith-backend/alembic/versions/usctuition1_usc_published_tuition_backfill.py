"""USC published tuition backfill — clear catalog-wide 0% matcher starvation.

Clears USC's acute matcher-core defect (REPAIR_BACKLOG run 76 HIGH #1): the
511-program catalog shipped 0% ``tuition`` on EVERY tier (bachelor's included), so the
CPEF budget-fit signal scored every program blind. Tuition is institution-PUBLISHED, so
each program now carries a USC 2025-26 figure (verify-or-omit, never guessed):

  * undergraduate — the uniform $73,260 sticker (same in-state/out-of-state);
  * graduate master's — USC's per-unit graduate rate, annualized at the full-time load
    (general $2,467, Cinematic Arts $2,624, Viterbi $2,665, Marshall $2,541 per unit);
  * professional doctorates — their own published flat rates (J.D., M.D., D.D.S.,
    Pharm.D., D.P.T.) and the Full-Time MBA program rate;
  * research doctorates, clinical professional doctorates with no single published
    annual figure, the non-degree diploma, and the per-program-flat MBA variants —
    tuition omitted-with-reason (funding / per-unit basis recorded in the cost note).

Re-applies ``usc_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: usctuition1
Revises: cornuwmrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import usc_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "usctuition1"
down_revision = "cornuwmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    usc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == usc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
