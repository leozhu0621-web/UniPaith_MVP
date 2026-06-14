"""repair Princeton catalog — disambiguate program names, departments, descriptions

Re-applies ``princeton_profile.apply()`` after the catalog repair that removes
null-department rows and duplicate bare field names: every program now carries
a credential-disambiguated ``program_name``, a real ``department``, and a
field-specific description. Persists ``department`` on every program row.
Idempotent; no-op when Princeton is absent.

Revision ID: princetonprof4
Revises: yaleprof3
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import princeton_profile

revision = "princetonprof4"
down_revision = "yaleprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    princeton_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
