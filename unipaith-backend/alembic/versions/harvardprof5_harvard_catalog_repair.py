"""repair Harvard catalog — disambiguate program names, departments, campus gallery

Re-applies ``harvard_profile.apply()`` after the catalog repair that removes
bare-abbr and CIP×award-level padding: every program now carries a
credential-disambiguated ``program_name``, a real ``department``, and a
field-specific description. Adds a verified 5-photo campus gallery and
external reviews for additional coverable programs. Idempotent; no-op when
Harvard University is absent.

Revision ID: harvardprof5
Revises: buprof2
Create Date: 2026-06-14
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import harvard_profile

revision = "harvardprof5"
down_revision = "buprof2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    harvard_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
