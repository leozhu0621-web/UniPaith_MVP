"""Cornell per-credential description repair (REPAIR BACKLOG HIGH #8).

Cornell's ``_cornell_level_body`` appended a generic credential tail after ONE shared
field clause from ``FIELD_DESCRIPTIONS`` — the run-68 dilution evasion that left 44 fields
failing ``frame_stripped_shared_body(..., abs_chars=150)`` live. ``_assign_descriptions``
now gives each credential level its own researched or level-specific body (gold MIT = 0%).
Re-applies ``cornell_profile.apply()`` and re-derives program-preference rows.

Revision ID: cornellpercrd2
Revises: stanfordpercrd2
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import cornell_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cornellpercrd2"
down_revision = "stanfordpercrd2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    cornell_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == cornell_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
