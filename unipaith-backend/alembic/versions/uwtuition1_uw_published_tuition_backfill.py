"""UW-Seattle published tuition backfill (clears catalog-wide 0% tuition).

Clears UW-Seattle's acute matcher-core defect (REPAIR_BACKLOG #4 — catalog-wide 0%
tuition): every one of the catalog's 360 programs shipped ``tuition = null`` so the CPEF
matcher scored budget-fit blind on every program. Each program now carries UW's published
2025-26 WA-resident annual tuition (UW Office of Planning & Budgeting / Financial Aid
student budgets): bachelor's the resident undergraduate sticker ($13,406); master's and PhD
the flat resident graduate Tier I sticker ($19,011, funding being a separate matcher signal,
not a $0 budget); the four bespoke professional schools their own published resident rates
(Law $47,073, Medicine $57,968, Dentistry $59,226, Pharmacy $36,708) and the two graduate-
schedule clinical doctorates theirs (DNP $35,064, DPT $27,807). Only the Doctor of Audiology
keeps tuition omitted-with-reason (variable graduate-tier schedule, no single published
annual figure). No undergrad-sticker copy-down onto graduate rows; structure + descriptions
unchanged (uw is already CERTIFIED_CLEAN).

Re-applies ``uw_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: uwtuition1
Revises: cmutuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwtuition1"
down_revision = "cmutuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uw_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
