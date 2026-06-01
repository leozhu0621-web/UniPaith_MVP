"""Spec 39 (Fees & Payments): payments table + institution payment_config.

Additive only:

1. **Creates ``payments``** — one row per ``(application_id, kind)`` (the unique
   constraint is the idempotency key, Spec 39 §4). Tracks an application fee or
   enrollment deposit through the provider lifecycle. No card data is stored —
   only provider charge / session IDs + status (PCI, Spec 39 §4).

2. **Adds ``institutions.payment_config`` (JSONB, nullable)** — the fee/deposit/
   waiver config edited at ``/i/settings?tab=billing`` (Spec 39 §2.1). NULL = no
   fee, no deposit.

Chains off ``s3637merge1c2d`` (the Spec 36+37 merge head) so the graph stays a
single linear head (``test_alembic_has_single_head`` gates the backend deploy).
Both operations are guarded so the revision is a safe no-op against a dev/test
DB built from the models via ``create_all``.

Revision ID: s39a1b2c3d4e
Revises: s3637merge1c2d
Create Date: 2026-06-01

"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "s39a1b2c3d4e"  # pragma: allowlist secret
down_revision = "s3637merge1c2d"  # pragma: allowlist secret
branch_labels = None
depends_on = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(name: str) -> bool:
    return name in _inspector().get_table_names()


def _has_column(table: str, column: str) -> bool:
    if not _has_table(table):
        return False
    return column in {c["name"] for c in _inspector().get_columns(table)}


def upgrade() -> None:
    if not _has_table("payments"):
        op.create_table(
            "payments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("kind", sa.String(length=24), nullable=False),
            sa.Column("amount_cents", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(length=3), nullable=False),
            sa.Column("status", sa.String(length=24), server_default="none", nullable=False),
            sa.Column("provider", sa.String(length=20), nullable=False),
            sa.Column("provider_charge_id", sa.String(length=255), nullable=True),
            sa.Column("provider_session_id", sa.String(length=255), nullable=True),
            sa.Column("waiver_requested", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("waiver_basis", sa.String(length=50), nullable=True),
            sa.Column("waiver_approved", sa.Boolean(), nullable=True),
            sa.Column("waiver_decided_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("waiver_decided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("waiver_evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("refunded_cents", sa.Integer(), server_default="0", nullable=False),
            sa.Column("refund_reason", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["waiver_decided_by"], ["users.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("application_id", "kind", name="uq_payment_application_kind"),
        )
        op.create_index("ix_payments_application_id", "payments", ["application_id"])

    if _has_table("institutions") and not _has_column("institutions", "payment_config"):
        op.add_column(
            "institutions",
            sa.Column("payment_config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )


def downgrade() -> None:
    if _has_column("institutions", "payment_config"):
        op.drop_column("institutions", "payment_config")
    if _has_table("payments"):
        op.drop_index("ix_payments_application_id", table_name="payments")
        op.drop_table("payments")
