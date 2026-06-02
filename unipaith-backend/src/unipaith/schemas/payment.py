"""Payment request schemas (Spec 39 — Fees & Payments).

Views (cost tracker, waiver queue, payments list) are returned as plain dicts
from ``PaymentService`` — mirroring the enrollment endpoints — so only request
bodies are typed here.
"""

from __future__ import annotations

from pydantic import BaseModel


class RequestWaiverRequest(BaseModel):
    # One of services.payments.config.WAIVER_BASES.
    basis: str
    note: str | None = None
    evidence_url: str | None = None


class WaiverDecisionRequest(BaseModel):
    # approve | deny | request_info (Spec 39 §2.3).
    decision: str
    reason: str | None = None


class RefundRequest(BaseModel):
    # None = full remaining balance; otherwise a partial refund in cents.
    amount_cents: int | None = None
    reason: str | None = None


class ApplicationFeeConfig(BaseModel):
    enabled: bool = False
    amount_cents: int = 0
    currency: str = "USD"


class WaiverPolicyConfig(BaseModel):
    policy: str = "allow_and_reconcile"
    auto_rules: list[str] = []


class DepositConfig(BaseModel):
    enabled: bool = False
    amount_cents: int = 0
    currency: str = "USD"
    deadline_days: int = 0
    refundable: bool = False
    non_refundable_cents: int = 0


class FeeConfigUpdate(BaseModel):
    application_fee: ApplicationFeeConfig | None = None
    waiver: WaiverPolicyConfig | None = None
    enrollment_deposit: DepositConfig | None = None
    stripe_connect_account_id: str | None = None
