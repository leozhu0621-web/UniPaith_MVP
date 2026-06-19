"""Re-apply Purdue gold-standard profile after the dual-head merge.

Production still ships 310 programs with peer-copy descriptions (Chesapeake,
SAS, Writing Seminars) because ``purduedefab1`` never ran while ``schol1a2b3c4d``
landed alone. This idempotently re-applies the de-fabricated catalog (286 real
programs, verified per-credential descriptions, 0 peer signatures).

Revision ID: purdueprof12
Revises: purduescholmerge1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "purdueprof12"
down_revision = "purduescholmerge1"
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
