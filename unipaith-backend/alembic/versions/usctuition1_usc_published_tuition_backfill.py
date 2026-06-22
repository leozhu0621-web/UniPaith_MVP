"""USC published tuition backfill (clears catalog-wide 0% tuition).

Clears USC's acute matcher-core defect (REPAIR_BACKLOG run 76 HIGH #1 — catalog-wide 0%
tuition): all 511 programs shipped ``tuition = null`` so the CPEF matcher scored budget-fit
blind on every program. Each program now carries USC's published 2025-26 annual tuition from
the USC Catalogue / Financial Aid COA (undergraduate sticker, general graduate flat rate,
engineering/business/cinema per-unit annualizations, and bespoke professional-school rates).
Fee-based online programs and the Thornton Artist Diploma keep tuition omitted-with-reason.
Re-applies ``usc_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: usctuition1
Revises: usccornuwmerge1
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
down_revision = "usccornuwmerge1"
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
