"""UW Seattle per-credential bodies — clear frame-stripped shared field definitions

University of Washington-Seattle's catalog carried generic Wikipedia-style field
definitions behind credential frames ("Graduate study.", "Doctoral research.") so
77 multi-credential fields still shared a body after frame-strip (REPAIR BACKLOG
#4 / miss #8). This re-applies ``uw_profile.apply()`` with UW-specific field
clauses, distinct per-credential sibling bodies, collapsed Education PhD
concentration splits into ``tracks`` on ``uw-education-phd``, and idempotent
``backfill_program_preferences``. Gold MIT = 0% frame-stripped shared body.

Revision ID: uwpercred1
Revises: uiucbslas1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwpercred1"
down_revision = "uiucbslas1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    uw_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uw_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
