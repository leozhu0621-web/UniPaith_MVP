"""merge three heads into one

Revision ID: e30b7734a1fe
Revises: 4c9d6e1a8b3f, 4c9e5f3a8b2d, e57f26412cb2
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union


revision: str = "e30b7734a1fe"
down_revision: Union[str, Sequence[str], None] = (
    "4c9d6e1a8b3f",
    "4c9e5f3a8b2d",
    "e57f26412cb2",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
