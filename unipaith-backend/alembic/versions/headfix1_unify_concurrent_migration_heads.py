"""unify concurrent migration heads

Revision ID: headfix1
Revises: jhuuscmrg1, sesstmpl1, uiucprof5
Create Date: 2026-06-20

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "headfix1"  # pragma: allowlist secret
down_revision: str | None = ("jhuuscmrg1", "sesstmpl1", "uiucprof5")  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
