"""Spec 23 (Program editor): program promotion_categories

Adds ``programs.promotion_categories`` (JSONB, nullable) — the set of
promoted-placement categories a program opts into (Spec 23 §2.8). The actual
promoted campaigns/auction live in Spec 25 (``promotions``); this column is just
the program's declared participation set, edited in the program editor.

Guarded with has_column so it is a safe no-op against a dev/test DB that was
built from the models via ``create_all``.

Revision ID: e7a1c4d9b230
Revises: e4f5a6b7c8d9
Create Date: 2026-05-31

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "e7a1c4d9b230"  # pragma: allowlist secret
# Rebased onto the Spec-20 auto-follow migration (the post-rebase head) so the
# chain stays linear — both this and e4f5a6b7c8d9 originally sat on c20c7a1f9e30.
down_revision = "e4f5a6b7c8d9"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(bind, table: str, column: str) -> bool:
    insp = sa.inspect(bind)
    try:
        return any(c["name"] == column for c in insp.get_columns(table))
    except Exception:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_column(bind, "programs", "promotion_categories"):
        op.add_column(
            "programs",
            sa.Column("promotion_categories", postgresql.JSONB(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if _has_column(bind, "programs", "promotion_categories"):
        op.drop_column("programs", "promotion_categories")
