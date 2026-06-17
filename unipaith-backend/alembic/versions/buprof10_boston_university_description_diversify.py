"""Boston University description diversify — peer de-contamination + credential suffixes

Re-applies ``bu_profile.apply()`` so credential-sibling programs carry distinct
BU-specific descriptions (0% identical-across-levels), peer-institution
contamination is cleared from field clauses, and program names use real degree
designations instead of credential-prefix stubs.

Revision ID: buprof10
Revises: uwmadisonprof6
Create Date: 2026-06-17
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import bu_profile

revision = "buprof10"
down_revision = "uwmadisonprof6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bu_profile.apply(Session(bind=bind))


def downgrade() -> None:
    pass
