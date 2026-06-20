"""Michigan per-credential description repair (REPAIR BACKLOG HIGH #5).

Replaces catalogue frame + ONE shared field body across credential siblings (67 fields
failed the frame-stripped shared-body gate live) with sibling-aware
``_assign_descriptions`` so each credential level carries its own researched or
level-specific body (gold MIT = 0%). Re-applies ``michigan_profile.apply()`` and
re-derives program-preference rows.

Revision ID: michpercrd1
Revises: columbiapercred1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import michigan_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "michpercrd1"
down_revision = "columbiapercred1"
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
