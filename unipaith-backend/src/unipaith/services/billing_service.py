"""Billing service (Spec 07 §4, 21 §2.7/§3.6).

Student subscription lifecycle (trial → paywall, Spec 05 §9) plus institution
usage billing ($15/unique applicant, Spec 07 §4.2). Payment movement is
abstracted behind ``PaymentProvider`` so a real Stripe provider (Spec 39) can
swap in without touching call sites; the MVP uses ``MockPaymentProvider``.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import Application
from unipaith.models.billing import StudentSubscription
from unipaith.models.institution import Institution, Program
from unipaith.schemas.billing import (
    InstitutionBillingResponse,
    InvoiceItem,
    StudentBillingResponse,
)

# Provider-portability seam — shared with the Spec 39 fee/deposit layer
# (Spec 39 §12 "same PaymentProvider"). Re-exported for back-compat.
from unipaith.services.payments.provider import (  # noqa: E402
    MockPaymentProvider,
    PaymentError,
    PaymentMethod,
    PaymentProvider,
    ProviderEvent,
    get_payment_provider,
)

__all__ = ["BillingService", "PaymentProvider", "MockPaymentProvider", "PaymentMethod"]


def _period_after(start: datetime, days: int = 30) -> datetime:
    return start + timedelta(days=days)


class BillingService:
    def __init__(self, db: AsyncSession, provider: PaymentProvider | None = None):
        self.db = db
        # Use the configured provider (Stripe when payments_provider="stripe" +
        # keys present, else mock). The factory never raises into the request.
        self.provider = provider or get_payment_provider()

    # ── Student ──────────────────────────────────────────────────────────
    async def get_or_create_subscription(self, user_id: UUID) -> StudentSubscription:
        result = await self.db.execute(
            select(StudentSubscription).where(StudentSubscription.user_id == user_id)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            now = datetime.now(UTC)
            sub = StudentSubscription(
                user_id=user_id,
                status="trialing",
                trial_started_at=now,
                trial_ends_at=now + timedelta(days=settings.student_trial_days),
            )
            self.db.add(sub)
            await self.db.flush()
            await self.db.refresh(sub)
        return sub

    async def _reconcile(self, sub: StudentSubscription) -> StudentSubscription:
        """Lazily advance lapsed states on read so the stored row stays honest:
        an expired trial with a card auto-converts to active; without a card it
        expires; a canceled plan past its period expires."""
        now = datetime.now(UTC)
        has_card = bool(sub.payment_method_last4)

        if sub.status == "trialing" and sub.trial_ends_at and now >= sub.trial_ends_at:
            if has_card:
                sub.status = "active"
                sub.current_period_end = _period_after(sub.trial_ends_at)
            else:
                sub.status = "expired"
            await self.db.flush()
        elif (
            sub.status in ("active", "canceled")
            and sub.current_period_end
            and now >= sub.current_period_end
        ):
            if sub.status == "canceled":
                sub.status = "expired"
            else:
                # Active plan renews for another period (mock auto-renew).
                sub.current_period_end = _period_after(sub.current_period_end)
            await self.db.flush()
        return sub

    @staticmethod
    def _is_premium(sub: StudentSubscription) -> bool:
        now = datetime.now(UTC)
        if sub.status == "active":
            return True
        if sub.status == "trialing":
            return not sub.trial_ends_at or now < sub.trial_ends_at
        if sub.status == "canceled":
            return bool(sub.current_period_end and now < sub.current_period_end)
        return False

    def _to_response(self, sub: StudentSubscription) -> StudentBillingResponse:
        now = datetime.now(UTC)
        is_premium = self._is_premium(sub)

        trial_days_left: int | None = None
        if sub.status == "trialing" and sub.trial_ends_at:
            remaining = (sub.trial_ends_at - now).total_seconds()
            trial_days_left = max(0, math.ceil(remaining / 86400))

        monthly_total = settings.student_plan_price_usd + (
            settings.student_ad_free_addon_usd if sub.ad_free else 0
        )

        invoices: list[InvoiceItem] = []
        bills_next = (
            sub.status in ("active", "canceled")
            and sub.current_period_end is not None
            and not sub.cancel_at_period_end
        )
        if bills_next:
            invoices.append(
                InvoiceItem(
                    id="upcoming",
                    date=sub.current_period_end,
                    amount_usd=float(monthly_total),
                    status="upcoming",
                    description="UniPaith Plus — next month",
                )
            )

        provider_name = self.provider.name
        return StudentBillingResponse(
            status=sub.status,  # type: ignore[arg-type]
            plan_price_usd=settings.student_plan_price_usd,
            ad_free=sub.ad_free,
            ad_free_addon_usd=settings.student_ad_free_addon_usd,
            monthly_total_usd=monthly_total,
            trial_ends_at=sub.trial_ends_at,
            trial_days_left=trial_days_left,
            current_period_end=sub.current_period_end,
            cancel_at_period_end=sub.cancel_at_period_end,
            has_payment_method=bool(sub.payment_method_last4),
            payment_method_brand=sub.payment_method_brand,
            payment_method_last4=sub.payment_method_last4,
            is_premium=is_premium,
            paywall_enforced=settings.paywall_enforced,
            invoices=invoices,
            provider=provider_name,
            # Client-safe key only — drives Stripe Elements when provider="stripe".
            publishable_key=(
                settings.stripe_publishable_key or None if provider_name == "stripe" else None
            ),
        )

    async def get_student_billing(self, user_id: UUID) -> StudentBillingResponse:
        sub = await self.get_or_create_subscription(user_id)
        sub = await self._reconcile(sub)
        return self._to_response(sub)

    async def upgrade(
        self,
        user_id: UUID,
        *,
        payment_method_token: str | None = None,
        email: str | None = None,
    ) -> StudentBillingResponse:
        """Add a card on file and move to the paid $15/mo plan.

        With a real provider the ``payment_method_token`` (Stripe Elements
        ``pm_...``) drives a real customer + recurring subscription; the mock
        fabricates a test card. A declined card surfaces as a 400."""
        sub = await self.get_or_create_subscription(user_id)
        if not sub.payment_method_last4:
            try:
                pm = self.provider.attach_payment_method(
                    user_id, payment_method_token=payment_method_token, email=email
                )
            except PaymentError as e:
                raise BadRequestException(str(e)) from e
            sub.provider = self.provider.name
            sub.provider_customer_id = pm.customer_id
            sub.provider_subscription_id = pm.subscription_id
            sub.payment_method_brand = pm.brand
            sub.payment_method_last4 = pm.last4
        sub.status = "active"
        sub.cancel_at_period_end = False
        sub.canceled_at = None
        sub.current_period_end = _period_after(datetime.now(UTC))
        await self.db.flush()
        await self.db.refresh(sub)
        return self._to_response(sub)

    async def set_ad_free(self, user_id: UUID, enabled: bool) -> StudentBillingResponse:
        sub = await self.get_or_create_subscription(user_id)
        sub = await self._reconcile(sub)
        # Reflect the add-on on a real provider subscription (Stripe adds/removes
        # a $5/mo line item; the mock is a no-op).
        if sub.provider != "mock" and sub.provider_subscription_id and sub.ad_free != enabled:
            try:
                self.provider.set_subscription_ad_free(
                    subscription_id=sub.provider_subscription_id, enabled=enabled
                )
            except PaymentError as e:
                raise BadRequestException(str(e)) from e
        sub.ad_free = enabled
        await self.db.flush()
        await self.db.refresh(sub)
        return self._to_response(sub)

    async def cancel(self, user_id: UUID) -> StudentBillingResponse:
        sub = await self.get_or_create_subscription(user_id)
        sub = await self._reconcile(sub)
        # Cancel at the provider too (at period end) for a real subscription.
        if sub.provider != "mock" and sub.provider_subscription_id:
            try:
                self.provider.cancel_subscription(
                    subscription_id=sub.provider_subscription_id, at_period_end=True
                )
            except PaymentError as e:
                raise BadRequestException(str(e)) from e
        sub.cancel_at_period_end = True
        sub.canceled_at = datetime.now(UTC)
        if sub.status == "active":
            sub.status = "canceled"
        await self.db.flush()
        await self.db.refresh(sub)
        return self._to_response(sub)

    async def resume(self, user_id: UUID) -> StudentBillingResponse:
        sub = await self.get_or_create_subscription(user_id)
        sub.cancel_at_period_end = False
        sub.canceled_at = None
        if sub.status == "canceled" and sub.payment_method_last4:
            sub.status = "active"
        await self.db.flush()
        await self.db.refresh(sub)
        return self._to_response(sub)

    async def handle_subscription_event(self, event: ProviderEvent) -> bool:
        """Reconcile local subscription state from a Stripe webhook (Spec 07
        §4.1) — the async lifecycle Stripe owns (renewals, cancellations). A
        failed renewal stays in grace (Stripe dunning) until deletion. Returns
        True when a row was updated."""
        if not event.subscription_id:
            return False
        result = await self.db.execute(
            select(StudentSubscription).where(
                StudentSubscription.provider_subscription_id == event.subscription_id
            )
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            return False
        if event.type == "invoice.payment_succeeded":
            sub.status = "active"
            sub.current_period_end = _period_after(datetime.now(UTC))
        elif event.type == "customer.subscription.deleted":
            sub.status = "expired"
            sub.cancel_at_period_end = False
        elif event.type == "customer.subscription.updated":
            if event.subscription_status == "active":
                sub.status = "active"
            elif event.subscription_status in ("canceled", "unpaid", "incomplete_expired"):
                sub.status = "expired"
        # invoice.payment_failed → grace period (Stripe retries); no change here.
        await self.db.flush()
        return True

    # ── Institution ──────────────────────────────────────────────────────
    async def _institution_for_admin(self, user_id: UUID) -> Institution:
        result = await self.db.execute(
            select(Institution).where(Institution.admin_user_id == user_id)
        )
        inst = result.scalar_one_or_none()
        if inst is None:
            raise NotFoundException("Institution not found")
        return inst

    async def get_institution_billing(self, user_id: UUID) -> InstitutionBillingResponse:
        inst = await self._institution_for_admin(user_id)
        now = datetime.now(UTC)
        cycle_start = datetime(now.year, now.month, 1, tzinfo=UTC)
        cycle_end = (
            datetime(now.year + 1, 1, 1, tzinfo=UTC)
            if now.month == 12
            else datetime(now.year, now.month + 1, 1, tzinfo=UTC)
        )

        # Unique applicants whose application to one of this institution's
        # programs was submitted in the current cycle (Spec 07 §4.2).
        stmt = (
            select(func.count(func.distinct(Application.student_id)))
            .select_from(Application)
            .join(Program, Program.id == Application.program_id)
            .where(
                Program.institution_id == inst.id,
                Application.submitted_at.is_not(None),
                Application.submitted_at >= cycle_start,
                Application.submitted_at < cycle_end,
            )
        )
        applicants = (await self.db.execute(stmt)).scalar_one() or 0
        charge = float(applicants * settings.institution_per_applicant_usd)

        return InstitutionBillingResponse(
            per_applicant_usd=settings.institution_per_applicant_usd,
            cycle_label=cycle_start.strftime("%B %Y"),
            cycle_start=cycle_start,
            cycle_end=cycle_end,
            applicants_processed=applicants,
            current_charge_usd=charge,
            has_payment_method=False,
            invoices=[],
        )
