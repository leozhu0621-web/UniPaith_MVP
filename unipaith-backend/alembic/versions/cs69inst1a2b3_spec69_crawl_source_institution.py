"""Spec 69 §3 — link a crawl source to an institution (program extraction).

Adds ``crawl_sources.institution_id`` (nullable) so the continuous crawler can
ingest programs it extracts from a source's pages under the right institution.
Additive + nullable, no backfill → safe to apply online. Guarded so it is a
no-op against the conftest ``create_all`` test DB (which already has the column
from the model) and runs incrementally in production from the prior head.

Revision ID: cs69inst1a2b3
Revises: fdbk0a1b2c3d
Create Date: 2026-06-03

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "cs69inst1a2b3"  # pragma: allowlist secret
down_revision = "fdbk0a1b2c3d"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if _has_column("crawl_sources", "institution_id"):
        return
    op.add_column(
        "crawl_sources",
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("crawl_sources", "institution_id")
