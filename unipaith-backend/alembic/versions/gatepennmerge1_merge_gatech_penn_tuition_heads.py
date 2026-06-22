"""merge gatech + penn graduate tuition heads

Unifies two alembic heads created by concurrent repair PRs: gatechgradtuition1
(Georgia Tech graduate-tier tuition) and penntuition1 (Penn graduate-tier tuition).
Both branched off harvardcip2. Merge-only: no schema or data changes.

Revision ID: gatepennmerge1
Revises: gatechgradtuition1, penntuition1
"""

revision = "gatepennmerge1"
down_revision = ("gatechgradtuition1", "penntuition1")
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
