"""UChicago description depth pass — field-specific descriptions for all 109 programs

Replaces classification-only program descriptions with field-specific clauses
from ``chicago_field_descriptions.py`` and re-applies ``chicago_profile.apply()``.

Revision ID: chicagoprof6
Revises: yaleprof6
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import chicago_profile

revision = "chicagoprof6"
down_revision = "yaleprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    chicago_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
