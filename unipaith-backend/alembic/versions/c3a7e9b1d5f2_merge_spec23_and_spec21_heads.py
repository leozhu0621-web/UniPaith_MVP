"""merge the Spec-23 program-editor head with the Spec-21 settings head

Two heads landed on main from concurrently-merged PRs:
  - e7a1c4d9b230  — Spec 23: programs.promotion_categories
  - f7820e695151  — Spec 21/20: merge of spec-20 peers + spec-21 settings heads

The branches touch disjoint tables (Spec 23 only adds a column to ``programs``;
the Spec-21/20 chain touches settings / peers tables and never references
``programs``), so the merge is collision-free and carries no DDL of its own.
This restores a single head so ``alembic upgrade head`` works for deploys and
``test_alembic_has_single_head`` passes.

Revision ID: c3a7e9b1d5f2
Revises: e7a1c4d9b230, f7820e695151
Create Date: 2026-05-31

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "c3a7e9b1d5f2"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = (
    "e7a1c4d9b230",  # pragma: allowlist secret
    "f7820e695151",  # pragma: allowlist secret
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
