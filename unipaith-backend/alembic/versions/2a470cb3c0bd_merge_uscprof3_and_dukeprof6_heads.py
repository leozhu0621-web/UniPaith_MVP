"""merge uscprof3 and dukeprof6 heads

Revision ID: 2a470cb3c0bd
Revises: uscprof3, dukeprof6
Create Date: 2026-06-18 12:41:36.428598

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a470cb3c0bd'
down_revision: Union[str, None] = ('uscprof3', 'dukeprof6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
