"""student_profile_timeline_events table (spec 10 §14, §22.8).

Persists profile change events (form saves, consent changes) that the
computed milestone feed can't derive from row created_at.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "profiletimeline01"
down_revision = "profilemerge01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_profile_timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="profile"),
        sa.Column("ref_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_profile_timeline_student_time",
        "student_profile_timeline_events",
        ["student_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_profile_timeline_student_time",
        table_name="student_profile_timeline_events",
    )
    op.drop_table("student_profile_timeline_events")
