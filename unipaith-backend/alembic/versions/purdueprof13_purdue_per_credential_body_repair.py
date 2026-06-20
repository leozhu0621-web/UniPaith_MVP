"""Purdue per-credential body repair — clear frame+tail-share evasion

Re-applies ``purdue_profile.apply()`` after replacing the shared DISCIPLINE_DEFS
encyclopedia clause (prepended with a credential frame) with structurally distinct,
credential-keyed bodies for every program (REPAIR_BACKLOG #2 — 51/51 multi-credential
fields shared an ≥80-char body after frame-strip). Derives program-preference rows
for the program -> student match.

Revision ID: purdueprof13
Revises: nwrebuild1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "purdueprof13"
down_revision = "nwrebuild1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    if purdue_profile.apply(session):
        inst = session.scalar(
            select(Institution).where(Institution.name == purdue_profile.INSTITUTION_NAME)
        )
        if inst is not None:
            backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
