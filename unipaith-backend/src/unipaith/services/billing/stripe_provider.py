"""Stripe implementation of ``BillingProvider`` (Spec 06 §4 / Spec 43 §10).

Activated when ``BILLING_PROVIDER=stripe`` and ``STRIPE_SECRET_KEY`` is set
(``BILLING_MOCK_MODE`` must be false). The mock provider remains the default for
dev / test / CI, so no Stripe account or network is needed there.

PCI posture: this provider NEVER accepts a raw PAN. The client tokenizes the
card with Stripe Elements and sends the resulting PaymentMethod id
(``pm_...``) as ``CardInput.token``; only that token reaches the server.

Money is integer cents end-to-end, which is exactly Stripe's unit for USD.
"""

from __future__ import annotations

import logging

import stripe

from unipaith.config import settings
from unipaith.services.billing.provider import (
    BillingError,
    CardDeclinedError,
    CardInput,
    ChargeResult,
    PaymentMethodResult,
    SubscriptionResult,
)

logger = logging.getLogger(__name__)


class StripeBillingProvider:
    """Maps billing intents onto the Stripe API. One instance per process."""

    name = "stripe"

    def __init__(self) -> None:
        stripe.api_key = settings.stripe_secret_key
        if settings.stripe_api_version:
            stripe.api_version = settings.stripe_api_version

    # -- helpers ----------------------------------------------------------------

    @staticmethod
    def _raise(e: Exception) -> None:
        """Translate a Stripe error into our typed billing errors so the service
        layer can map to 402 (declined) vs 400 (other)."""
        if isinstance(e, stripe.error.CardError):
            # Surfaced to the student as a 402 with the card's decline message.
            raise CardDeclinedError(
                getattr(e, "user_message", None) or "Your card was declined."
            ) from e
        raise BillingError(f"Stripe error: {e}") from e

    # -- customer ---------------------------------------------------------------

    def create_customer(self, *, email: str, user_ref: str) -> str:
        try:
            customer = stripe.Customer.create(email=email, metadata={"user_id": user_ref})
            return customer.id
        except stripe.error.StripeError as e:
            self._raise(e)
            raise  # unreachable — _raise always raises

    # -- payment method ---------------------------------------------------------

    def attach_payment_method(self, *, customer_id: str, card: CardInput) -> PaymentMethodResult:
        if not card.token:
            # Raw PAN must never reach a real provider (PCI). The client must
            # tokenize via Stripe Elements and pass the PaymentMethod id.
            raise BillingError(
                "Stripe requires a tokenized payment method (pm_...). "
                "Tokenize the card client-side with Stripe Elements."
            )
        try:
            pm = stripe.PaymentMethod.attach(card.token, customer=customer_id)
            # Make it the default for invoices (so the subscription charges it).
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": pm.id},
            )
            details = pm.card
            return PaymentMethodResult(
                provider_payment_method_id=pm.id,
                brand=details.brand,
                last4=details.last4,
                exp_month=details.exp_month,
                exp_year=details.exp_year,
            )
        except stripe.error.StripeError as e:
            self._raise(e)
            raise

    # -- subscription -----------------------------------------------------------

    def create_subscription(
        self, *, customer_id: str, price_cents: int, description: str
    ) -> SubscriptionResult:
        if settings.stripe_price_id:
            item: dict = {"price": settings.stripe_price_id}
        else:
            # No pre-created Price — build an inline recurring price from config.
            item = {
                "price_data": {
                    "currency": settings.billing_currency,
                    "product_data": {"name": "UniPaith Plus"},
                    "recurring": {"interval": "month"},
                    "unit_amount": price_cents,
                }
            }
        try:
            sub = stripe.Subscription.create(
                customer=customer_id,
                items=[item],
                # Charge the card-on-file now; raise immediately if it fails so
                # we map to a 402 rather than leaving an "incomplete" sub.
                payment_behavior="error_if_incomplete",
                expand=["latest_invoice.payment_intent"],
                metadata={"description": description},
            )
            return SubscriptionResult(provider_subscription_id=sub.id, status=sub.status)
        except stripe.error.StripeError as e:
            self._raise(e)
            raise

    def cancel_subscription(self, *, subscription_id: str, at_period_end: bool) -> None:
        try:
            if at_period_end:
                stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
            else:
                stripe.Subscription.cancel(subscription_id)
        except stripe.error.StripeError as e:
            self._raise(e)

    def set_ad_free(self, *, subscription_id: str, enabled: bool) -> None:
        price_id = settings.stripe_adfree_price_id
        if not price_id:
            raise BillingError(
                "STRIPE_ADFREE_PRICE_ID is not configured; cannot manage the ad-free add-on."
            )
        try:
            items = stripe.SubscriptionItem.list(subscription=subscription_id)
            existing = next((i for i in items.data if i.price.id == price_id), None)
            if enabled and existing is None:
                stripe.SubscriptionItem.create(subscription=subscription_id, price=price_id)
            elif not enabled and existing is not None:
                stripe.SubscriptionItem.delete(existing.id)
        except stripe.error.StripeError as e:
            self._raise(e)

    # -- one-off charge (institution per-applicant fee) -------------------------

    def charge(self, *, customer_id: str, amount_cents: int, description: str) -> ChargeResult:
        try:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=settings.billing_currency,
                customer=customer_id,
                description=description,
                off_session=True,
                confirm=True,
            )
            return ChargeResult(
                provider_ref=intent.id,
                status="succeeded" if intent.status == "succeeded" else "failed",
                amount_cents=amount_cents,
            )
        except stripe.error.CardError as e:
            # Institution card declined — record as a failed charge, not a 402.
            logger.warning("institution charge declined: %s", e)
            return ChargeResult(
                provider_ref=getattr(getattr(e, "error", None), "payment_intent", {}).get("id", "")
                if getattr(e, "error", None)
                else "",
                status="failed",
                amount_cents=amount_cents,
            )
        except stripe.error.StripeError as e:
            self._raise(e)
            raise
