"""per-program concentrations / degree tracks

Data-only migration (no DDL). Re-applies the canonical MIT profile so programs
that offer them get real concentrations / degree tracks (e.g. EECS 6-1/6-2/6-3,
MechE 2/2-A/2-OE, Math pure/applied/18-C, Sloan MBA certificates), filling the
program page's concentrations section. Idempotent; no-ops when MIT is absent.

Revision ID: mitcrawl9z0a
Revises: mitcrawl8y9z
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl9z0a"
down_revision = "mitcrawl8y9z"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
