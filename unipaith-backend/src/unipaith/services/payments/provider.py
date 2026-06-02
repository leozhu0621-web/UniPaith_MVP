"""PaymentProvider seam (Spec 39 §4).

Provider-portability — the same pattern as the LLM provider abstraction (Spec
04): swap providers, not call sites. ``MockPaymentProvider`` is the default and
moves no real money (a deterministic in-app checkout the student completes), so
the whole fee/deposit flow is live and demoable without Stripe keys.
``StripePaymentProvider`` swaps in per-environment once Stripe Connect
onboarding + keys are present (``payments_provider="stripe"``).

PCI: providers return only identifiers + status. No raw card data ever reaches
the application or the database.

This module is also the single source of the ``PaymentMethod`` / provider used
by the student-subscription billing layer (``billing_service``) — Spec 39 §12
"same PaymentProvider".
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import UUID

from unipaith.config import settings


@dataclass
class PaymentMethod:
    """A card-on-file summary for subscription billing (Spec 21 §2.7)."""

    brand: str
    last4: str
    customer_id: str
    subscription_id: str


@dataclass
class CheckoutSession:
    """The result of opening a checkout for a fee/deposit.

    ``inline`` providers (mock) are completed in-app via ``confirm-mock``; the
    UI shows a calm checkout panel rather than redirecting. Redirect providers
    (stripe) hand back a hosted-checkout ``url``.
    """

    session_id: str
    provider: str
    inline: bool
    url: str | None = None
    publishable_key: str | None = None


@dataclass
class RefundResult:
    refund_id: str
    amount_cents: int
    status: str  # 'succeeded' | 'pending' | 'failed'


@dataclass
class ProviderEvent:
    """Normalized webhook event the service can act on without provider details."""

    type: str  # 'checkout.session.completed' | 'charge.refunded' | other (ignored)
    session_id: str | None = None
    charge_id: str | None = None
    amount_cents: int | None = None
    metadata: dict = field(default_factory=dict)


class PaymentProvider(ABC):
    """The seam every payment surface depends on (never a concrete provider)."""

    name: str = "base"

    @abstractmethod
    def attach_payment_method(self, user_id: UUID) -> PaymentMethod: ...

    @abstractmethod
    def create_checkout_session(
        self,
        *,
        payment_id: UUID,
        kind: str,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
        connected_account_id: str | None = None,
        metadata: dict | None = None,
    ) -> CheckoutSession: ...

    @abstractmethod
    def refund(self, *, charge_id: str, amount_cents: int | None = None) -> RefundResult: ...

    @abstractmethod
    def verify_and_parse_webhook(self, payload: bytes, sig_header: str | None) -> ProviderEvent: ...


class MockPaymentProvider(PaymentProvider):
    """No real charge. Checkout is completed in-app (``confirm-mock``), driving
    the exact same success path a real webhook would. Returns a deterministic
    test card for subscription billing (Spec 21 §2.7 MVP scope)."""

    name = "mock"

    def attach_payment_method(self, user_id: UUID) -> PaymentMethod:
        token = uuid.uuid4().hex
        return PaymentMethod(
            brand="Visa",
            last4="4242",
            customer_id=f"mock_cus_{token[:14]}",
            subscription_id=f"mock_sub_{token[14:]}",
        )

    def create_checkout_session(
        self,
        *,
        payment_id: UUID,
        kind: str,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
        connected_account_id: str | None = None,
        metadata: dict | None = None,
    ) -> CheckoutSession:
        return CheckoutSession(
            session_id=f"mock_cs_{uuid.uuid4().hex[:20]}",
            provider="mock",
            inline=True,
            url=None,
        )

    def refund(self, *, charge_id: str, amount_cents: int | None = None) -> RefundResult:
        return RefundResult(
            refund_id=f"mock_re_{uuid.uuid4().hex[:16]}",
            amount_cents=amount_cents or 0,
            status="succeeded",
        )

    def verify_and_parse_webhook(self, payload: bytes, sig_header: str | None) -> ProviderEvent:
        # Mock mode has no external webhook source — the in-app confirm endpoint
        # drives success instead. Treated as a no-op by the webhook route.
        return ProviderEvent(type="ignored")


class StripePaymentProvider(PaymentProvider):
    """Real Stripe (Connect). Lazy-imports ``stripe`` so the dependency is only
    touched when this provider is actually selected."""

    name = "stripe"

    def __init__(self) -> None:
        import stripe  # lazy — only when payments_provider == "stripe"

        stripe.api_key = settings.stripe_secret_key
        self._stripe = stripe

    def attach_payment_method(self, user_id: UUID) -> PaymentMethod:
        # Subscription card capture is out of Spec 39's transactional scope;
        # mirror the deterministic mock so existing billing UI is unaffected.
        return MockPaymentProvider().attach_payment_method(user_id)

    def create_checkout_session(
        self,
        *,
        payment_id: UUID,
        kind: str,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
        connected_account_id: str | None = None,
        metadata: dict | None = None,
    ) -> CheckoutSession:
        meta = {"payment_id": str(payment_id), "kind": kind, **(metadata or {})}
        params: dict = {
            "mode": "payment",
            "line_items": [
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": description},
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "client_reference_id": str(payment_id),
            "metadata": meta,
            "payment_intent_data": {"metadata": meta},
        }
        if customer_email:
            params["customer_email"] = customer_email
        if kind == "enrollment_deposit":
            # ACH for larger deposits (Spec 39 §4) — card + US bank debit.
            params["payment_method_types"] = ["card", "us_bank_account"]
        request_opts: dict = {}
        if connected_account_id:
            # Stripe Connect direct charge — funds settle on the institution's
            # connected account (Spec 39 §4).
            request_opts["stripe_account"] = connected_account_id
        session = self._stripe.checkout.Session.create(**params, **request_opts)
        return CheckoutSession(
            session_id=session.id,
            provider="stripe",
            inline=False,
            url=session.url,
            publishable_key=settings.stripe_publishable_key or None,
        )

    def refund(self, *, charge_id: str, amount_cents: int | None = None) -> RefundResult:
        kwargs: dict = {"charge": charge_id}
        if amount_cents is not None:
            kwargs["amount"] = amount_cents
        refund = self._stripe.Refund.create(**kwargs)
        return RefundResult(
            refund_id=refund.id,
            amount_cents=int(getattr(refund, "amount", amount_cents or 0) or 0),
            status=getattr(refund, "status", "succeeded") or "succeeded",
        )

    def verify_and_parse_webhook(self, payload: bytes, sig_header: str | None) -> ProviderEvent:
        event = self._stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
        etype = event["type"]
        data = event["data"]["object"]
        if etype == "checkout.session.completed":
            return ProviderEvent(
                type=etype,
                session_id=data.get("id"),
                charge_id=data.get("payment_intent"),
                amount_cents=data.get("amount_total"),
                metadata=data.get("metadata") or {},
            )
        if etype in ("charge.refunded", "charge.refund.updated"):
            return ProviderEvent(
                type="charge.refunded",
                charge_id=data.get("id") or data.get("charge"),
                amount_cents=data.get("amount_refunded"),
                metadata=data.get("metadata") or {},
            )
        return ProviderEvent(type=etype)


def get_payment_provider() -> PaymentProvider:
    """Factory — the only place provider selection happens (Spec 39 §4)."""
    if settings.payments_provider == "stripe" and settings.stripe_secret_key:
        try:
            return StripePaymentProvider()
        except Exception:  # noqa: BLE001 — never let a misconfigured Stripe break the app
            return MockPaymentProvider()
    return MockPaymentProvider()
