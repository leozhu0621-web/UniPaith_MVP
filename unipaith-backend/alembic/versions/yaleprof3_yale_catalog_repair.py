"""repair Yale catalog — disambiguate program names, departments, descriptions

Re-applies ``yale_profile.apply()`` after the catalog repair that removes
null-department rows and duplicate bare field names: every program now carries
a credential-disambiguated ``program_name``, a real ``department``, and a
field-specific description. Persists ``department`` on every program row.
Idempotent; no-op when Yale is absent.

Revision ID: yaleprof3
Revises: stanfordprof4
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import yale_profile

revision = "yaleprof3"
down_revision = "stanfordprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    yale_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
