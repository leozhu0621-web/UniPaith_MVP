"""Payment model (Spec 39 — Fees & Payments).

One row per ``(application_id, kind)`` — the unique constraint *is* the
idempotency key (Spec 39 §4): a retry reuses the row, so a fee or deposit can
never be double-charged. The row tracks an application fee or an enrollment
deposit through the provider lifecycle.

PCI (Spec 39 §4): we **never** store raw card data — only provider charge /
session IDs + status. ``tests/test_spec39_fees_payments.py`` asserts no
card-bearing column exists on this table.

Money is stored in **minor units** (``amount_cents``) — Stripe-native and
float-drift-free; the API exposes whole-currency amounts.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base

# Payment kinds — what the charge is for.
PAYMENT_KINDS = ("application_fee", "enrollment_deposit")

# Lifecycle status (Spec 39 §6).
PAYMENT_STATUSES = (
    "none",  # configured but nothing started
    "pending",  # checkout session open / awaiting confirmation
    "paid",
    "waived",  # fee waived by the institution (application_fee only)
    "refunded",
    "partially_refunded",
    "failed",
)


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        # The idempotency key (Spec 39 §4) — one payment per application + kind.
        UniqueConstraint("application_id", "kind", name="uq_payment_application_kind"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # 'application_fee' | 'enrollment_deposit'
    kind: Mapped[str] = mapped_column(String(24), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, server_default="none", default="none"
    )

    # Provider seam (Spec 39 §4) — mirrors the model-portability pattern. We only
    # ever persist provider identifiers + status, never card data (PCI).
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="mock")
    provider_charge_id: Mapped[str | None] = mapped_column(String(255))
    provider_session_id: Mapped[str | None] = mapped_column(String(255))

    # Fee-waiver workflow (Spec 39 §2.2 / §2.3) — applies to application fees.
    waiver_requested: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false", default=False
    )
    waiver_basis: Mapped[str | None] = mapped_column(String(50))
    # None = undecided / pending; True = approved; False = denied.
    waiver_approved: Mapped[bool | None] = mapped_column(Boolean)
    waiver_decided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    waiver_decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Free-form supporting evidence + decision notes, e.g.
    # {"note": str, "url": str, "decision_note": str}.
    waiver_evidence: Mapped[dict | None] = mapped_column(JSONB)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refunded_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0", default=0
    )
    refund_reason: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
