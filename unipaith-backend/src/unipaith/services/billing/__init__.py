"""Billing subsystem (Spec 06 §4).

- ``provider`` — payment-provider abstraction (Protocol + MockBillingProvider,
  Stripe-ready) mirroring the AI-provider pattern in ``unipaith.ai.providers``.
- ``unipaith.services.entitlements`` — the free-vs-paid feature gate map.
- ``unipaith.services.billing_service`` — orchestration (trial, subscribe,
  ad-free, cancel, institution per-applicant charges).
"""

from unipaith.services.billing.provider import (
    BillingError,
    BillingProvider,
    CardDeclinedError,
    CardInput,
    ChargeResult,
    MockBillingProvider,
    PaymentMethodResult,
    SubscriptionResult,
    get_billing_provider,
)

__all__ = [
    "BillingError",
    "BillingProvider",
    "CardDeclinedError",
    "CardInput",
    "ChargeResult",
    "MockBillingProvider",
    "PaymentMethodResult",
    "SubscriptionResult",
    "get_billing_provider",
]
