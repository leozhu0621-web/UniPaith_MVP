"""Spec 30 — Institution Setup (first-run wizard).

Adds the gating + resume state for the ``/i/setup`` onboarding wizard:
- ``institutions.setup_complete`` (§2/§4): gates the forced-onboarding redirect
  and the dimmed-nav state until profile + first program are published.
- ``institutions.setup_state`` (§5): JSONB persisting wizard progress so the flow
  is resumable — ``{step, steps_complete{profile,program,data,team}, skipped, first_program_id}``.

Chains onto the single head (``f27e5a1c0d34`` Spec 27), keeping one linear head
(``test_alembic_has_single_head``). Every op is guarded with ``_has_column`` so the
revision is a safe no-op against a dev/test DB built from the models via ``create_all``.

Revision ID: f30a1b2c3d45
Revises: f27e5a1c0d34
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "f30a1b2c3d45"  # pragma: allowlist secret
down_revision = "f27e5a1c0d34"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    try:
        return column in {c["name"] for c in insp.get_columns(table)}
    except Exception:
        return False


def _add(table: str, column: sa.Column) -> None:
    if not _has_column(table, column.name):
        op.add_column(table, column)


def _drop(table: str, column: str) -> None:
    if _has_column(table, column):
        op.drop_column(table, column)


def upgrade() -> None:
    _add(
        "institutions",
        sa.Column("setup_complete", sa.Boolean(), server_default="false", nullable=False),
    )
    _add(
        "institutions",
        sa.Column("setup_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    _drop("institutions", "setup_state")
    _drop("institutions", "setup_complete")
