"""merge intake_rounds and missing_model_columns

Revision ID: 0789102fcf9e
Revises: 1b4651702328, h8i9j0k1l2m3
Create Date: 2026-04-09 08:32:13.986153

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0789102fcf9e'
down_revision: Union[str, None] = ('1b4651702328', 'h8i9j0k1l2m3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
