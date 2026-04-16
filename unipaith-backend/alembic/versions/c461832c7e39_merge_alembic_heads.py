"""merge alembic heads

Revision ID: c461832c7e39
Revises: 5690fbaea71f, m3n4o5p6q7r8
Create Date: 2026-04-14 00:58:36.214245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c461832c7e39'
down_revision: Union[str, None] = ('5690fbaea71f', 'm3n4o5p6q7r8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
