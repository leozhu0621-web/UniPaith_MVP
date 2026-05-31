"""Billing orchestration (Spec 06 §4).

Owns the DB and the append-only ``billing_events`` ledger; delegates the actual
money movement to a ``BillingProvider`` (mock by default). Everything here is a
no-op when ``settings.billing_enabled`` is False, so the platform is unchanged
until the flag is flipped per-environment.

Student lifecycle:  signup → 7-day trial → (card-on-file) → ``$15/mo`` Plus,
with an optional ``$5/mo`` ad-free add-on. Trial expiry is resolved lazily on
read (no cron needed): a ``trialing`` subscription past ``trial_ends_at`` with no
card becomes ``free``.

Institution lifecycle:  each *unique* applicant an institution processes is a
``$15`` charge, deduped on (institution, student).
"""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException
from unipaith.models.application import Application
from unipaith.models.billing import (
    EVENT_ADFREE_DISABLED,
    EVENT_ADFREE_ENABLED,
    EVENT_APPLICANT_CHARGED,
    EVENT_PAYMENT_FAILED,
    EVENT_PAYMENT_METHOD_ADDED,
    EVENT_PAYMENT_SUCCEEDED,
    EVENT_SUBSCRIPTION_CANCELED,
    EVENT_SUBSCRIPTION_CREATED,
    EVENT_TRIAL_CONVERTED,
    EVENT_TRIAL_STARTED,
    PLAN_FREE,
    PLAN_PLUS,
    PLAN_TRIAL,
    STATUS_ACTIVE,
    STATUS_CANCELED,
    STATUS_FREE,
    STATUS_PAST_DUE,
    STATUS_TRIALING,
    BillingEvent,
    InstitutionApplicantCharge,
    PaymentMethod,
    Subscription,
)
from unipaith.models.institution import Program
from unipaith.models.user import User
from unipaith.services.billing.provider import (
    BillingError,
    CardInput,
    get_billing_provider,
)
from unipaith.services.entitlements import entitlements_for, feature_matrix

