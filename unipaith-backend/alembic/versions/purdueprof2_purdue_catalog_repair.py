"""repair Purdue catalog — disambiguate program names, departments, descriptions

Re-applies ``purdue_profile.apply()`` after the catalog repair that removes CIP×
award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description (no
template stubs). Idempotent; no-op when Purdue is absent.

Revision ID: purdueprof2
Revises: ucsdprof2
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import purdue_profile

revision = "purdueprof2"
down_revision = "ucsdprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    purdue_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
