"""JHU published graduate-tier tuition backfill.

Clears Johns Hopkins's acute matcher-core defect (REPAIR_BACKLOG run 74 HIGH #2): the
244-program catalog filled the uniform undergrad sticker (bachelor's 100%) but shipped
every graduate tier at null (master's 0/95, certificate 0/84, PhD 0/4). Every program
now carries a JHU-published 2025-26 tuition figure from the Academic Catalogue cost-of-
attendance tables; funded research doctorates stamp tuition 0 with the published sticker
recorded in the note (funding is a separate signal).

Re-applies ``jhu_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: jhutuition1
Revises: jhubumrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "jhutuition1"
down_revision = "jhubumrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    jhu_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == jhu_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
