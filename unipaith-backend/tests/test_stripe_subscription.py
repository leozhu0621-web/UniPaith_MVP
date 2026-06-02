"""Real-Stripe subscription path (Spec 07 §4.1 / 43 §10).

The Stripe SDK is mocked — no network, no keys — so these run in CI next to the
mock-provider tests. They prove the StripePaymentProvider maps subscription
intents onto the right Stripe calls, that declines surface as 400s, and that the
subscription webhook reconciles local state.
"""

from __future__ import annotations

import types
import uuid

import pytest
import stripe
from sqlalchemy import select

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException
from unipaith.models.billing import StudentSubscription
from unipaith.models.user import User, UserRole
from unipaith.services.billing_service import BillingService
from unipaith.services.payments.provider import (
    PaymentError,
    PaymentMethod,
    PaymentProvider,
    ProviderEvent,
    StripePaymentProvider,
)


def _ns(**kw):
    return types.SimpleNamespace(**kw)


# ── provider ────────────────────────────────────────────────────────────────


def test_attach_requires_token():
    # Raw PAN must never reach Stripe — a tokenized pm_... is required.
    with pytest.raises(PaymentError):
        StripePaymentProvider().attach_payment_method(uuid.uuid4())


def test_attach_creates_customer_and_subscription(monkeypatch):
    monkeypatch.setattr(settings, "stripe_price_id", "price_plus")
    monkeypatch.setattr(stripe.Customer, "create", lambda **kw: _ns(id="cus_1"))
    monkeypatch.setattr(stripe.PaymentMethod, "attach", lambda tok, **kw: _ns(id=tok))
    monkeypatch.setattr(stripe.Customer, "modify", lambda cid, **kw: _ns(id=cid))
    sub_created = {}
    monkeypatch.setattr(
        stripe.Subscription,
        "create",
        lambda **kw: sub_created.update(kw) or _ns(id="sub_1", status="active"),
    )
    monkeypatch.setattr(
        stripe.PaymentMethod,
        "retrieve",
        lambda tok, **kw: _ns(card=_ns(brand="visa", last4="4242")),
    )
    pm = StripePaymentProvider().attach_payment_method(
        uuid.uuid4(), payment_method_token="pm_abc", email="s@ex.co"
    )
    assert isinstance(pm, PaymentMethod)
    assert pm.customer_id == "cus_1"
    assert pm.subscription_id == "sub_1"
    assert pm.brand == "visa"
    assert pm.last4 == "4242"
    assert sub_created["items"][0]["price"] == "price_plus"


def test_attach_inline_price_when_unconfigured(monkeypatch):
    monkeypatch.setattr(settings, "stripe_price_id", "")
    monkeypatch.setattr(settings, "student_plan_price_usd", 15)
    monkeypatch.setattr(stripe.Customer, "create", lambda **kw: _ns(id="c"))
    monkeypatch.setattr(stripe.PaymentMethod, "attach", lambda tok, **kw: _ns(id=tok))
    monkeypatch.setattr(stripe.Customer, "modify", lambda cid, **kw: _ns(id=cid))
    captured = {}
    monkeypatch.setattr(
        stripe.Subscription,
        "create",
        lambda **kw: captured.update(kw) or _ns(id="s", status="active"),
    )
    monkeypatch.setattr(
        stripe.PaymentMethod, "retrieve", lambda tok, **kw: _ns(card=_ns(brand="visa", last4="1"))
    )
    StripePaymentProvider().attach_payment_method(uuid.uuid4(), payment_method_token="pm_x")
    # $15 → 1500 cents, monthly recurring.
    assert captured["items"][0]["price_data"]["unit_amount"] == 1500
    assert captured["items"][0]["price_data"]["recurring"]["interval"] == "month"


def test_declined_card_maps_to_payment_error(monkeypatch):
    monkeypatch.setattr(stripe.Customer, "create", lambda **kw: _ns(id="c"))

    def boom(tok, **kw):
        raise stripe.error.CardError("Your card was declined.", None, "card_declined")

    monkeypatch.setattr(stripe.PaymentMethod, "attach", boom)
    with pytest.raises(PaymentError):
        StripePaymentProvider().attach_payment_method(uuid.uuid4(), payment_method_token="pm_x")


def test_cancel_subscription_calls_stripe(monkeypatch):
    called = {}
    monkeypatch.setattr(
        stripe.Subscription, "modify", lambda sid, **kw: called.update({"id": sid, **kw})
    )
    StripePaymentProvider().cancel_subscription(subscription_id="sub_1", at_period_end=True)
    assert called["id"] == "sub_1"
    assert called["cancel_at_period_end"] is True


