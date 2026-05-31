"""Add mode, target_program_id, input_text, readiness_summary to workshop runs."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "f7a8b9c0d1e2"  # pragma: allowlist secret
down_revision = "b7d1e9f3a2c5"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workshop_feedback_runs",
        sa.Column("mode", sa.String(20), nullable=False, server_default="general"),
    )
    op.add_column(
        "workshop_feedback_runs",
        sa.Column("target_program_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "workshop_feedback_runs",
        sa.Column("input_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "workshop_feedback_runs",
        sa.Column("readiness_summary", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_workshop_feedback_runs_target_program",
        "workshop_feedback_runs",
        "programs",
        ["target_program_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_workshop_feedback_runs_mode",
        "workshop_feedback_runs",
        "mode IN ('general','program_specific')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_workshop_feedback_runs_mode", "workshop_feedback_runs", type_="check")
    op.drop_constraint(
        "fk_workshop_feedback_runs_target_program", "workshop_feedback_runs", type_="foreignkey"
    )
    op.drop_column("workshop_feedback_runs", "readiness_summary")
    op.drop_column("workshop_feedback_runs", "input_text")
    op.drop_column("workshop_feedback_runs", "target_program_id")
    op.drop_column("workshop_feedback_runs", "mode")
