"""JHU catalog structural repair — de-fabricate IPEDS template stubs

Replaces 95% ``program_description`` template rows with field-specific descriptions,
maps CIP rollup titles to real JHU degree names and owning departments, and
re-applies ``jhu_profile.apply()``.

Revision ID: jhuprof4
Revises: northwesternprof3
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import jhu_profile

revision = "jhuprof4"
down_revision = "northwesternprof3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    jhu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
