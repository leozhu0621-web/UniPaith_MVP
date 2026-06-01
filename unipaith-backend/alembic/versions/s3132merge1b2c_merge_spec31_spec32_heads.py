"""merge spec 31 admissions-intake + spec 32 review-workspace heads

Spec 31 (b31a1c2d3e4f) and Spec 32 (a32revwork1b2c) branched independently off
a3029merge1b2c and merged to main concurrently, leaving two alembic heads. This
empty merge revision rejoins them so `alembic upgrade head` has a single target
(test_alembic_has_single_head gates the backend deploy).

Revision ID: s3132merge1b2c
Revises: b31a1c2d3e4f, a32revwork1b2c
Create Date: 2026-06-01 14:05:00.000000
"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "s3132merge1b2c"  # pragma: allowlist secret
down_revision: str | Sequence[str] | None = (
    "b31a1c2d3e4f",  # pragma: allowlist secret
    "a32revwork1b2c",  # pragma: allowlist secret
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """No-op: pure head merge."""


def downgrade() -> None:
    """No-op: pure head merge."""
