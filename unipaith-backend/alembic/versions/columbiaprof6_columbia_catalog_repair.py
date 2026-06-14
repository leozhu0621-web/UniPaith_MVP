"""repair Columbia catalog — disambiguate program names, departments, descriptions

Re-applies ``columbia_profile.apply()`` after the catalog repair that removes
CIP×award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description.
Also persists ``department`` on every program row. Idempotent; no-op when
Columbia is absent.

Revision ID: columbiaprof6
Revises: berkeleyprof5
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import columbia_profile

revision = "columbiaprof6"
down_revision = "berkeleyprof5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columbia_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
