"""Add priority column to saved_list_items.

Saved-list priority (considering/planning/applied/dropped) was previously
held in frontend useState — wiped on refresh (gap audit G-S5). This adds
the column so SavedListPage can PATCH it and re-read it on load.

Revision ID: p7q8r9s0t1u2
Revises: f1a9c0d2e3b4
Create Date: 2026-05-30 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "p7q8r9s0t1u2"  # pragma: allowlist secret
down_revision: str | None = "f1a9c0d2e3b4"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Idempotent on purpose: the e4a5b6c7d8e9 "sync_all_missing_columns" migration
# adds any model column missing from the DB via ADD COLUMN IF NOT EXISTS, so on
# a fresh DB `priority` already exists by the time this runs. On an incremental
# (production) DB the sync ran before the model gained `priority`, so this adds
# it. Either way we converge to: NOT NULL, default 'considering', check present.


def upgrade() -> None:
    op.execute("ALTER TABLE saved_list_items ADD COLUMN IF NOT EXISTS priority VARCHAR(20)")
    op.execute("UPDATE saved_list_items SET priority = 'considering' WHERE priority IS NULL")
    op.execute("ALTER TABLE saved_list_items ALTER COLUMN priority SET DEFAULT 'considering'")
    op.execute("ALTER TABLE saved_list_items ALTER COLUMN priority SET NOT NULL")
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_constraint "
        "WHERE conname = 'ck_saved_list_items_priority') THEN "
        "ALTER TABLE saved_list_items ADD CONSTRAINT ck_saved_list_items_priority "
        "CHECK (priority IN ('considering', 'planning', 'applied', 'dropped')); "
        "END IF; END $$;"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE saved_list_items DROP CONSTRAINT IF EXISTS ck_saved_list_items_priority"
    )
    op.execute("ALTER TABLE saved_list_items DROP COLUMN IF EXISTS priority")
