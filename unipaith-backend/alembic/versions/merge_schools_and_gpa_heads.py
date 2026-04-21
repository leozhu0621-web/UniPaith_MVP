"""merge schools and gpa heads

Revision ID: merge_schools_gpa
Revises: a1b2c3schools, 4c9e5f3a8b2d
Create Date: 2026-04-21 10:00:00.000000

"""
from typing import Sequence, Union


revision: str = "merge_schools_gpa"
down_revision: Union[str, None] = ("a1b2c3schools", "4c9e5f3a8b2d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
