"""MBAn cost-of-attendance breakdown

Data-only migration (no DDL). Re-applies the MIT profile so the MBAn cost_data
carries a `breakdown` (tuition · Capstone subsidy · living) + estimated total,
shown as "what it's made up of" on the Costs tab. Idempotent; no-ops when MIT
is absent.

Revision ID: mbancost1
Revises: intlreq1
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mbancost1"
down_revision = "intlreq1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
