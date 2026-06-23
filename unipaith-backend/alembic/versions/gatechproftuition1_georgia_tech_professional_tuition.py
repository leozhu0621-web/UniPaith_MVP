"""Georgia Tech published professional-tier tuition backfill (REPAIR_BACKLOG)

Clears the professional-tier tuition STARVATION: Georgia Tech's bachelor's and
master's tiers were filled but 5 of 8 professional rows were still null (prof
3/8 live). Scheller Executive MBA publishes an inclusive $87,100 total program
fee; GTPE professional master's degrees publish $3,415 per three-credit course
(10 courses = $34,150 total). PhD rows remain funded-omit-with-reason.

Idempotent: re-applies ``georgia_tech_profile.apply()`` and re-derives
program-preference rows.

Revision ID: gatechproftuition1
Revises: dukemstuition1
Create Date: 2026-06-23
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import georgia_tech_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "gatechproftuition1"
down_revision = "dukemstuition1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    session = Session(bind=bind)
    georgia_tech_profile.apply(session)
    inst = session.scalar(
        select(Institution).where(
            Institution.name == georgia_tech_profile.INSTITUTION_NAME
        )
    )
    if inst is not None:
        backfill_program_preferences(session, institution_id=inst.id)
    session.flush()


def downgrade() -> None:
    pass
