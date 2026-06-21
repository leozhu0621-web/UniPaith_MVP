"""Boston University per-credential bodies + published tuition backfill.

Clears BU's two acute defects (REPAIR_BACKLOG run 73 HIGH #5 / #6):
  1. 23 fields failed ``frame_stripped_shared_body(..., abs_chars=150)`` — credential
     siblings shared one ``FIELD_DESCRIPTIONS`` clause with only a trailing
     ``_level_body`` frame differing. ``_assign_descriptions`` now gives each credential
     its own researched or level-specific body (frame_abs150 23 → 0).
  2. ``tuition`` was null catalog-wide (matcher-core budget-fit starvation). Every program
     now carries a BU-published 2025-26 tuition figure from the Office of Financial
     Assistance cost-of-attendance tables; funded research doctorates at tuition 0.

Re-applies ``bu_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: bupercred2
Revises: cornelltrm1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "bupercred2"
down_revision = "cornelltrm1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    bu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == bu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
