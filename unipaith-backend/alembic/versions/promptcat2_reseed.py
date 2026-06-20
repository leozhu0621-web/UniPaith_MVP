"""prompt_catalog reseed — clear seed-managed rows so the expanded 23→40
catalog re-materialises on next startup via CatalogService.ensure_seeded.

Rows with an airtable_record_id are NOT touched (they came from Airtable,
not from the seed, so we preserve any operator edits).

Revision ID: promptcat2
Revises: bupromptmerge1
Create Date: 2026-06-20

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "promptcat2"  # pragma: allowlist secret
down_revision: str | None = "bupromptmerge1"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has(table: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table)


def upgrade() -> None:
    if not _has("prompt_catalog"):
        return
    op.execute("DELETE FROM prompt_catalog WHERE airtable_record_id IS NULL")


def downgrade() -> None:
    # intentional no-op: seed-managed rows are re-materialized from CATALOG on next
    # startup by ensure_seeded; nothing to reverse.
    pass
