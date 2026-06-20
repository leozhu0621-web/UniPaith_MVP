"""Rice per-credential bodies — drop credential-frame + tail-shared field body (REPAIR BACKLOG #3)

The ``ricedefab1`` pass left a single ``FIELD_DESCRIPTIONS`` clause stamped behind a
swapped credential frame, so a field's BA / MS / PhD rows still shared one body in the
description TAIL (the run-65 credential-frame + tail-shared field body, miss #8). This
migration re-applies ``rice_profile.apply()`` with a distinct per-(field, degree_type)
body for every multi-credential field (what THAT degree studies at THAT level) and the
redundant "Rice offers the … in {field}." classification lead dropped — gold MIT = 0%
frame-stripped shared body. Idempotent (``replace=True``); re-derives target-applicant
rows for the matcher.

Revision ID: ricepercred1
Revises: purduerebuild1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ricepercred1"
down_revision = "purduerebuild1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    rice_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == rice_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
