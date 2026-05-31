"""Stripe provider + webhook tests (Spec 06 §4 / Spec 43 §10).

The Stripe SDK is mocked — no network, no keys — so these run in CI alongside
the mock-provider tests. They assert the provider maps our intents onto the
right Stripe calls and translates Stripe errors/events correctly.
"""

from __future__ import annotations

import types
from datetime import UTC, datetime, timedelta

import pytest
import stripe

from unipaith.config import settings
from unipaith.models.billing import (
    PLAN_FREE,
    PLAN_PLUS,
    PLAN_TRIAL,
    STATUS_ACTIVE,
    STATUS_CANCELED,
    STATUS_PAST_DUE,
    STATUS_TRIALING,
    BillingEvent,
    Subscription,
)
from unipaith.models.user import User, UserRole
from unipaith.services.billing.provider import (
    BillingError,
    CardDeclinedError,
    CardInput,
)
from unipaith.services.billing.stripe_provider import StripeBillingProvider
from unipaith.services.billing_service import BillingService


def _ns(**kw):
    return types.SimpleNamespace(**kw)


# ------------------------------------------------------------------- provider


def test_create_customer(monkeypatch):
    monkeypatch.setattr(stripe.Customer, "create", lambda **kw: _ns(id="cus_123"))
    assert StripeBillingProvider().create_customer(email="a@b.co", user_ref="u1") == "cus_123"


def test_attach_requires_token():
    # Raw PAN must never reach Stripe — only a tokenized pm_... is accepted.
    with pytest.raises(BillingError):
        StripeBillingProvider().attach_payment_method(
            customer_id="cus_1", card=CardInput(number="4242424242424242")
        )


def test_attach_payment_method(monkeypatch):
    pm = _ns(id="pm_1", card=_ns(brand="visa", last4="4242", exp_month=12, exp_year=2030))
    monkeypatch.setattr(stripe.PaymentMethod, "attach", lambda tok, **kw: pm)
    monkeypatch.setattr(stripe.Customer, "modify", lambda cid, **kw: _ns(id=cid))
    r = StripeBillingProvider().attach_payment_method(
        customer_id="cus_1", card=CardInput(token="pm_1")
    )
    assert r.provider_payment_method_id == "pm_1"
    assert r.brand == "visa"
    assert r.last4 == "4242"
    assert r.exp_month == 12


def test_card_declined_maps_to_typed_error(monkeypatch):
    def boom(tok, **kw):
        raise stripe.error.CardError("Your card was declined.", None, "card_declined")

    monkeypatch.setattr(stripe.PaymentMethod, "attach", boom)
    with pytest.raises(CardDeclinedError):
        StripeBillingProvider().attach_payment_method(
            customer_id="cus_1", card=CardInput(token="pm_x")
        )


def test_create_subscription_with_configured_price(monkeypatch):
    captured = {}

    def fake_create(**kw):
        captured.update(kw)
        return _ns(id="sub_1", status="active")

    monkeypatch.setattr(settings, "stripe_price_id", "price_plus")
    monkeypatch.setattr(stripe.Subscription, "create", fake_create)
    r = StripeBillingProvider().create_subscription(
        customer_id="cus_1", price_cents=1500, description="x"
    )
    assert r.provider_subscription_id == "sub_1"
    assert r.status == "active"
    assert captured["items"][0]["price"] == "price_plus"


def test_create_subscription_inline_price_when_unconfigured(monkeypatch):
    captured = {}
    monkeypatch.setattr(settings, "stripe_price_id", "")
    monkeypatch.setattr(
        stripe.Subscription,
        "create",
        lambda **kw: captured.update(kw) or _ns(id="s", status="active"),
    )
    StripeBillingProvider().create_subscription(customer_id="c", price_cents=1500, description="x")
    assert captured["items"][0]["price_data"]["unit_amount"] == 1500
    assert captured["items"][0]["price_data"]["recurring"]["interval"] == "month"


