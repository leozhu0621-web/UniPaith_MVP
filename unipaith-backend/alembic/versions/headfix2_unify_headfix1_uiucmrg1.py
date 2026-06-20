"""unify headfix1 + uiucmrg1

Revision ID: headfix2
Revises: headfix1, uiucmrg1
Create Date: 2026-06-20

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "headfix2"  # pragma: allowlist secret
down_revision: str | None = ("headfix1", "uiucmrg1")  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
