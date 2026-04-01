"""add training run metadata fields

Revision ID: b8d4e2a1c9f0
Revises: 9f2b1d3c4a10
Create Date: 2026-04-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b8d4e2a1c9f0"
down_revision: Union[str, Sequence[str], None] = "9f2b1d3c4a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("training_runs", sa.Column("mode", sa.String(length=16), nullable=True))
    op.add_column("training_runs", sa.Column("trigger_reason", sa.String(length=120), nullable=True))
    op.add_column("training_runs", sa.Column("new_outcomes_count", sa.Integer(), nullable=True))
    op.add_column("training_runs", sa.Column("data_window_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column("training_runs", sa.Column("data_window_end", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE training_runs SET mode = 'full' WHERE mode IS NULL")
    op.alter_column("training_runs", "mode", nullable=False)


def downgrade() -> None:
    op.drop_column("training_runs", "data_window_end")
    op.drop_column("training_runs", "data_window_start")
    op.drop_column("training_runs", "new_outcomes_count")
    op.drop_column("training_runs", "trigger_reason")
    op.drop_column("training_runs", "mode")
