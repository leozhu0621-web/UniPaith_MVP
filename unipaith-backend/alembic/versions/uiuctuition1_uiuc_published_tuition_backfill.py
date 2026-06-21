"""UIUC published tuition backfill across the whole catalog.

Clears UIUC's acute matcher-core defect (REPAIR_BACKLOG run 74 HIGH #3): the 419-program
catalog shipped ``tuition`` null on EVERY tier, so the CPEF matcher scored budget-fit blind
on every program. Every program now carries a UIUC-published 2025-26 tuition figure
(Illinois-resident annual tuition as the matcher number; non-resident in the breakdown):
the resident base undergraduate rate, the graduate base / Grainger-engineering / named-Gies
rates, the online flat-tuition totals (iMBA, iMSM, iMSA, online MCS), and the professional
rates (Law, Medicine, Veterinary Medicine). Funded research doctorates stamp tuition 0 with
the published sticker recorded in the note (funding is a separate signal).

Re-applies ``uiuc_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: uiuctuition1
Revises: uwmadtuition1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uiuctuition1"
down_revision = "uwmadtuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uiuc_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uiuc_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
