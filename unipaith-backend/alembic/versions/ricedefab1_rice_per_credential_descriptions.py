"""Rice per-credential descriptions + conferred UG names (REPAIR BACKLOG #4)

Resolves Rice's 43% verbatim-across-levels defect and bare-field / dept-echo
undergraduate names: every row carries a conferred designation, a real owning
department (never ``program_name`` echoed verbatim), and a credential-specific
description lead so BA/MS/PhD siblings no longer share a leading body (gold
MIT/JHU = 0% verbatim / shared-leading-body). Re-applies ``rice_profile.apply()``
and re-derives target-applicant rows for the matcher.

Revision ID: ricedefab1
Revises: chatsessbf1
Create Date: 2026-06-20
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import rice_profile
from unipaith.models.institution import Institution
from unipaith.services.match.derive_preferences import backfill_program_preferences

revision = "ricedefab1"
down_revision = "chatsessbf1"
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
