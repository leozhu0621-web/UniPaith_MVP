"""Purdue published graduate-tier tuition backfill.

Clears Purdue's acute matcher-core defect (REPAIR_BACKLOG run 76 HIGH #3):
the 172-program catalog filled the uniform in-state undergraduate sticker
(bachelor's 100%) but shipped the graduate tiers nearly null (master's 0/68,
professional 0/2). Each program now carries a Purdue-published Indiana-resident
tuition figure from the Bursar graduate / PharmD / Vet Med schedules, with
school differentials for Engineering, Daniels Business, Polytechnic, and SLP.

Re-applies ``purdue_profile.apply()`` (idempotent) and re-derives
program-preference rows.

Revision ID: purduetuition1
Revises: nyutuition1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "purduetuition1"
down_revision = "nyutuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    purdue_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == purdue_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
