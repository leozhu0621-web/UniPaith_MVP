"""add student_subscriptions

Spec 07 (Product Context §4) — per-student monetization: 7-day trial → $15/mo
Pro, optional +$5/mo ad-free, mock card-on-file. One row per student.

Revision ID: q5s7u9w1y3a5
Revises: p3q5r7s9t1u3
Create Date: 2026-05-30 21:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "q5s7u9w1y3a5"
down_revision = "p3q5r7s9t1u3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # On fresh installs the metadata catch-up migration (d3f4a5b6c7d8) already
    # creates this table from Base.metadata; only create it where it is missing
    # (e.g. environments migrated before this model existed). Idempotent.
    bind = op.get_bind()
    if sa.inspect(bind).has_table("student_subscriptions"):
        return
    op.create_table(
        "student_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ad_free", sa.Boolean(), nullable=False),
        sa.Column("card_brand", sa.String(30), nullable=True),
        sa.Column("card_last4", sa.String(4), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("plan IN ('free','pro')", name="ck_student_subscriptions_plan"),
        sa.CheckConstraint(
            "status IN ('trialing','active','canceled','expired')",
            name="ck_student_subscriptions_status",
        ),
        sa.UniqueConstraint("student_id", name="uq_student_subscriptions_student_id"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("student_subscriptions"):
        op.drop_table("student_subscriptions")
