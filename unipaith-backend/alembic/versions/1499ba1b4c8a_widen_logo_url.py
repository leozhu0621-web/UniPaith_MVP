"""widen logo_url to 2000 chars

Revision ID: 1499ba1b4c8a
Revises: c461832c7e39
Create Date: 2026-04-15 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '1499ba1b4c8a'
down_revision: str = 'c461832c7e39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('institutions', 'logo_url',
                    existing_type=sa.String(1000),
                    type_=sa.String(2000))


def downgrade() -> None:
    op.alter_column('institutions', 'logo_url',
                    existing_type=sa.String(2000),
                    type_=sa.String(1000))
