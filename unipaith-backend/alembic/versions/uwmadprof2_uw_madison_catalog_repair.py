"""repair UW-Madison catalog — disambiguate program names, departments, descriptions

Re-applies ``uw_madison_profile.apply()`` after the catalog repair that removes
CIP×award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description.
Idempotent; no-op when University of Wisconsin-Madison is absent.

Revision ID: uwmadprof2
Revises: harvardprof5
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile

revision = "uwmadprof2"
down_revision = "harvardprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    uw_madison_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
