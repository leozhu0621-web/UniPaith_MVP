"""Northwestern per-credential descriptions (REPAIR BACKLOG #6)

Replaces suffix-diversifier stamping with per-credential description leads so
BA/MS/PhD siblings no longer share a ≥120-char leading body (gold MIT = 0%
shared-leading-body). Re-applies ``northwestern_profile.apply()`` and re-derives
target-applicant rows for the matcher.

Revision ID: nwdefab1
Revises: uwmaddefab1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "nwdefab1"
down_revision = "uwmaddefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    northwestern_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == northwestern_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
