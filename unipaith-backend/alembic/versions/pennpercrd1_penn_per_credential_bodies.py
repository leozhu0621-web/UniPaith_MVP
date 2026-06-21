"""Penn per-credential description repair (REPAIR BACKLOG HIGH #3).

Penn's ``_level_body`` prepended credential frames onto ONE shared field fact from
``FIELD_DESCRIPTIONS`` across credential siblings — the run-68 evasion that left 51 fields
failing the frame-stripped shared-body gate live (``frame_stripped_shared_body(...,
abs_chars=150)``). ``_assign_descriptions`` now gives each credential level its own
researched or level-specific body (gold MIT = 0%). Re-applies ``penn_profile.apply()`` and
re-derives program-preference rows.

Revision ID: pennpercrd1
Revises: uclaberkmerge1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "pennpercrd1"
down_revision = "uclaberkmerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    penn_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == penn_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
