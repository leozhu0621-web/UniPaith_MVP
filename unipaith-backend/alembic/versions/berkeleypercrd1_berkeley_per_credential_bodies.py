"""Berkeley per-credential description repair (REPAIR BACKLOG HIGH #4).

Replaces credential-frame + ONE shared FIELD_DESCRIPTIONS body across credential
siblings (64 fields failed the frame-stripped shared-body gate live) with sibling-aware
``_assign_descriptions`` so each credential level carries its own researched or
level-specific body (gold MIT = 0%). Re-applies ``berkeley_profile.apply()`` and
re-derives program-preference rows.

Revision ID: berkeleypercrd1
Revises: uclareapply1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "berkeleypercrd1"
down_revision = "uclareapply1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    berkeley_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == berkeley_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
