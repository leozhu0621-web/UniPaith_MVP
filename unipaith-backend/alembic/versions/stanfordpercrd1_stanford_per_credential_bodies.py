"""Stanford per-credential description repair (REPAIR BACKLOG HIGH #6).

Stanford's catalogue builder prepended credential frames onto ONE shared discipline-
definition body across credential siblings — the run-68 evasion that left 51 fields
failing the frame-stripped shared-body gate live (``frame_stripped_shared_body(...,
abs_chars=150)``). ``_assign_descriptions`` now gives each credential level its own
researched or level-specific body (gold MIT = 0%). Re-applies ``stanford_profile.apply()``
and re-derives program-preference rows.

Revision ID: stanfordpercrd1
Revises: ufpercrd1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "stanfordpercrd1"
down_revision = "ufpercrd1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    stanford_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == stanford_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
