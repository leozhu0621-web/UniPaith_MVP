"""merge spec-03 audit-ledger head with the table-sync head

Two heads diverged from ac252aa411c3:
  - n9p2q4r6s8t0  — spec 03 audit-ledger fields + match_rationales.prompt_version
  - f1a9c0d2e3b4  — table-sync chain (create missing tables, sync columns,
                    drop crawler tables)

The branches touch disjoint tables (spec 03 only adds columns to ai_turns /
match_rationales; the table-sync chain never references them), so the merge is
collision-free and carries no DDL of its own. This restores a single head so
`alembic upgrade head` works for deploys.

Revision ID: p3q5r7s9t1u3
Revises: n9p2q4r6s8t0, f1a9c0d2e3b4
Create Date: 2026-05-30 17:45:00.000000
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "p3q5r7s9t1u3"
down_revision: str | Sequence[str] | None = ("n9p2q4r6s8t0", "f1a9c0d2e3b4")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
