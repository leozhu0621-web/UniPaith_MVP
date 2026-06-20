"""merge headfix2 + uiucbslas1

Revision ID: 4c82f7423afb
Revises: headfix2, uiucbslas1
Create Date: 2026-06-20 15:04:53.864035

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "4c82f7423afb"  # pragma: allowlist secret
down_revision: str | None = ("headfix2", "uiucbslas1")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
