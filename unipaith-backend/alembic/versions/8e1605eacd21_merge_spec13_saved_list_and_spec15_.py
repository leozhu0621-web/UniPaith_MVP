"""merge spec13 saved-list and spec15 application-workspace heads

Two migrations branched off the same parent (``a1f7c93d2e64``) on main —
``f2e1d0c9b8a7`` (Spec 13 saved_list_items.priority + tags) and
``b2cc633aba88`` (Spec 15 application-workspace fields). This no-op merge
rejoins them so the lineage has a single head again.

Revision ID: 8e1605eacd21
Revises: b2cc633aba88, f2e1d0c9b8a7
Create Date: 2026-05-31

"""

from __future__ import annotations

# revision identifiers, used by Alembic.
revision = "8e1605eacd21"  # pragma: allowlist secret
down_revision = ("b2cc633aba88", "f2e1d0c9b8a7")  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
