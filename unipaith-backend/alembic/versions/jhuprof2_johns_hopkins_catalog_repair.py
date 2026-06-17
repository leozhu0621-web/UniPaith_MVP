"""repair JHU catalog — disambiguate program names, departments, descriptions

Re-applies ``jhu_profile.apply()`` after the catalog repair that removes CIP×
award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description (no
template stubs). Idempotent; no-op when JHU is absent.

Revision ID: jhuprof2
Revises: purdueprof2
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile

revision = "jhuprof2"
down_revision = "purdueprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    jhu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
