"""spec 06 — billing tables + consent_training

Adds the monetization layer (Spec 06 §4): per-account ``subscriptions`` with the
7-day trial + optional ad-free upgrade, card-on-file ``payment_methods``, the
append-only ``billing_events`` ledger, the per-unique-applicant
``institution_applicant_charges``, and the 4th consent lever
``student_data_consent.consent_training`` (Spec 43 §2 / 06 §4.3).

Written idempotently: a fresh DB has these created by the metadata-sync
migration (``d3f4a5b6c7d8``) before this runs, so each step is guarded by an
inspector existence check. On an already-deployed DB at the prior head the
guards fire and the objects are created here.

Revision ID: a6f1b2c3d4e5
Revises: p3q5r7s9t1u3
Create Date: 2026-05-30 19:25:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a6f1b2c3d4e5"  # pragma: allowlist secret
down_revision: str | None = "p3q5r7s9t1u3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def _has_column(inspector, table: str, column: str) -> bool:
    if table not in inspector.get_table_names():
        return False
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "subscriptions"):
        op.create_table(
            "subscriptions",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("plan", sa.String(20), nullable=False, server_default="trial"),
            sa.Column("status", sa.String(20), nullable=False, server_default="trialing"),
            sa.Column("trial_started_at", sa.DateTime(timezone=True)),
            sa.Column("trial_ends_at", sa.DateTime(timezone=True)),
            sa.Column("current_period_start", sa.DateTime(timezone=True)),
            sa.Column("current_period_end", sa.DateTime(timezone=True)),
            sa.Column("ad_free", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column(
                "cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
            sa.Column("canceled_at", sa.DateTime(timezone=True)),
            sa.Column("provider", sa.String(20), nullable=False, server_default="mock"),
            sa.Column("provider_customer_id", sa.String(255)),
            sa.Column("provider_subscription_id", sa.String(255)),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.UniqueConstraint("user_id", name="uq_subscriptions_user_id"),
        )
        op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])

    if not _has_table(inspector, "payment_methods"):
        op.create_table(
            "payment_methods",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("provider", sa.String(20), nullable=False, server_default="mock"),
            sa.Column("provider_payment_method_id", sa.String(255)),
            sa.Column("brand", sa.String(30)),
            sa.Column("last4", sa.String(4)),
            sa.Column("exp_month", sa.Integer()),
            sa.Column("exp_year", sa.Integer()),
            sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_payment_methods_user_id", "payment_methods", ["user_id"])

    if not _has_table(inspector, "billing_events"):
        op.create_table(
            "billing_events",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE")),
            sa.Column(
                "institution_id",
                UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            ),
            sa.Column("event_type", sa.String(40), nullable=False),
            sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(10), nullable=False, server_default="usd"),
            sa.Column("status", sa.String(20), nullable=False, server_default="succeeded"),
            sa.Column("provider", sa.String(20)),
            sa.Column("provider_ref", sa.String(255)),
            sa.Column("event_metadata", JSONB()),
            sa.Column(
                "occurred_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )
        op.create_index("ix_billing_events_user_id", "billing_events", ["user_id"])
        op.create_index("ix_billing_events_institution_id", "billing_events", ["institution_id"])
        op.create_index("ix_billing_events_user_type", "billing_events", ["user_id", "event_type"])
        op.create_index(
            "ix_billing_events_institution_type",
            "billing_events",
            ["institution_id", "event_type"],
        )

    if not _has_table(inspector, "institution_applicant_charges"):
        op.create_table(
            "institution_applicant_charges",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "institution_id",
                UUID(as_uuid=True),
                sa.ForeignKey("institutions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "student_id",
                UUID(as_uuid=True),
                sa.ForeignKey("student_profiles.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "application_id",
                UUID(as_uuid=True),
                sa.ForeignKey("applications.id", ondelete="SET NULL"),
            ),
            sa.Column("amount_cents", sa.Integer(), nullable=False, server_default="1500"),
            sa.Column("currency", sa.String(10), nullable=False, server_default="usd"),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("provider", sa.String(20)),
            sa.Column("provider_ref", sa.String(255)),
            sa.Column("charged_at", sa.DateTime(timezone=True)),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
            sa.UniqueConstraint(
                "institution_id",
                "student_id",
                name="uq_applicant_charge_institution_student",
            ),
        )
        op.create_index(
            "ix_institution_applicant_charges_institution_id",
            "institution_applicant_charges",
            ["institution_id"],
        )
        op.create_index(
            "ix_institution_applicant_charges_student_id",
            "institution_applicant_charges",
            ["student_id"],
        )

    if not _has_column(inspector, "student_data_consent", "consent_training"):
        # server_default false backfills existing rows; the column is NOT NULL
        # to match the model. Leave the default in place — harmless and keeps
        # raw SQL inserts valid.
        op.add_column(
            "student_data_consent",
            sa.Column(
                "consent_training",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_column(inspector, "student_data_consent", "consent_training"):
        op.drop_column("student_data_consent", "consent_training")
    for table in (
        "institution_applicant_charges",
        "billing_events",
        "payment_methods",
        "subscriptions",
    ):
        if _has_table(inspector, table):
            op.drop_table(table)
