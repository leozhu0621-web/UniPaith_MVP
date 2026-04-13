"""merge_conversation_sessions_and_pipeline_index

Revision ID: 350fe6cc8c5e
Revises: 0ebebb7c82a4, 7fa321c6e551
Create Date: 2026-04-13 22:23:30.663262

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '350fe6cc8c5e'
down_revision: Union[str, None] = ('0ebebb7c82a4', '7fa321c6e551')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
