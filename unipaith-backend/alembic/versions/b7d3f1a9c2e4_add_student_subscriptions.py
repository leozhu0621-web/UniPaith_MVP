"""Add student_subscriptions (Spec 07 §4.1 / 21 §2.7).

Backs the platform's own student subscription billing: a 7-day full-access
trial that auto-converts to the $15/mo plan when a card is on file, plus the
optional $5/mo ad-free upgrade. One row per user. Institution usage billing
($15/unique applicant, Spec 07 §4.2) is computed from the pipeline, so it
needs no table.

Revision ID: b7d3f1a9c2e4
Revises: a6c1f0d2e3b4
Create Date: 2026-05-30 22:50:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "b7d3f1a9c2e4"  # pragma: allowlist secret
down_revision = "a6c1f0d2e3b4"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_subscriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Allowed values: 'trialing' | 'active' | 'canceled' | 'expired'
        sa.Column("status", sa.String(20), nullable=False, server_default="trialing"),
        sa.Column("trial_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ad_free", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "cancel_at_period_end",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("provider", sa.String(20), nullable=False, server_default="mock"),
        sa.Column("provider_customer_id", sa.String(255), nullable=True),
        sa.Column("provider_subscription_id", sa.String(255), nullable=True),
        sa.Column("payment_method_brand", sa.String(40), nullable=True),
        sa.Column("payment_method_last4", sa.String(4), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('trialing','active','canceled','expired')",
            name="ck_student_subscriptions_status",
        ),
        sa.UniqueConstraint("user_id", name="uq_student_subscriptions_user"),
    )


def downgrade() -> None:
    op.drop_table("student_subscriptions")
