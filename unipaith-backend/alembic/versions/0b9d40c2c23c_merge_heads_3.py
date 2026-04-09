"""merge_heads_3

Revision ID: 0b9d40c2c23c
Revises: 51c72506f2d4, k1l2m3n4o5p6
Create Date: 2026-04-09 17:42:49.880569

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b9d40c2c23c'
down_revision: Union[str, None] = ('51c72506f2d4', 'k1l2m3n4o5p6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