def test_set_ad_free_adds_and_removes_item(monkeypatch):
    monkeypatch.setattr(settings, "stripe_adfree_price_id", "price_adfree")
    created, deleted = {}, {}
    # No existing ad-free item → enabling creates one.
    monkeypatch.setattr(stripe.SubscriptionItem, "list", lambda **kw: _ns(data=[]))
    monkeypatch.setattr(
        stripe.SubscriptionItem, "create", lambda **kw: created.update(kw) or _ns(id="si_1")
    )
    StripeBillingProvider().set_ad_free(subscription_id="sub_1", enabled=True)
    assert created["price"] == "price_adfree"

    # Existing ad-free item → disabling deletes it.
    existing = _ns(id="si_1", price=_ns(id="price_adfree"))
    monkeypatch.setattr(stripe.SubscriptionItem, "list", lambda **kw: _ns(data=[existing]))
    monkeypatch.setattr(
        stripe.SubscriptionItem, "delete", lambda item_id, **kw: deleted.update({"id": item_id})
    )
    StripeBillingProvider().set_ad_free(subscription_id="sub_1", enabled=False)
    assert deleted["id"] == "si_1"


def test_set_ad_free_without_price_raises():
    # No ad-free price configured → clear error, not a silent no-op.
    s_before = settings.stripe_adfree_price_id
    settings.stripe_adfree_price_id = ""
    try:
        with pytest.raises(BillingError):
            StripeBillingProvider().set_ad_free(subscription_id="sub_1", enabled=True)
    finally:
        settings.stripe_adfree_price_id = s_before


def test_charge_one_off(monkeypatch):
    monkeypatch.setattr(
        stripe.PaymentIntent, "create", lambda **kw: _ns(id="pi_1", status="succeeded")
    )
    r = StripeBillingProvider().charge(customer_id="cus_1", amount_cents=1500, description="x")
    assert r.status == "succeeded"
    assert r.provider_ref == "pi_1"
    assert r.amount_cents == 1500


# -------------------------------------------------------------------- webhook


async def _sub(db, *, provider_subscription_id="sub_1", plan=PLAN_PLUS, status=STATUS_ACTIVE):
    import uuid

    u = User(
        email=f"wh-{uuid.uuid4().hex[:8]}@ex.co",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(u)
    await db.flush()
    s = Subscription(
        user_id=u.id,
        plan=plan,
        status=status,
        provider="stripe",
        provider_subscription_id=provider_subscription_id,
    )
    db.add(s)
    await db.flush()
    return s


async def test_webhook_subscription_past_due(db_session):
    s = await _sub(db_session)
    svc = BillingService(db_session)
    handled = await svc._apply_stripe_event(
        "customer.subscription.updated",
        {
            "id": "sub_1",
            "status": "past_due",
            "cancel_at_period_end": False,
            "current_period_end": int((datetime.now(UTC) + timedelta(days=2)).timestamp()),
        },
    )
    assert handled is True
    await db_session.flush()
    await db_session.refresh(s)
    assert s.status == STATUS_PAST_DUE


async def test_webhook_subscription_deleted_drops_to_free(db_session):
    s = await _sub(db_session)
    svc = BillingService(db_session)
    handled = await svc._apply_stripe_event("customer.subscription.deleted", {"id": "sub_1"})
    assert handled is True
    await db_session.flush()
    await db_session.refresh(s)
    assert s.plan == PLAN_FREE
    assert s.status == STATUS_CANCELED


async def test_webhook_invoice_paid_logs_payment(db_session):
    from sqlalchemy import select

    s = await _sub(db_session, plan=PLAN_TRIAL, status=STATUS_TRIALING)
    svc = BillingService(db_session)
    handled = await svc._apply_stripe_event(
        "invoice.payment_succeeded",
        {"subscription": "sub_1", "amount_paid": 1500, "id": "in_1", "period_end": None},
    )
    assert handled is True
    await db_session.refresh(s)
    assert s.status == STATUS_ACTIVE
    assert s.plan == PLAN_PLUS
    events = (
        (await db_session.execute(select(BillingEvent).where(BillingEvent.user_id == s.user_id)))
        .scalars()
        .all()
    )
    assert any(e.event_type == "payment_succeeded" and e.amount_cents == 1500 for e in events)


async def test_webhook_unknown_subscription_is_noop(db_session):
    svc = BillingService(db_session)
    handled = await svc._apply_stripe_event("customer.subscription.deleted", {"id": "nope"})
    assert handled is False


async def test_webhook_bad_signature_rejected(db_session, monkeypatch):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")

    def boom(payload, sig, secret):
        raise ValueError("bad sig")

    monkeypatch.setattr(stripe.Webhook, "construct_event", boom)
    svc = BillingService(db_session)
    with pytest.raises(Exception) as ei:
        await svc.handle_stripe_webhook(b"{}", "t=1,v1=bad")
    assert "signature" in str(ei.value).lower()
