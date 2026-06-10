"""merge feeds backfill + penn heads

Unifies two alembic heads created by concurrent work: feedsbackfill1 (institution
feeds backfill) and pennprof3 (routine's Penn grad/professional programs). Both
branched off pennprof2. Merge-only: no schema or data changes.

Revision ID: feedspennmerge1
Revises: feedsbackfill1, pennprof3
"""

revision = "feedspennmerge1"
down_revision = ("feedsbackfill1", "pennprof3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
