"""drop crawler tables (program crawler removed)

The program-data crawler subsystem was removed (no platform-admin app,
no crawler). The program library is now sourced from institution Data
Upload / direct creation, so the crawler staging/job tables are dropped.

Revision ID: f1a9c0d2e3b4
Revises: e4a5b6c7d8e9
Create Date: 2026-05-22
"""

from alembic import op

revision = "f1a9c0d2e3b4"  # pragma: allowlist secret
down_revision = "e4a5b6c7d8e9"  # pragma: allowlist secret
branch_labels = None
depends_on = None

# Drop order is irrelevant with IF EXISTS + CASCADE; listed dependents first.
_CRAWLER_TABLES = (
    "enrichment_records",
    "extracted_programs",
    "crawl_schedules",
    "source_url_patterns",
    "crawl_jobs",
)


def upgrade() -> None:
    for table in _CRAWLER_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")


def downgrade() -> None:
    # The crawler subsystem was removed; these tables are intentionally
    # not recreated. Restore from the pre-removal revision if ever needed.
    pass
