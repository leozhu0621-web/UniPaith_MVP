"""merge profile intelligence and concurrent catalog repair heads

Revision ID: deepintelmerge1
Revises: deepintel1, michaimrg1, colaivisamerge1
Create Date: 2026-06-20
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "deepintelmerge1"
down_revision: str | Sequence[str] | None = (
    "deepintel1",
    "michaimrg1",
    "colaivisamerge1",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
