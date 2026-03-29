"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2026-03-29

Creates all 45 Phase 1 tables via metadata.create_all.
Requires the pgvector extension to be installed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from unipaith.models import Base

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
