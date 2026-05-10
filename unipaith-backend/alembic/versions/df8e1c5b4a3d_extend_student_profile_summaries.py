"""Phase A — extend student_profiles with summary columns.

Adds two columns the Phase B UI reads on the home page without joining:

  discovery_completion  jsonb  {profile, goals, needs, identity} 0..1
  strategy_active_id    uuid   FK student_strategies.id  ON DELETE SET NULL

Both are kept fresh by service-layer hooks: DiscoveryService writes
discovery_completion when a session completes; StrategyService writes
strategy_active_id when activate() runs (and clears it via SET NULL when
the active strategy is deleted, which can also happen when a CASCADE drops
a student).

Revision ID: df8e1c5b4a3d
Revises: ce7d9f4a3b2c
Create Date: 2026-05-10 09:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "df8e1c5b4a3d"  # pragma: allowlist secret
down_revision = "ce7d9f4a3b2c"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column(
            "discovery_completion",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "student_profiles",
        sa.Column(
            "strategy_active_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_strategies.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_student_profiles_strategy_active",
        "student_profiles",
        ["strategy_active_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_student_profiles_strategy_active", table_name="student_profiles")
    op.drop_column("student_profiles", "strategy_active_id")
    op.drop_column("student_profiles", "discovery_completion")
