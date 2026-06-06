"""enrich MIT profile — program tuition (undergrad rate + funded PhDs)

Data-only migration (no DDL). Re-applies the canonical MIT profile so the new
per-program tuition logic (undergrads = MIT's published rate, PhDs = 0/funded,
others null) lands on deploy. ``apply()`` is idempotent and no-ops when MIT is
absent.

Revision ID: mitcrawl4t5u
Revises: mitcrawl3e4f
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl4t5u"
down_revision = "mitcrawl3e4f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
