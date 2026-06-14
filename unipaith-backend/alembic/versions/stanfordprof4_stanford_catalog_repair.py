"""repair Stanford catalog — disambiguate program names, departments, descriptions

Re-applies ``stanford_profile.apply()`` after the catalog repair that removes
CIP×award-level padding: every program now carries a credential-disambiguated
``program_name``, a real ``department``, and a field-specific description.
Also routes content_sources through verified server-fetchable RSS (law.stanford.edu)
and persists ``department`` on every program row. Idempotent; no-op when Stanford
is absent.

Revision ID: stanfordprof4
Revises: pennprof6
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof4"
down_revision = "pennprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    stanford_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
