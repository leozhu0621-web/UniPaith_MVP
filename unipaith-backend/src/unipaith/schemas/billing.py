"""Billing schemas (Spec 07 §4, 21 §2.7/§3.6)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SubscriptionStatus = Literal["trialing", "active", "canceled", "expired"]


class InvoiceItem(BaseModel):
    id: str
    date: datetime
    amount_usd: float
    status: Literal["paid", "due", "upcoming"]
    description: str


class StudentBillingResponse(BaseModel):
    status: SubscriptionStatus
    plan_price_usd: int
    ad_free: bool
    ad_free_addon_usd: int
    monthly_total_usd: int
    trial_ends_at: datetime | None = None
    trial_days_left: int | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    has_payment_method: bool = False
    payment_method_brand: str | None = None
    payment_method_last4: str | None = None
    # Derived access: True while the student should have premium surfaces.
    is_premium: bool = True
    paywall_enforced: bool = False
    invoices: list[InvoiceItem] = []
    # Active payment provider ("mock" | "stripe") + the client-safe publishable
    # key (present only in stripe mode) so the UI knows whether to capture the
    # card with Stripe Elements.
    provider: str = "mock"
    publishable_key: str | None = None


class AdFreeRequest(BaseModel):
    enabled: bool


class UpgradeRequest(BaseModel):
    """Optional payload for /upgrade. In stripe mode the client sends the
    tokenized card (Stripe Elements ``pm_...``); the mock needs no body."""

    payment_method_token: str | None = None


class InstitutionBillingResponse(BaseModel):
    per_applicant_usd: int
    cycle_label: str
    cycle_start: datetime
    cycle_end: datetime
    applicants_processed: int
    current_charge_usd: float
    has_payment_method: bool = False
    payment_method_brand: str | None = None
    payment_method_last4: str | None = None
    invoices: list[InvoiceItem] = []
