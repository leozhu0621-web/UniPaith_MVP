"""merge phase A profile summaries + phase D2 calibrator heads

Revision ID: ac252aa411c3
Revises: d4e5f6a7b8c9, df8e1c5b4a3d
Create Date: 2026-05-10 19:53:04.149484

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ac252aa411c3"
down_revision: str | None = ("d4e5f6a7b8c9", "df8e1c5b4a3d")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
