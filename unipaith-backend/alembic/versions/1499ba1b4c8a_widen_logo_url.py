"""widen logo_url to 2000 chars

Revision ID: 1499ba1b4c8a
Revises: m3n4o5p6q7r8
Create Date: 2026-04-15 20:00:00.000000

Note: down_revision points to m3n4o5p6q7r8 (no-op bridge alias) so that
prod DBs which have alembic_version='m3n4o5p6q7r8' (from a deploy where
this same migration was named with that ID) can roll forward cleanly.
The bridge alias chains back to c461832c7e39, preserving the full chain
for fresh DBs.

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
    # Idempotent: if a prior deploy already widened to String(2000) under the
    # m3n4o5p6q7r8 revision id, this ALTER COLUMN is a no-op in PostgreSQL.
    op.alter_column('institutions', 'logo_url',
                    existing_type=sa.String(1000),
                    type_=sa.String(2000))


def downgrade() -> None:
    op.alter_column('institutions', 'logo_url',
                    existing_type=sa.String(2000),
                    type_=sa.String(1000))
