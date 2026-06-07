"""richer per-program descriptions + application deadlines

Data-only migration (no DDL). Re-applies the canonical MIT profile so major
programs get a richer 2-sentence description and every program gets an
application deadline by type (undergrad Regular Action Jan 1, Sloan MBA round,
graduate ~Dec 15, online/certificate none). Idempotent; no-ops when MIT absent.

Revision ID: mitcrawla0b1
Revises: mitcrawl9z0a
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawla0b1"
down_revision = "mitcrawl9z0a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
