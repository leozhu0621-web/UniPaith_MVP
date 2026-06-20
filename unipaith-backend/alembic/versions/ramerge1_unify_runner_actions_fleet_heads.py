"""unify runner-actions + fleet heads

Revision ID: ramerge1
Revises: nyuprof4, uiucuwmrg1
Create Date: 2026-06-20

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ramerge1"  # pragma: allowlist secret
down_revision: str | None = ("nyuprof4", "uiucuwmrg1")  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
