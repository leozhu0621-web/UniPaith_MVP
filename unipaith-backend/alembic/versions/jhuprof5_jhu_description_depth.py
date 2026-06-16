"""JHU description depth pass — field-specific descriptions + final coverable reviews

Replaces classification-only program descriptions with field-specific clauses,
drops fabricated Pre-Medicine IPEDS rows, adds Carey MS Business Analytics review,
and re-applies ``jhu_profile.apply()``.

Revision ID: jhuprof5
Revises: uwmadisonprof4
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile

revision = "jhuprof5"
down_revision = "uwmadisonprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    jhu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
