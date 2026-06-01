"""merge spec24 data-upload + spec25 campaigns heads

Revision ID: e9f0a1b2c3d4
Revises: c25a1b2c3d4e, f24da7a0c1b3
Create Date: 2026-05-31 21:43:20.394903

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "e9f0a1b2c3d4"  # pragma: allowlist secret
down_revision: str | None = ("c25a1b2c3d4e", "f24da7a0c1b3")  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
