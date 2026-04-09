"""merge_heads

Revision ID: d6cc531e526f
Revises: 0789102fcf9e, i9j0k1l2m3n4
Create Date: 2026-04-09 17:20:08.372145

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6cc531e526f'
down_revision: Union[str, None] = ('0789102fcf9e', 'i9j0k1l2m3n4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
