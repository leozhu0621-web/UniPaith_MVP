"""Duke structural repair — field-specific program descriptions

Re-applies ``duke_profile.apply()`` after replacing 102 classification-only
program descriptions with field-specific clauses from ``duke_field_descriptions.py``.
Idempotent; no-op when Duke is absent.

Revision ID: dukeprof5
Revises: material_ingest_a1b2
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import duke_profile

revision = "dukeprof5"
down_revision = "material_ingest_a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    duke_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