def test_set_ad_free_item_add_and_remove(monkeypatch):
    monkeypatch.setattr(settings, "stripe_adfree_price_id", "price_adfree")
    created, deleted = {}, {}
    monkeypatch.setattr(stripe.SubscriptionItem, "list", lambda **kw: _ns(data=[]))
    monkeypatch.setattr(
        stripe.SubscriptionItem, "create", lambda **kw: created.update(kw) or _ns(id="si_1")
    )
    StripePaymentProvider().set_subscription_ad_free(subscription_id="sub_1", enabled=True)
    assert created["price"] == "price_adfree"

    existing = _ns(id="si_1", price=_ns(id="price_adfree"))
    monkeypatch.setattr(stripe.SubscriptionItem, "list", lambda **kw: _ns(data=[existing]))
    monkeypatch.setattr(
        stripe.SubscriptionItem, "delete", lambda iid, **kw: deleted.update({"id": iid})
    )
    StripePaymentProvider().set_subscription_ad_free(subscription_id="sub_1", enabled=False)
    assert deleted["id"] == "si_1"


def test_webhook_parses_subscription_events(monkeypatch):
    monkeypatch.setattr(
        stripe.Webhook,
        "construct_event",
        lambda payload, sig, secret: {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_9", "status": "canceled"}},
        },
    )
    ev = StripePaymentProvider().verify_and_parse_webhook(b"{}", "sig")
    assert ev.type == "customer.subscription.deleted"
    assert ev.subscription_id == "sub_9"
    assert ev.subscription_status == "canceled"


# ── service (with a fake stripe-named provider) ──────────────────────────────


class _FakeStripeProvider(PaymentProvider):
    name = "stripe"

    def __init__(self, *, decline: bool = False):
        self.decline = decline
        self.canceled = None
        self.ad_free = None

    def attach_payment_method(self, user_id, *, payment_method_token=None, email=None):
        if self.decline:
            raise PaymentError("Your card was declined.")
        return PaymentMethod(
            brand="visa", last4="4242", customer_id="cus_x", subscription_id="sub_x"
        )

    def cancel_subscription(self, *, subscription_id, at_period_end=True):
        self.canceled = subscription_id

    def set_subscription_ad_free(self, *, subscription_id, enabled):
        self.ad_free = (subscription_id, enabled)

    def create_checkout_session(self, **kw):  # pragma: no cover - unused here
        raise NotImplementedError

    def refund(self, **kw):  # pragma: no cover - unused here
        raise NotImplementedError

    def verify_and_parse_webhook(self, payload, sig_header):  # pragma: no cover
        return ProviderEvent(type="ignored")


async def _student(db) -> User:
    u = User(
        email=f"st-{uuid.uuid4().hex[:8]}@ex.co",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


@pytest.mark.asyncio
async def test_upgrade_with_stripe_records_real_provider(db_session):
    u = await _student(db_session)
    svc = BillingService(db_session, provider=_FakeStripeProvider())
    resp = await svc.upgrade(u.id, payment_method_token="pm_live", email=u.email)
    assert resp.status == "active"
    assert resp.payment_method_last4 == "4242"
    assert resp.provider == "stripe"
    sub = (
        await db_session.execute(
            select(StudentSubscription).where(StudentSubscription.user_id == u.id)
        )
    ).scalar_one()
    assert sub.provider == "stripe"  # not hardcoded "mock"
    assert sub.provider_subscription_id == "sub_x"


@pytest.mark.asyncio
async def test_upgrade_declined_card_returns_400(db_session):
    u = await _student(db_session)
    svc = BillingService(db_session, provider=_FakeStripeProvider(decline=True))
    with pytest.raises(BadRequestException):
        await svc.upgrade(u.id, payment_method_token="pm_bad", email=u.email)


@pytest.mark.asyncio
async def test_cancel_calls_provider_for_real_sub(db_session):
    u = await _student(db_session)
    provider = _FakeStripeProvider()
    svc = BillingService(db_session, provider=provider)
    await svc.upgrade(u.id, payment_method_token="pm_live", email=u.email)
    await svc.cancel(u.id)
    assert provider.canceled == "sub_x"


@pytest.mark.asyncio
async def test_webhook_event_expires_subscription(db_session):
    u = await _student(db_session)
    svc = BillingService(db_session, provider=_FakeStripeProvider())
    await svc.upgrade(u.id, payment_method_token="pm_live", email=u.email)
    handled = await svc.handle_subscription_event(
        ProviderEvent(type="customer.subscription.deleted", subscription_id="sub_x")
    )
    assert handled is True
    sub = (
        await db_session.execute(
            select(StudentSubscription).where(StudentSubscription.user_id == u.id)
        )
    ).scalar_one()
    assert sub.status == "expired"


@pytest.mark.asyncio
async def test_webhook_invoice_paid_keeps_active(db_session):
    u = await _student(db_session)
    svc = BillingService(db_session, provider=_FakeStripeProvider())
    await svc.upgrade(u.id, payment_method_token="pm_live", email=u.email)
    handled = await svc.handle_subscription_event(
        ProviderEvent(type="invoice.payment_succeeded", subscription_id="sub_x", amount_cents=1500)
    )
    assert handled is True
    sub = (
        await db_session.execute(
            select(StudentSubscription).where(StudentSubscription.user_id == u.id)
        )
    ).scalar_one()
    assert sub.status == "active"
