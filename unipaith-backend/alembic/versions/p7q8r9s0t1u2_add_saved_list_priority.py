"""Add priority column to saved_list_items.

Saved-list priority (considering/planning/applied/dropped) was previously
held in frontend useState — wiped on refresh (gap audit G-S5). This adds
the column so SavedListPage can PATCH it and re-read it on load.

Revision ID: p7q8r9s0t1u2
Revises: 1499ba1b4c8a
Create Date: 2026-05-30 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "p7q8r9s0t1u2"
down_revision: str | None = "1499ba1b4c8a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


PRIORITY_VALUES = ("considering", "planning", "applied", "dropped")


def upgrade() -> None:
    op.add_column(
        "saved_list_items",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="considering",
        ),
    )
    op.create_check_constraint(
        "ck_saved_list_items_priority",
        "saved_list_items",
        f"priority IN {PRIORITY_VALUES!r}".replace("'", "'"),
    )


def downgrade() -> None:
    op.drop_constraint("ck_saved_list_items_priority", "saved_list_items", type_="check")
    op.drop_column("saved_list_items", "priority")
