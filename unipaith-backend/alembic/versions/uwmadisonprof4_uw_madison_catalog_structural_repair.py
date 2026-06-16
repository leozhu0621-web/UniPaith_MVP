"""UW-Madison catalog structural repair — de-fabricate IPEDS template stubs

Replaces 96% ``program_description`` template rows with field-specific descriptions,
maps CIP rollup titles to real UW-Madison degree names and owning departments, and
re-applies ``uw_madison_profile.apply()``.

Revision ID: uwmadisonprof4
Revises: jhuprof4
Create Date: 2026-06-16
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import uw_madison_profile

revision = "uwmadisonprof4"
down_revision = "jhuprof4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    uw_madison_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
