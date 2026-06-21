"""UW-Madison published tuition backfill for graduate tiers.

Clears Wisconsin's acute matcher-core defect (REPAIR_BACKLOG run 74 HIGH #2): the catalog
filled the uniform undergrad sticker (bachelor's 100%) but shipped every graduate tier at
null (certificate 0/129, master's 0/107, professional 0/4). Every program now carries a
UW-published 2025-26 tuition & fees figure from the Office of Student Financial Aid cost-
of-attendance tables; funded research doctorates at tuition 0.

Re-applies ``uw_madison_profile.apply()`` (idempotent) and re-derives program-preference rows.

Revision ID: uwmadtuition1
Revises: buconc1
Create Date: 2026-06-21
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile
from unipaith.models import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "uwmadtuition1"
down_revision = "buconc1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uw_madison_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(Institution.name == uw_madison_profile.INSTITUTION_NAME)
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
