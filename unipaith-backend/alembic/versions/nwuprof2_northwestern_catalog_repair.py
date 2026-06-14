"""repair Northwestern catalog — disambiguate program names, departments, descriptions

Re-applies ``northwestern_profile.apply()`` after the catalog repair that removes
CIP×award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description (no
template stubs). Idempotent; no-op when Northwestern is absent.

Revision ID: nwuprof2
Revises: jhuprof2
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "nwuprof2"
down_revision = "jhuprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    northwestern_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
