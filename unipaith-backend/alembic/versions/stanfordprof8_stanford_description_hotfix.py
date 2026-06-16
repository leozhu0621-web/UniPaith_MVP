"""Stanford field-description hotfix — correct peer-adaptation leaks

Fixes Chemical Engineering (College of Chemistry) and GSE teacher-education
clauses corrupted by bad Harvard→Stanford regex adaptation (Harvardsylvania).

Revision ID: stanfordprof8
Revises: stanfordprof7
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import stanford_profile

revision = "stanfordprof8"
down_revision = "stanfordprof7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    stanford_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
