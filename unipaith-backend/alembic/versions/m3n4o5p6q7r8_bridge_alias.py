"""bridge alias for renamed widen_logo_url migration

Production DB has alembic_version = 'm3n4o5p6q7r8' from a deploy where the
widen_logo_url migration was named with that ID. The migration was later
renamed (twice) and is now '1499ba1b4c8a'. Without a file matching
'm3n4o5p6q7r8', alembic cannot resolve the DB's current revision and
crashes on every container start.

This file is a no-op bridge: it represents the same DDL as the renamed
migration, with no-op upgrade (because the widen already happened in any
DB that has this revision_id), and re-points the chain so DBs at this
revision can roll forward to '1499ba1b4c8a'.

Revision ID: m3n4o5p6q7r8
Revises: c461832c7e39
Create Date: 2026-04-15 20:00:00.000000

"""
from typing import Sequence, Union


# revision identifiers
revision: str = 'm3n4o5p6q7r8'
down_revision: str = 'c461832c7e39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: any DB that ever had this revision recorded already had
    # institutions.logo_url widened to String(2000). The chain continues
    # at 1499ba1b4c8a which we now re-point to depend on this revision.
    pass


def downgrade() -> None:
    pass
