"""merge_heads_2

Revision ID: 5254d672d4da
Revises: f3da9591d4a9, j0k1l2m3n4o5
Create Date: 2026-04-09 17:33:03.339011

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5254d672d4da'
down_revision: Union[str, None] = ('f3da9591d4a9', 'j0k1l2m3n4o5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
