"""enrich MIT profile from crawl — phase 1 (facts, scale, schools, aid)

Data-only migration (no DDL). Re-applies the updated canonical MIT profile
(``unipaith.data.mit_profile``) so the crawl-enriched figures — corrected
enrollment/admit rate, the new institutional ``scale`` block, deeper financial
aid, national-medal recognition, and refreshed school descriptions — land in
every environment on deploy. ``apply()`` is idempotent and no-ops when MIT is
absent, so this is safe on fresh/CI databases.

Revision ID: mitcrawl1a2b
Revises: ud2scovery3c4d
"""

from sqlalchemy.orm import Session

from alembic import op
from unipaith.data import mit_profile

revision = "mitcrawl1a2b"
down_revision = "ud2scovery3c4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    mit_profile.apply(Session(bind=op.get_bind()))


def downgrade() -> None:
    # Data-only, idempotent enrichment; no structural rollback.
    pass