logger = logging.getLogger(__name__)


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ trial

    async def start_trial(self, user: User) -> Subscription | None:
        """Create the 7-day trial for a student. Idempotent; no-op when billing
        is disabled or the user already has a subscription. Safe to call from
        signup — never raises into the caller."""
        if not settings.billing_enabled:
            return None
        if user.role.value != "student":
            return None
        existing = await self._get_subscription(user.id)
        if existing is not None:
            return existing
        now = datetime.now(UTC)
        sub = Subscription(
            user_id=user.id,
            plan=PLAN_TRIAL,
            status=STATUS_TRIALING,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=settings.billing_trial_days),
            provider=get_billing_provider().name,
        )
        self.db.add(sub)
        await self.db.flush()
        await self._log_event(
            user_id=user.id,
            event_type=EVENT_TRIAL_STARTED,
            metadata={"trial_days": settings.billing_trial_days},
        )
        return sub

    # --------------------------------------------------------------- read/status

    async def get_status(self, user: User) -> dict:
        """Resolved billing status for the student app. Lazily starts a trial for
        an entitled student who has none, and lazily expires a lapsed trial."""
        if not settings.billing_enabled:
            # Billing off → the UI shows no paywall and everything is entitled.
            return {
                "enabled": False,
                "plan": PLAN_PLUS,
                "status": STATUS_ACTIVE,
                "trial_ends_at": None,
                "trial_days_left": None,
                "ad_free": True,
                "has_payment_method": False,
                "cancel_at_period_end": False,
                "current_period_end": None,
                "entitlements": sorted(f.value for f in entitlements_for(PLAN_PLUS)),
                "feature_matrix": feature_matrix(),
                "prices": self._prices(),
            }

        sub = await self._get_subscription(user.id)
        if sub is None:
            sub = await self.start_trial(user)
        if sub is None:  # non-student or still disabled
            sub = Subscription(user_id=user.id, plan=PLAN_FREE, status=STATUS_FREE)

        plan = await self._resolve_and_persist_expiry(sub)
        pm = await self._get_default_payment_method(user.id)
        provider_name = "mock" if settings.billing_mock_mode else settings.billing_provider
        return {
            "enabled": True,
            "mock": settings.billing_mock_mode,
            "provider": provider_name,
            # Only the publishable key is client-safe; never the secret key.
            "publishable_key": (
                settings.stripe_publishable_key if provider_name == "stripe" else None
            ),
            "plan": plan,
            "status": sub.status,
            "trial_ends_at": _iso(sub.trial_ends_at),
            "trial_days_left": self._trial_days_left(sub),
            "ad_free": bool(sub.ad_free),
            "has_payment_method": pm is not None,
            "payment_method": _pm_public(pm),
            "cancel_at_period_end": bool(sub.cancel_at_period_end),
            "current_period_end": _iso(sub.current_period_end),
            "entitlements": sorted(f.value for f in entitlements_for(plan)),
            "feature_matrix": feature_matrix(),
            "prices": self._prices(),
        }

    async def effective_plan(self, user: User) -> str:
        """The plan to enforce entitlements against. ``plus`` when billing is
        disabled (no gating)."""
        if not settings.billing_enabled:
            return PLAN_PLUS
        sub = await self._get_subscription(user.id)
        if sub is None:
            sub = await self.start_trial(user)
        if sub is None:
            return PLAN_FREE
        return await self._resolve_and_persist_expiry(sub)

    # ------------------------------------------------------------ payment method

    async def add_payment_method(self, user: User, card: CardInput) -> dict:
        self._require_enabled()
        sub = await self._get_subscription(user.id) or await self.start_trial(user)
        if sub is None:
            raise BadRequestException("Billing is not available for this account.")
        provider = get_billing_provider()
        try:
            if not sub.provider_customer_id:
                sub.provider_customer_id = provider.create_customer(
                    email=user.email, user_ref=str(user.id)
                )
            result = provider.attach_payment_method(customer_id=sub.provider_customer_id, card=card)
        except BillingError as e:
            await self._log_event(
                user_id=user.id,
                event_type="payment_failed",
                status="failed",
                metadata={"reason": str(e)},
            )
            raise BadRequestException(str(e)) from e

        # One card on file: clear any previous default, store the new one.
        for old in await self._list_payment_methods(user.id):
            old.is_default = False
        pm = PaymentMethod(
            user_id=user.id,
            provider=provider.name,
            provider_payment_method_id=result.provider_payment_method_id,
            brand=result.brand,
            last4=result.last4,
            exp_month=result.exp_month,
            exp_year=result.exp_year,
            is_default=True,
        )
        self.db.add(pm)
        await self.db.flush()
        await self._log_event(
            user_id=user.id,
            event_type=EVENT_PAYMENT_METHOD_ADDED,
            provider=provider.name,
            provider_ref=result.provider_payment_method_id,
            metadata={"brand": result.brand, "last4": result.last4},
        )
        return _pm_public(pm)

    # ----------------------------------------------------------------- subscribe

    async def subscribe(self, user: User) -> dict:
        """Convert the trial (or free) account to paying ``$15/mo`` Plus.
        Requires a card on file (card-on-file auto-convert, Spec 06 §4.1)."""
        self._require_enabled()
        sub = await self._get_subscription(user.id) or await self.start_trial(user)
        if sub is None:
            raise BadRequestException("Billing is not available for this account.")

        plan = await self._resolve_and_persist_expiry(sub)
        if plan == PLAN_PLUS and sub.status == STATUS_ACTIVE and not sub.cancel_at_period_end:
            return await self.get_status(user)  # already subscribed — idempotent

        pm = await self._get_default_payment_method(user.id)
        if pm is None:
            raise BadRequestException("Add a payment method before subscribing.")

        was_trialing = sub.status == STATUS_TRIALING
        provider = get_billing_provider()
        result = provider.create_subscription(
            customer_id=sub.provider_customer_id or "mock",
            price_cents=settings.billing_student_plan_price_cents,
            description="UniPaith Plus — monthly",
        )
        now = datetime.now(UTC)
        sub.plan = PLAN_PLUS
        sub.status = STATUS_ACTIVE
        sub.provider_subscription_id = result.provider_subscription_id
        sub.current_period_start = now
        sub.current_period_end = now + timedelta(days=30)
        sub.cancel_at_period_end = False
        sub.canceled_at = None
        await self.db.flush()

        if was_trialing:
            await self._log_event(user_id=user.id, event_type=EVENT_TRIAL_CONVERTED)
        await self._log_event(
            user_id=user.id,
            event_type=EVENT_SUBSCRIPTION_CREATED,
            provider=provider.name,
            provider_ref=result.provider_subscription_id,
        )
        await self._log_event(
            user_id=user.id,
            event_type=EVENT_PAYMENT_SUCCEEDED,
            amount_cents=settings.billing_student_plan_price_cents,
            provider=provider.name,
        )
        return await self.get_status(user)

    # ------------------------------------------------------------------ ad-free

    async def set_ad_free(self, user: User, enabled: bool) -> dict:
        """Toggle the ``$5/mo`` ad-free add-on. Requires an active Plus plan —
        ad-free is an add-on to a paid subscription, not a standalone."""
        self._require_enabled()
        sub = await self._get_subscription(user.id)
        if sub is None:
            raise BadRequestException("No subscription found.")
        plan = await self._resolve_and_persist_expiry(sub)
        if enabled and plan != PLAN_PLUS:
            raise BadRequestException("Subscribe to Plus before adding the ad-free upgrade.")
        if bool(sub.ad_free) == enabled:
            return await self.get_status(user)
        # Reflect the add-on on the provider subscription (Stripe adds/removes a
        # $5/mo line item; the mock is a no-op).
        if sub.provider_subscription_id:
            try:
                get_billing_provider().set_ad_free(
                    subscription_id=sub.provider_subscription_id, enabled=enabled
                )
            except BillingError as e:
                raise BadRequestException(str(e)) from e
        sub.ad_free = enabled
        await self.db.flush()
        await self._log_event(
            user_id=user.id,
            event_type=EVENT_ADFREE_ENABLED if enabled else EVENT_ADFREE_DISABLED,
            amount_cents=settings.billing_student_adfree_price_cents if enabled else 0,
        )
        return await self.get_status(user)

    # ------------------------------------------------------------------- cancel

    async def cancel(self, user: User) -> dict:
        """Cancel at period end — access continues until the paid period closes."""
        self._require_enabled()
        sub = await self._get_subscription(user.id)
        if sub is None or sub.plan != PLAN_PLUS:
            raise BadRequestException("No active subscription to cancel.")
        provider = get_billing_provider()
        if sub.provider_subscription_id:
            provider.cancel_subscription(
                subscription_id=sub.provider_subscription_id, at_period_end=True
            )
        sub.cancel_at_period_end = True
        sub.canceled_at = datetime.now(UTC)
        await self.db.flush()
        await self._log_event(user_id=user.id, event_type=EVENT_SUBSCRIPTION_CANCELED)
        return await self.get_status(user)

    async def get_history(self, user: User, limit: int = 50) -> list[dict]:
        rows = (
            (
                await self.db.execute(
                    select(BillingEvent)
                    .where(BillingEvent.user_id == user.id)
                    .order_by(BillingEvent.occurred_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [_event_public(e) for e in rows]

    # ------------------------------------------------------- institution billing

    async def record_applicant_charge(
        self, application: Application
    ) -> InstitutionApplicantCharge | None:
        """Record the ``$15`` charge for a unique applicant an institution
        processes (Spec 06 §4.2). Deduped on (institution, student). Defensive:
        never raises into the application-submission flow."""
        if not settings.billing_enabled:
            return None
        try:
            program = await self.db.get(Program, application.program_id)
            if program is None or program.institution_id is None:
                return None
            institution_id = program.institution_id
            existing = (
                await self.db.execute(
                    select(InstitutionApplicantCharge).where(
                        InstitutionApplicantCharge.institution_id == institution_id,
                        InstitutionApplicantCharge.student_id == application.student_id,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                return existing  # already billed for this unique applicant

            provider = get_billing_provider()
            amount = settings.billing_institution_per_applicant_cents
            charge = InstitutionApplicantCharge(
                institution_id=institution_id,
                student_id=application.student_id,
                application_id=application.id,
                amount_cents=amount,
                status="pending",
                provider=provider.name,
            )
            try:
                result = provider.charge(
                    customer_id=f"inst_{institution_id}",
                    amount_cents=amount,
                    description="UniPaith applicant processing fee",
                )
                charge.status = "charged"
                charge.provider_ref = result.provider_ref
                charge.charged_at = datetime.now(UTC)
            except BillingError as e:
                charge.status = "failed"
                logger.warning("applicant charge failed: %s", e)
            self.db.add(charge)
            await self.db.flush()
            await self._log_event(
                institution_id=institution_id,
                event_type=EVENT_APPLICANT_CHARGED,
                amount_cents=amount,
                status="succeeded" if charge.status == "charged" else "failed",
                provider=provider.name,
                provider_ref=charge.provider_ref,
                metadata={"student_id": str(application.student_id)},
            )
            return charge
        except Exception:  # never break submission on a billing hiccup
            logger.exception("record_applicant_charge failed for app %s", application.id)
            return None

    async def get_institution_usage(self, institution_id: UUID, limit: int = 100) -> dict:
        rows = (
            (
                await self.db.execute(
                    select(InstitutionApplicantCharge)
                    .where(InstitutionApplicantCharge.institution_id == institution_id)
                    .order_by(InstitutionApplicantCharge.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        charged = [r for r in rows if r.status == "charged"]
        total_cents = sum(r.amount_cents for r in charged)
        return {
            "enabled": settings.billing_enabled,
            "unique_applicants": len(rows),
            "billable_applicants": len(charged),
            "per_applicant_cents": settings.billing_institution_per_applicant_cents,
            "total_cents": total_cents,
            "currency": settings.billing_currency,
            "charges": [_charge_public(r) for r in rows[:limit]],
        }

    # ----------------------------------------------------------- stripe webhook

    async def handle_stripe_webhook(self, payload: bytes, sig_header: str | None) -> dict:
        """Verify a Stripe webhook signature and reconcile local state with the
        async lifecycle events Stripe owns (renewals, failures, cancellations).
        Raises BadRequestException on a bad signature so the route returns 400."""
        import stripe

        if not settings.stripe_webhook_secret:
            raise BadRequestException("Stripe webhook secret is not configured.")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header or "", settings.stripe_webhook_secret
            )
        except Exception as e:  # noqa: BLE001 — any failure = reject
            raise BadRequestException(f"Invalid Stripe webhook signature: {e}") from e

        handled = await self._apply_stripe_event(event["type"], event["data"]["object"])
        await self.db.flush()
        return {"received": True, "type": event["type"], "handled": handled}

    async def _apply_stripe_event(self, event_type: str, obj: dict) -> bool:
        # Resolve the affected local subscription from the Stripe object.
        if event_type.startswith("customer.subscription"):
            sub_ref = obj.get("id")
        else:  # invoice.* events carry the subscription id
            sub_ref = obj.get("subscription")
        if not sub_ref:
            return False
        sub = (
            await self.db.execute(
                select(Subscription).where(Subscription.provider_subscription_id == sub_ref)
            )
        ).scalar_one_or_none()
        if sub is None:
            return False

        if event_type == "customer.subscription.updated":
            stripe_status = obj.get("status", sub.status)
            sub.cancel_at_period_end = bool(obj.get("cancel_at_period_end"))
            sub.current_period_end = _epoch(obj.get("current_period_end"))
            if stripe_status == "active":
                sub.status = STATUS_ACTIVE
                sub.plan = PLAN_PLUS
            elif stripe_status == "past_due":
                sub.status = STATUS_PAST_DUE
            elif stripe_status in ("canceled", "unpaid", "incomplete_expired"):
                sub.status = STATUS_CANCELED
                sub.plan = PLAN_FREE
            return True

        if event_type == "customer.subscription.deleted":
            sub.status = STATUS_CANCELED
            sub.plan = PLAN_FREE
            sub.cancel_at_period_end = False
            sub.canceled_at = datetime.now(UTC)
            return True

        if event_type == "invoice.payment_succeeded":
            sub.status = STATUS_ACTIVE
            sub.plan = PLAN_PLUS
            sub.current_period_end = _epoch(obj.get("period_end")) or sub.current_period_end
            await self._log_event(
                user_id=sub.user_id,
                event_type=EVENT_PAYMENT_SUCCEEDED,
                amount_cents=int(obj.get("amount_paid") or 0),
                provider="stripe",
                provider_ref=obj.get("id"),
            )
            return True

        if event_type == "invoice.payment_failed":
            sub.status = STATUS_PAST_DUE
            await self._log_event(
                user_id=sub.user_id,
                event_type=EVENT_PAYMENT_FAILED,
                status="failed",
                provider="stripe",
                provider_ref=obj.get("id"),
            )
            return True

        return False

    # ------------------------------------------------------------------ helpers

    def _prices(self) -> dict:
        return {
            "student_plan_cents": settings.billing_student_plan_price_cents,
            "student_adfree_cents": settings.billing_student_adfree_price_cents,
            "institution_per_applicant_cents": settings.billing_institution_per_applicant_cents,
            "trial_days": settings.billing_trial_days,
            "currency": settings.billing_currency,
        }

    def _require_enabled(self) -> None:
        if not settings.billing_enabled:
            raise BadRequestException("Billing is not enabled in this environment.")

    async def _get_subscription(self, user_id: UUID) -> Subscription | None:
        return (
            await self.db.execute(select(Subscription).where(Subscription.user_id == user_id))
        ).scalar_one_or_none()

    async def _list_payment_methods(self, user_id: UUID) -> list[PaymentMethod]:
        return list(
            (await self.db.execute(select(PaymentMethod).where(PaymentMethod.user_id == user_id)))
            .scalars()
            .all()
        )

    async def _get_default_payment_method(self, user_id: UUID) -> PaymentMethod | None:
        return (
            (
                await self.db.execute(
                    select(PaymentMethod)
                    .where(PaymentMethod.user_id == user_id, PaymentMethod.is_default.is_(True))
                    .order_by(PaymentMethod.created_at.desc())
                )
            )
            .scalars()
            .first()
        )

    async def _resolve_and_persist_expiry(self, sub: Subscription) -> str:
        """Effective plan, persisting a lapsed-trial transition to ``free``."""
        if sub.status == STATUS_TRIALING and sub.trial_ends_at is not None:
            if datetime.now(UTC) >= _aware(sub.trial_ends_at):
                sub.plan = PLAN_FREE
                sub.status = STATUS_FREE
                if sub.id is not None:
                    await self.db.flush()
        return sub.plan

    def _trial_days_left(self, sub: Subscription) -> int | None:
        if sub.status != STATUS_TRIALING or sub.trial_ends_at is None:
            return None
        delta = _aware(sub.trial_ends_at) - datetime.now(UTC)
        return max(0, math.ceil(delta.total_seconds() / 86400))

    async def _log_event(
        self,
        *,
        event_type: str,
        user_id: UUID | None = None,
        institution_id: UUID | None = None,
        amount_cents: int = 0,
        currency: str | None = None,
        status: str = "succeeded",
        provider: str | None = None,
        provider_ref: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self.db.add(
            BillingEvent(
                user_id=user_id,
                institution_id=institution_id,
                event_type=event_type,
                amount_cents=amount_cents,
                currency=currency or settings.billing_currency,
                status=status,
                provider=provider,
                provider_ref=provider_ref,
                event_metadata=metadata,
            )
        )
        await self.db.flush()


# --------------------------------------------------------------- serialization


def _aware(dt: datetime) -> datetime:
    """Treat naive timestamps (from some DB drivers) as UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _epoch(ts: int | None) -> datetime | None:
    """Stripe sends Unix-epoch seconds; convert to an aware UTC datetime."""
    return datetime.fromtimestamp(ts, UTC) if ts else None


def _iso(dt: datetime | None) -> str | None:
    return _aware(dt).isoformat() if dt is not None else None


def _pm_public(pm: PaymentMethod | None) -> dict | None:
    if pm is None:
        return None
    return {
        "id": str(pm.id),
        "brand": pm.brand,
        "last4": pm.last4,
        "exp_month": pm.exp_month,
        "exp_year": pm.exp_year,
    }


def _event_public(e: BillingEvent) -> dict:
    return {
        "id": str(e.id),
        "event_type": e.event_type,
        "amount_cents": e.amount_cents,
        "currency": e.currency,
        "status": e.status,
        "occurred_at": _iso(e.occurred_at),
        "metadata": e.event_metadata,
    }


def _charge_public(c: InstitutionApplicantCharge) -> dict:
    return {
        "id": str(c.id),
        "student_id": str(c.student_id),
        "application_id": str(c.application_id) if c.application_id else None,
        "amount_cents": c.amount_cents,
        "currency": c.currency,
        "status": c.status,
        "charged_at": _iso(c.charged_at),
        "created_at": _iso(c.created_at),
    }
