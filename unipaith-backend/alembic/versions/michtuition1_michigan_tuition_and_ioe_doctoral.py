"""Michigan published tuition backfill + IOE doctoral description repair.

Clears Michigan's two acute defects (REPAIR_BACKLOG run 73 CRITICAL #2 / HIGH #6):
  1. The one ``template_slot_artifacts`` doctoral row (Industrial and Operations
     Engineering Ph.D. — an empty-focus "advances original research in ," splice) is
     replaced by a researched per-credential doctoral body, with distinct master's and
     bachelor's bodies for the same field (template_slot 1 → 0).
  2. ``tuition`` was null catalog-wide (matcher-core budget-fit starvation). Every program
     now carries a U-M-published 2025-26 tuition figure by school and credential level
     (Office of the Registrar Fee Bulletin), funded research doctoral rows at 0, with the
     single Law LL.M. honestly omitted (its rate is published separately by the Law School).

Re-applies ``michigan_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: michtuition1
Revises: ndllmmerge1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "michtuition1"
down_revision = "ndllmmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    michigan_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == michigan_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
