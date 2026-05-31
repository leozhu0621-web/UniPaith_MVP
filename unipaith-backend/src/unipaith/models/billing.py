"""Spec 07 (Product Context §4) — student subscription / monetization.

One row per student, created lazily on first read with a 7-day full-access
trial (Product Context §4.1: 7-day trial → $15/mo, card-on-file auto-convert;
optional +$5/mo ad-free). Payment capture is a mock card-on-file stub — only the
card brand + last4 are stored, never a PAN — so a real processor slots in behind
the same fields. Plan/entitlement logic lives in
``services.subscription_service``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from unipaith.models.base import Base


class StudentSubscription(Base):
    __tablename__ = "student_subscriptions"
    __table_args__ = (
        CheckConstraint(
            "plan IN ('free','pro')",
            name="ck_student_subscriptions_plan",
        ),
        CheckConstraint(
            "status IN ('trialing','active','canceled','expired')",
            name="ck_student_subscriptions_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    # free | pro — entitlement tier.
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    # trialing | active | canceled | expired — lifecycle state.
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="trialing")
    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # +$5/mo ad-free add-on (Product Context §4.1).
    ad_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Mock card-on-file — brand + last4 only, NEVER a PAN. Real PSP slots in here.
    card_brand: Mapped[str | None] = mapped_column(String(30))
    card_last4: Mapped[str | None] = mapped_column(String(4))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
