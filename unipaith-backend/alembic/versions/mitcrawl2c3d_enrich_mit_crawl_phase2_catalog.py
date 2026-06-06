"""enrich MIT profile from crawl — phase 2 (full program catalog)

Data-only migration (no DDL). Re-applies the updated canonical MIT profile so
the expanded program catalog — additional degree programs plus online,
non-degree credentials (MicroMasters and professional certificates, carrying
``delivery_format``) — lands on deploy. ``apply()`` is idempotent and no-ops
when MIT is absent.

Revision ID: mitcrawl2c3d
Revises: mitcrawl1a2b
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl2c3d"
down_revision = "mitcrawl1a2b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
