"""Notre Dame per-credential description repair (REPAIR BACKLOG HIGH #7).

Notre Dame's ``_description`` stamped ONE shared ``DISCIPLINE_DEFS`` clause across
credential siblings — the run-72 evasion that left 23 fields failing
``frame_stripped_shared_body(..., abs_chars=150)`` live. ``_assign_descriptions``
now gives each credential level its own researched or level-specific body (gold MIT = 0%).
Re-applies ``notre_dame_profile.apply()`` and re-derives program-preference rows.

Revision ID: ndpercrd1
Revises: cornellpercrd2
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import notre_dame_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ndpercrd1"
down_revision = "utaustintuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    notre_dame_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == notre_dame_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
