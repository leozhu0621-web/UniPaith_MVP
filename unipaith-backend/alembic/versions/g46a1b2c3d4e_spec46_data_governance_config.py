"""Spec 46 §9/§10 — institution data-governance config.

Adds ``institutions.data_governance`` (JSONB) — the per-institution governance
settings (override-expiry default, protected-attributes-tracked, no-training
tier, data residency) behind the /i/settings?tab=data surface. Layers on top of
Spec 46 §6 (``f46a1b2c3d4e``, the fairness auto-halt engine) which already added
the fairness tables + program halt columns.

Guarded add so the migration is a safe no-op against a dev/test DB built from the
models via ``create_all`` (conftest path).

Revision ID: g46a1b2c3d4e
Revises: f46a1b2c3d4e
Create Date: 2026-06-02

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "g46a1b2c3d4e"  # pragma: allowlist secret
down_revision = "f46a1b2c3d4e"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("institutions", "data_governance"):
        op.add_column(
            "institutions",
            sa.Column("data_governance", postgresql.JSONB(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("institutions", "data_governance"):
        op.drop_column("institutions", "data_governance")
