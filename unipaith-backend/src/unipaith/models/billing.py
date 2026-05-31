"""Billing / monetization models (Spec 07 §4, 21 §2.7).

Student subscription state: a 7-day full-access trial that auto-converts to a
$15/mo plan when a card is on file (Spec 07 §4.1). Institution usage billing
($15/unique applicant, Spec 07 §4.2) is computed on the fly from the pipeline,
so it needs no table here.

MVP scope per Spec 21 §2.7 is "plan state + manage link" — the real charge
movement is a Phase-2 detail (Spec 39, Stripe). Provider defaults to ``mock``.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from unipaith.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudentSubscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One row per student. Status drives access + the trial→paywall gate.

    status:
      - ``trialing``  — inside the 7-day full-access trial.
      - ``active``    — paying $15/mo (card on file).
      - ``canceled``  — cancel scheduled; access continues until period end.
      - ``expired``   — trial lapsed (no card) or canceled period ended → gated.
    """

    __tablename__ = "student_subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="trialing")

    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ad_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Payment provider — abstracted behind PaymentProvider (Spec 39 §4).
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="mock")
    provider_customer_id: Mapped[str | None] = mapped_column(String(255))
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255))
    payment_method_brand: Mapped[str | None] = mapped_column(String(40))
    payment_method_last4: Mapped[str | None] = mapped_column(String(4))

    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship("User")  # type: ignore[name-defined]  # noqa: F821
