"""per-program official admission-requirements baseline

Data-only migration (no DDL). Re-applies the canonical MIT profile so each
program gets an official application-requirements baseline (materials,
test policy, recommendations) by program type — undergrad (institute-wide,
SAT/ACT required), graduate (GRE varies by department), Sloan MBA, and open
online/MicroMasters — each carrying its MIT source. Fills the previously-empty
"Application Requirements" section. Idempotent; no-ops when MIT is absent.

Revision ID: mitcrawl6w7x
Revises: mitcrawl5v6w
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl6w7x"
down_revision = "mitcrawl5v6w"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
