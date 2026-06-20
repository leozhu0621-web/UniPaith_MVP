"""unify runner + fleet heads

Revision ID: runnermrg1
Revises: 4c82f7423afb, uiucheadmrg1, uwmrg1
Create Date: 2026-06-20

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "runnermrg1"  # pragma: allowlist secret
down_revision: str | None = ("4c82f7423afb", "uiucheadmrg1", "uwmrg1")  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
