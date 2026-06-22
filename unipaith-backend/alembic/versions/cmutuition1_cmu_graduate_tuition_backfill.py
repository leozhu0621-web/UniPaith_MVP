"""CMU published graduate-tier tuition backfill.

Clears Carnegie Mellon's acute matcher-core defect (REPAIR_BACKLOG run 75 HIGH #3):
the 180-program catalog filled the uniform undergrad sticker (bachelor's 100%) but
shipped the graduate tiers nearly null (master's 1/99, PhD partially filled). Every
program now carries a CMU-published 2026-27 tuition figure from Student Financial
Services college/program tables; funded research doctorates stamp tuition 0 with the
published sticker recorded in the note.

Re-applies ``carnegie_mellon_profile.apply()`` (idempotent) and re-derives
program-preference rows.

Revision ID: cmutuition1
Revises: bucornmrg1
Create Date: 2026-06-22
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import carnegie_mellon_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "cmutuition1"
down_revision = "bucornmrg1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    carnegie_mellon_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == carnegie_mellon_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
