"""Northwestern catalog structural repair — de-fabricate IPEDS template stubs

Replaces 95% ``program_description`` template rows with field-specific descriptions,
maps CIP rollup titles to real Northwestern degree names and owning departments, and
re-applies ``northwestern_profile.apply()``.

Revision ID: northwesternprof3
Revises: ucsdprof4
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import northwestern_profile

revision = "northwesternprof3"
down_revision = "ucsdprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    northwestern_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
