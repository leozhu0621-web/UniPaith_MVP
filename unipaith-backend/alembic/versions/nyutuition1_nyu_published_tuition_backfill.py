"""NYU published tuition backfill (clears catalog-wide 0% tuition).

Clears NYU's acute matcher-core defect (REPAIR_BACKLOG run 76 HIGH #1 — catalog-wide 0%
tuition): all ~500 New York University programs shipped ``tuition = null`` so the CPEF
matcher scored budget-fit blind on every one. Each program now carries NYU's published
tuition as the budget signal — the per-school undergraduate direct cost (tuition + fees),
the published per-credit / flat graduate rate per school annualized at NYU's full-time
standard (12 points/semester), and the professional flats (J.D. $83,952, D.D.S. $106,962,
M.D. tuition-free). Funded research doctorates and programs billed at a program-specific
cohort / per-credit rate NYU does not publish as one verified annual figure keep tuition
omitted-with-reason (never guessed). Re-applies ``nyu_profile.apply()`` (idempotent) and
re-derives program-preference rows.

Revision ID: nyutuition1
Revises: cornuwuscmrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import nyu_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nyutuition1"
down_revision = "cornuwuscmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    nyu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == nyu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
