"""widen logo_url to 2000 chars

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2026-04-15 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = 'a1b2c3d4e5f6'
down_revision: str = 'l2m3n4o5p6q7'
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
