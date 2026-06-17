"""repair Penn catalog — disambiguate program names, departments, descriptions

Re-applies ``penn_profile.apply()`` after the catalog repair that removes
CIP×award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description.
Also adds a verified 5-photo campus gallery and persists ``department`` on every
program row. Idempotent; no-op when Penn is absent.

Revision ID: pennprof6
Revises: columbiaprof6
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import penn_profile

revision = "pennprof6"
down_revision = "columbiaprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    penn_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
