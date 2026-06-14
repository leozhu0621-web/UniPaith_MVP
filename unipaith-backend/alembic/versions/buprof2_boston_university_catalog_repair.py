"""repair Boston University catalog — disambiguate program names, departments, descriptions

Re-applies ``bu_profile.apply()`` after the catalog repair that removes bare-abbr
and CIP×award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description (no
template stubs). Idempotent; no-op when Boston University is absent.

Revision ID: buprof2
Revises: nwuprof2
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof2"
down_revision = "nwuprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
