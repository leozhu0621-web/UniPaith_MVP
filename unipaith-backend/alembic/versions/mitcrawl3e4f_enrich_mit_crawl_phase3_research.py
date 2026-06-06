"""enrich MIT profile from crawl — phase 3 (research + campus life)

Data-only migration (no DDL). Re-applies the canonical MIT profile so the new
``research`` (named labs/institutes + areas + industry collaborators) and
``campus_life`` (athletics, arts, residence halls) blocks land on deploy.
``apply()`` is idempotent and no-ops when MIT is absent.

Revision ID: mitcrawl3e4f
Revises: mitcrawl2c3d
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl3e4f"
down_revision = "mitcrawl2c3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
