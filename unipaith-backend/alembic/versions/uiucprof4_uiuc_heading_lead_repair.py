"""Repair the UIUC catalogue descriptions #763 shipped with a malformed CourseLeaf
"for the <credential> in <field> …" subtitle prepended (80 of 419 rows, ~19%) plus a
handful of admissions/referral stubs. Each affected row is replaced with degree-strict
re-matched catalog prose or verified department-page prose; re-applies the profile.

Revision ID: uiucprof4
Revises: uiucprof3
Create Date: 2026-06-18
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uiuc_profile

revision = "uiucprof4"
down_revision = "uiucprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = Session(bind=op.get_bind())
    uiuc_profile.apply(session)
    session.flush()


def downgrade() -> None:
    pass
