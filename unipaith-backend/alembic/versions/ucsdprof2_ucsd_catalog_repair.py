"""repair UC San Diego catalog — disambiguate program names, departments, descriptions

Re-applies ``ucsd_profile.apply()`` after the catalog repair that removes CIP×
award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description (no
template stubs). Idempotent; no-op when UCSD is absent.

Revision ID: ucsdprof2
Revises: uwmadprof1
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import ucsd_profile

revision = "ucsdprof2"
down_revision = "uwmadprof1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    ucsd_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
