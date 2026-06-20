"""Harvard per-credential description repair (REPAIR BACKLOG HIGH #6).

Replaces ``_level_body`` (ONE shared field clause behind per-credential frames —
68 fields failed the frame-stripped shared-body gate live) with sibling-aware
``_assign_descriptions`` so each credential level carries its own researched body
(gold MIT = 0% frame-stripped shared body). Re-applies ``harvard_profile.apply()``
and re-derives program-preference rows.

Revision ID: harvardpercred1
Revises: ramerge1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "harvardpercred1"
down_revision = "ramerge1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    harvard_profile.apply(session)
    session.flush()
    inst = session.scalar(
        select(Institution).where(Institution.name == harvard_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
