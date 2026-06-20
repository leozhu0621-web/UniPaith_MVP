"""UW-Madison per-credential bodies — drop credential-frame + tail-shared field body

The ``uwmaddefab1`` pass left a shared FIELD_DESCRIPTIONS clause behind swapped
credential leads, so 109 multi-credential fields still shared a body once the frame
was stripped (REPAIR BACKLOG #5 / miss #8). This migration re-applies
``uw_madison_profile.apply()`` with distinct per-credential ``_level_body`` text after
each field's verified clause (gold MIT = 0% frame-stripped shared body). Idempotent;
re-derives target-applicant rows.

Revision ID: uwmadpercred1
Revises: ufdefab1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwmadpercred1"
down_revision = "ufdefab1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uw_madison_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == uw_madison_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
