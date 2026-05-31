"""Spec 13 — saved_list_items priority, tags, status.

Revision ID: b3c4d5e6f7a8
Revises: a1f7c93d2e64
Create Date: 2026-05-31 12:00:00.000000

"""

from alembic import op

revision = "b3c4d5e6f7a8"  # pragma: allowlist secret
down_revision = "a1f7c93d2e64"  # pragma: allowlist secret
branch_labels = None
depends_on = None

_PRIORITY_CHECK = "priority IN ('considering','planning_to_apply','applied','dropped')"
_STATUS_CHECK = (
    "status IN ('considering','application_started','submitted',"
    "'accepted','rejected','waitlisted','dropped')"
)


def _add_column_if_missing(table: str, column: str, ddl: str) -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_name = '{table}'
          ) AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = '{table}' AND column_name = '{column}'
          ) THEN
            ALTER TABLE {table} ADD COLUMN {ddl};
          END IF;
        END $$;
        """
    )


def upgrade() -> None:
    _add_column_if_missing(
        "saved_list_items",
        "priority",
        "priority VARCHAR(30) NOT NULL DEFAULT 'considering'",
    )
    _add_column_if_missing(
        "saved_list_items",
        "status",
        "status VARCHAR(30) NOT NULL DEFAULT 'considering'",
    )
    _add_column_if_missing(
        "saved_list_items",
        "tags",
        "tags JSONB NOT NULL DEFAULT '[]'::jsonb",
    )
    op.execute(
        f"""
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_saved_list_items_priority'
          ) THEN
            ALTER TABLE saved_list_items
              ADD CONSTRAINT ck_saved_list_items_priority
              CHECK ({_PRIORITY_CHECK});
          END IF;
        END $$;
        """
    )
    op.execute(
        f"""
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'ck_saved_list_items_status'
          ) THEN
            ALTER TABLE saved_list_items
              ADD CONSTRAINT ck_saved_list_items_status
              CHECK ({_STATUS_CHECK});
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE saved_list_items DROP CONSTRAINT IF EXISTS ck_saved_list_items_status")
    op.execute(
        "ALTER TABLE saved_list_items DROP CONSTRAINT IF EXISTS ck_saved_list_items_priority"
    )
    for col in ("tags", "status", "priority"):
        op.execute(
            f"""
            DO $$
            BEGIN
              IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'saved_list_items' AND column_name = '{col}'
              ) THEN
                ALTER TABLE saved_list_items DROP COLUMN {col};
              END IF;
            END $$;
            """
        )
