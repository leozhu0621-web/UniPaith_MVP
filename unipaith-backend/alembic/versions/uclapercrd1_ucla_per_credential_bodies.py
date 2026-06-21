"""UCLA per-credential description repair (REPAIR BACKLOG HIGH #3).

Replaces catalogue frame + ONE shared field body across credential siblings (67 fields
failed the frame-stripped shared-body gate live) with sibling-aware
``_assign_descriptions`` so each credential level carries its own researched or
level-specific body (gold MIT = 0%). Re-applies ``ucla_profile.apply()`` and
re-derives program-preference rows.

Revision ID: uclapercrd1
Revises: uclaheadmrg1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucla_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uclapercrd1"
down_revision = "uclaheadmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    ucla_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == ucla_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
