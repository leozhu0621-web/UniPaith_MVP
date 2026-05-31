"""Billing / monetization models (Spec 06 §4).

The student model is a 7-day full-access trial (card-on-file auto-convert) →
``$15/mo`` "UniPaith Plus", with an optional ``$5/mo`` ad-free upgrade. The
institution model is ``$15`` per *unique* applicant processed.

Money is always stored as integer cents. Plan/status are plain ``String``
columns (matching ``applications.status``) — validated by the service layer
against the constants below — to avoid Postgres ENUM migration churn.

All rows are written behind ``settings.billing_enabled``; when that flag is
False the billing service is a no-op and these tables stay empty, so the rest
of the platform is unaffected.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base

# --- Plan / status vocabularies (validated in the service layer) ---------------

# A subscription plan is the *tier* the account is entitled to.
PLAN_TRIAL = "trial"  # inside the 7-day full-access window
PLAN_FREE = "free"  # trial lapsed without a card → freemium tier
PLAN_PLUS = "plus"  # paying $15/mo
SUBSCRIPTION_PLANS = (PLAN_TRIAL, PLAN_FREE, PLAN_PLUS)

# Status mirrors the payment lifecycle (Stripe-compatible vocabulary).
STATUS_TRIALING = "trialing"
STATUS_ACTIVE = "active"
STATUS_PAST_DUE = "past_due"
STATUS_CANCELED = "canceled"
STATUS_FREE = "free"
SUBSCRIPTION_STATUSES = (
    STATUS_TRIALING,
    STATUS_ACTIVE,
    STATUS_PAST_DUE,
    STATUS_CANCELED,
    STATUS_FREE,
)

# Billing-event ledger types (the §7 telemetry substrate: MRR, conversions,
# institution revenue all derive from this append-only stream).
EVENT_TRIAL_STARTED = "trial_started"
EVENT_TRIAL_CONVERTED = "trial_converted"
EVENT_SUBSCRIPTION_CREATED = "subscription_created"
EVENT_SUBSCRIPTION_CANCELED = "subscription_canceled"
EVENT_PAYMENT_SUCCEEDED = "payment_succeeded"
EVENT_PAYMENT_FAILED = "payment_failed"
EVENT_PAYMENT_METHOD_ADDED = "payment_method_added"
EVENT_ADFREE_ENABLED = "adfree_enabled"
EVENT_ADFREE_DISABLED = "adfree_disabled"
EVENT_APPLICANT_CHARGED = "applicant_charged"


class Subscription(Base):
    """One row per account (student). Holds the trial window, plan, and the
    optional ad-free upgrade. Institutions bill per-applicant, not per-seat, so
    they do not get a Subscription row."""

    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    plan: Mapped[str] = mapped_column(String(20), default=PLAN_TRIAL, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=STATUS_TRIALING, nullable=False)

    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ad_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    provider: Mapped[str] = mapped_column(String(20), default="mock", nullable=False)
    provider_customer_id: Mapped[str | None] = mapped_column(String(255))
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    payment_methods: Mapped[list[PaymentMethod]] = relationship(
        "PaymentMethod",
        primaryjoin="Subscription.user_id == foreign(PaymentMethod.user_id)",
        viewonly=True,
    )


class PaymentMethod(Base):
    """Card-on-file metadata only — never the PAN/CVC. The provider holds the
    real instrument; we keep brand + last4 + expiry for display."""

    __tablename__ = "payment_methods"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(20), default="mock", nullable=False)
    provider_payment_method_id: Mapped[str | None] = mapped_column(String(255))
    brand: Mapped[str | None] = mapped_column(String(30))
    last4: Mapped[str | None] = mapped_column(String(4))
    exp_month: Mapped[int | None] = mapped_column(Integer)
    exp_year: Mapped[int | None] = mapped_column(Integer)
    is_default: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class BillingEvent(Base):
    """Append-only ledger of every billing-relevant event. Source of truth for
    cost/revenue dashboards (Spec 06 §7) and compliance (Spec 43 §7). Either
    ``user_id`` (student events) or ``institution_id`` (institution events) is
    set, never assume both."""

    __tablename__ = "billing_events"
    __table_args__ = (
        Index("ix_billing_events_user_type", "user_id", "event_type"),
        Index("ix_billing_events_institution_type", "institution_id", "event_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="usd", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="succeeded", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(20))
    provider_ref: Mapped[str | None] = mapped_column(String(255))
    # Renamed from `metadata` (reserved on the SQLAlchemy declarative Base).
    event_metadata: Mapped[dict | None] = mapped_column(JSONB)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InstitutionApplicantCharge(Base):
    """The ``$15`` per *unique* applicant processed (Spec 06 §4.2). Uniqueness is
    enforced on ``(institution_id, student_id)`` so an applicant who applies to
    three programs at one institution is billed once."""

    __tablename__ = "institution_applicant_charges"
    __table_args__ = (
        UniqueConstraint(
            "institution_id", "student_id", name="uq_applicant_charge_institution_student"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # The application that first triggered the charge (nullable for resilience).
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="SET NULL")
    )
    amount_cents: Mapped[int] = mapped_column(Integer, default=1500, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="usd", nullable=False)
    # pending → charged (mock auto-charges) | invoiced (billed in arrears).
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    provider: Mapped[str | None] = mapped_column(String(20))
    provider_ref: Mapped[str | None] = mapped_column(String(255))
    charged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
