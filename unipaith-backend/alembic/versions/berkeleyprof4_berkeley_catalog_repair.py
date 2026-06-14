"""repair Berkeley catalog — disambiguate program names, departments, descriptions

Re-applies ``berkeley_profile.apply()`` after the catalog repair that removes
CIP×award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description.
Also adds a verified 5-photo campus gallery. Idempotent; no-op when Berkeley is
absent.

Revision ID: berkeleyprof4
Revises: cornellprof4
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import berkeley_profile

revision = "berkeleyprof4"
down_revision = "cornellprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    berkeley_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
