"""Payment-provider abstraction (Spec 06 §4 / Spec 43 §10).

A ``BillingProvider`` turns billing intents (create customer, attach card,
create subscription, charge) into provider-side effects. This mirrors the AI
``AIProvider`` Protocol: the service layer stays provider-agnostic, and a
concrete provider maps the intent onto its own API.

Two providers are anticipated:
- ``MockBillingProvider`` — default. Deterministic, no network, no PCI surface.
  Used in dev / test / demo. A card ending ``0002`` is declined so the failure
  path is exercisable (Stripe-style test-card convention).
- ``StripeBillingProvider`` — planned (Spec 43 §10 sub-processor list). Slots in
  behind ``settings.billing_provider="stripe"`` without touching the service
  layer. Not implemented in the MVP; ``get_billing_provider`` raises a clear
  error if selected so misconfiguration is obvious rather than silent.

Money is integer cents throughout. The provider never persists rows — the
``BillingService`` owns the DB and the ledger, exactly as ``AIClient`` (not the
provider) owns the audit ledger.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from unipaith.config import settings


class BillingError(RuntimeError):
    """Base for provider-side billing failures."""


class CardDeclinedError(BillingError):
    """The payment instrument was declined. Surfaced to the caller as a 402."""


class ProviderNotConfiguredError(BillingError):
    """A real provider was selected but its credentials/SDK are absent."""


@dataclass
class CardInput:
    """A payment instrument supplied by the client.

    For the mock provider the raw fields are accepted (dev/demo only — there is
    no real card). For a real provider, ``token`` (an opaque, already-tokenized
    instrument from the client-side SDK) is the only PCI-safe path; raw PAN must
    never reach the server in production.
    """

    token: str | None = None
    number: str | None = None
    exp_month: int | None = None
    exp_year: int | None = None
    cvc: str | None = None
    name: str | None = None


@dataclass
class PaymentMethodResult:
    provider_payment_method_id: str
    brand: str
    last4: str
    exp_month: int
    exp_year: int


@dataclass
class SubscriptionResult:
    provider_subscription_id: str
    status: str  # "active" | "trialing" | "past_due"


@dataclass
class ChargeResult:
    provider_ref: str
    status: str  # "succeeded" | "failed"
    amount_cents: int


@runtime_checkable
class BillingProvider(Protocol):
    name: str

    def create_customer(self, *, email: str, user_ref: str) -> str:
        """Return a provider customer id."""
        ...

    def attach_payment_method(self, *, customer_id: str, card: CardInput) -> PaymentMethodResult:
        """Tokenize/attach the instrument; return display-safe metadata."""
        ...

    def create_subscription(
        self, *, customer_id: str, price_cents: int, description: str
    ) -> SubscriptionResult: ...

    def cancel_subscription(self, *, subscription_id: str, at_period_end: bool) -> None: ...

    def charge(self, *, customer_id: str, amount_cents: int, description: str) -> ChargeResult:
        """One-off charge (used for the institution per-applicant fee)."""
        ...

    def set_ad_free(self, *, subscription_id: str, enabled: bool) -> None:
        """Add/remove the $5/mo ad-free add-on item on an existing subscription.
        No-op for providers that model ad-free as a local flag only."""
        ...


def _brand_from_number(number: str) -> str:
    n = (number or "").replace(" ", "")
    if n.startswith("4"):
        return "visa"
    if n[:2] in {"51", "52", "53", "54", "55"} or n[:2] == "22":
        return "mastercard"
    if n[:2] in {"34", "37"}:
        return "amex"
    if n[:2] == "60" or n[:4] == "6011":
        return "discover"
    return "card"


class MockBillingProvider:
    """In-process, deterministic billing. No network, no stored secrets.

    Behaviour:
    - ``create_customer`` / ``create_subscription`` / ``charge`` succeed.
    - A card whose last4 is ``0002`` is declined (CardDeclinedError) so the
      failure path is testable.
    - ``brand``/``last4`` are derived from the supplied number; ids are random
      uuids prefixed by ``mock_`` so they read clearly in the ledger.
    """

    name = "mock"

    def create_customer(self, *, email: str, user_ref: str) -> str:
        return f"mock_cus_{uuid.uuid4().hex[:16]}"

    def attach_payment_method(self, *, customer_id: str, card: CardInput) -> PaymentMethodResult:
        number = (card.number or "").replace(" ", "")
        # Without a number (token-only), fall back to a generic display card.
        last4 = number[-4:] if len(number) >= 4 else "4242"
        if last4 == "0002":
            raise CardDeclinedError("Your card was declined.")
        return PaymentMethodResult(
            provider_payment_method_id=f"mock_pm_{uuid.uuid4().hex[:16]}",
            brand=_brand_from_number(number) if number else "card",
            last4=last4,
            exp_month=card.exp_month or 12,
            exp_year=card.exp_year or 2030,
        )

    def create_subscription(
        self, *, customer_id: str, price_cents: int, description: str
    ) -> SubscriptionResult:
        return SubscriptionResult(
            provider_subscription_id=f"mock_sub_{uuid.uuid4().hex[:16]}",
            status="active",
        )

    def cancel_subscription(self, *, subscription_id: str, at_period_end: bool) -> None:
        return None

    def charge(self, *, customer_id: str, amount_cents: int, description: str) -> ChargeResult:
        return ChargeResult(
            provider_ref=f"mock_ch_{uuid.uuid4().hex[:16]}",
            status="succeeded",
            amount_cents=amount_cents,
        )

    def set_ad_free(self, *, subscription_id: str, enabled: bool) -> None:
        # Mock tracks ad-free as a local flag on the Subscription row only.
        return None


_provider_singleton: BillingProvider | None = None


def get_billing_provider() -> BillingProvider:
    """Resolve the configured provider (singleton).

    ``mock`` (default, or whenever ``billing_mock_mode`` is on) returns the
    in-process provider. ``stripe`` is reserved — it raises until implemented so
    a half-configured production env fails loudly instead of silently no-op-ing.
    """
    global _provider_singleton
    if _provider_singleton is not None:
        return _provider_singleton

    name = (settings.billing_provider or "mock").lower()
    if settings.billing_mock_mode or name == "mock":
        _provider_singleton = MockBillingProvider()
    elif name == "stripe":
        if not settings.stripe_secret_key:
            raise ProviderNotConfiguredError(
                "BILLING_PROVIDER=stripe but STRIPE_SECRET_KEY is empty. "
                "Set the Stripe keys, or use BILLING_MOCK_MODE=true."
            )
        # Imported lazily so the stripe SDK isn't required for mock/dev/test.
        from unipaith.services.billing.stripe_provider import StripeBillingProvider

        _provider_singleton = StripeBillingProvider()
    else:
        raise ProviderNotConfiguredError(f"Unknown billing provider: {name!r}")
    return _provider_singleton


def reset_billing_provider_singleton() -> None:
    """Test hook — drop the cached provider so config changes take effect."""
    global _provider_singleton
    _provider_singleton = None
