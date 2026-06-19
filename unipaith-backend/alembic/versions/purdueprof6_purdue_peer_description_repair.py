"""Remove cross-institution-copy peer signatures from Purdue program descriptions.

Re-applies purdue_profile after purdue_field_descriptions.py was rewritten with
verified Purdue-only college/department clauses (REPAIR_BACKLOG #3, purdueprof6).

Revision ID: purdueprof6
Revises: progprefbf1
Create Date: 2026-06-19
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile

revision = "purdueprof6"
down_revision = "progprefbf1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    purdue_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
