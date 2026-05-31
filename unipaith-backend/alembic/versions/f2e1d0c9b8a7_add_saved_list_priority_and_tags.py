"""add saved_list_items.priority and saved_list_items.tags

Spec 13 (Saved List) §4.2 / §4.3 — closes gap G-S5. Priority on a saved
program was previously ``useState`` / localStorage-only on the client and was
wiped on refresh. This persists it server-side, plus a free-text ``tags`` array
(the student's own tag dictionary).

Both columns are added idempotently (guarded by an inspector check) so the
revision is a no-op on a dev DB built via ``create_all`` or already migrated —
matching the house pattern (the parent revision uses the same guards). This
keeps ``alembic upgrade heads`` safe in the prod entrypoint even when the
target DB's alembic state is divergent.

Revision ID: f2e1d0c9b8a7
Revises: a1f7c93d2e64
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f2e1d0c9b8a7"  # pragma: allowlist secret
down_revision = "a1f7c93d2e64"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(c["name"] == column for c in insp.get_columns(table))
    except Exception:
        return False


def _has_table(bind, table: str) -> bool:
    insp = sa.inspect(bind)
    return insp.has_table(table)


def upgrade() -> None:
    bind = op.get_bind()

    # Nothing to do if the table itself doesn't exist yet (a minimal/divergent
    # dev DB) — create_all / a later sync migration will build it with these
    # columns already present from the model.
    if not _has_table(bind, "saved_list_items"):
        return

    # priority — considering | planning_to_apply | applied | dropped.
    if not _has_column(bind, "saved_list_items", "priority"):
        op.add_column(
            "saved_list_items",
            sa.Column(
                "priority",
                sa.String(length=20),
                nullable=False,
                server_default="considering",
            ),
        )

    # tags — free-text tag array (the student's own tag dictionary).
    if not _has_column(bind, "saved_list_items", "tags"):
        op.add_column(
            "saved_list_items",
            sa.Column(
                "tags",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "saved_list_items", "tags"):
        op.drop_column("saved_list_items", "tags")
    if _has_column(bind, "saved_list_items", "priority"):
        op.drop_column("saved_list_items", "priority")
