"""Spec 07 (Product Context §4) — subscription / monetization service.

Owns the 7-day trial → paywall → feature-gating lifecycle and the public plan
catalog that drives the pricing page. Payment is a mock card-on-file stub; the
method surface is shaped so a real processor replaces ``subscribe`` without
touching callers.

Lifecycle (``status``):
    trialing  — inside the 7-day window; full (pro) access.
    active    — subscribed; pro access.
    canceled  — user canceled; pro access until ``current_period_end``.
    expired   — trial lapsed without subscribing, or a canceled period ended;
                free access only.
Transitions to ``expired`` are applied lazily on read so status + entitlements
stay honest without a background job.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.billing import StudentSubscription
from unipaith.models.student import StudentProfile
from unipaith.schemas.billing import (
    AdFreeRequest,
    InstitutionPlanCatalog,
    PlanCatalogResponse,
    PlanFeature,
    StudentPlanCatalog,
    SubscribeRequest,
    SubscriptionResponse,
)

TRIAL_DAYS = 7
BILLING_PERIOD_DAYS = 30

STUDENT_PRICE_MONTHLY = 15
AD_FREE_ADDON_MONTHLY = 5
INSTITUTION_PRICE_PER_APPLICANT = 15

# Feature keys (Product Context §4.1 free-vs-paid ladder).
FREE_FEATURES = (
    "portable_profile",
    "baseline_readiness",
    "limited_matching",
)
PRO_FEATURES = (
    "expanded_matching",
    "deadline_alerts",
    "scholarship_tools",
    "writing_workflows",
    "priority_support",
)


def _now() -> datetime:
    return datetime.now(UTC)


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _student_id(self, user_id: UUID) -> UUID:
        result = await self.db.execute(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        sid = result.scalar_one_or_none()
        if sid is None:
            raise NotFoundException("Student profile not found")
        return sid

    async def get_or_create(self, user_id: UUID) -> StudentSubscription:
        student_id = await self._student_id(user_id)
        result = await self.db.execute(
            select(StudentSubscription).where(StudentSubscription.student_id == student_id)
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            now = _now()
            sub = StudentSubscription(
                student_id=student_id,
                plan="free",
                status="trialing",
                trial_started_at=now,
                trial_ends_at=now + timedelta(days=TRIAL_DAYS),
            )
            self.db.add(sub)
            await self.db.flush()
            await self.db.refresh(sub)
        else:
            self._apply_lazy_transitions(sub)
        return sub

    @staticmethod
    def _apply_lazy_transitions(sub: StudentSubscription) -> None:
        now = _now()
        if sub.status == "trialing" and sub.trial_ends_at and now >= sub.trial_ends_at:
            sub.status = "expired"
        elif sub.status == "canceled" and sub.current_period_end and now >= sub.current_period_end:
            sub.status = "expired"

    @staticmethod
    def _has_pro_access(sub: StudentSubscription) -> bool:
        now = _now()
        if sub.status == "active":
            return True
        if sub.status == "trialing" and sub.trial_ends_at and now < sub.trial_ends_at:
            return True
        if sub.status == "canceled" and sub.current_period_end and now < sub.current_period_end:
            return True
        return False

    @classmethod
    def _entitlements(cls, sub: StudentSubscription) -> list[str]:
        feats = list(FREE_FEATURES)
        if cls._has_pro_access(sub):
            feats.extend(PRO_FEATURES)
        return feats

    @classmethod
    def is_entitled(cls, sub: StudentSubscription, feature: str) -> bool:
        return feature in cls._entitlements(sub)

    @classmethod
    def _view(cls, sub: StudentSubscription) -> SubscriptionResponse:
        now = _now()
        has_pro = cls._has_pro_access(sub)
        is_trialing = bool(
            sub.status == "trialing" and sub.trial_ends_at and now < sub.trial_ends_at
        )
        days_left: int | None = None
        if is_trialing and sub.trial_ends_at:
            secs = (sub.trial_ends_at - now).total_seconds()
            days_left = max(0, math.ceil(secs / 86400))
        return SubscriptionResponse(
            status=sub.status,
            plan=sub.plan,
            effective_plan="pro" if has_pro else "free",
            ad_free=sub.ad_free,
            is_trialing=is_trialing,
            is_active=sub.status == "active",
            has_pro_access=has_pro,
            trial_ends_at=sub.trial_ends_at,
            current_period_end=sub.current_period_end,
            days_left_in_trial=days_left,
            card_brand=sub.card_brand,
            card_last4=sub.card_last4,
            entitlements=cls._entitlements(sub),
        )

    async def status_view(self, user_id: UUID) -> SubscriptionResponse:
        sub = await self.get_or_create(user_id)
        await self.db.flush()
        return self._view(sub)

    async def subscribe(self, user_id: UUID, body: SubscribeRequest) -> SubscriptionResponse:
        sub = await self.get_or_create(user_id)
        now = _now()
        sub.plan = "pro"
        sub.status = "active"
        sub.current_period_end = now + timedelta(days=BILLING_PERIOD_DAYS)
        sub.canceled_at = None
        sub.card_brand = body.card_brand
        sub.card_last4 = body.card_last4
        if body.ad_free:
            sub.ad_free = True
        await self.db.flush()
        await self.db.refresh(sub)
        return self._view(sub)

    async def cancel(self, user_id: UUID) -> SubscriptionResponse:
        sub = await self.get_or_create(user_id)
        if sub.status != "active":
            raise BadRequestException("Only an active subscription can be canceled")
        sub.status = "canceled"
        sub.canceled_at = _now()
        await self.db.flush()
        await self.db.refresh(sub)
        return self._view(sub)

    async def resume(self, user_id: UUID) -> SubscriptionResponse:
        sub = await self.get_or_create(user_id)
        if sub.status != "canceled":
            raise BadRequestException("Only a canceled subscription can be resumed")
        sub.status = "active"
        sub.canceled_at = None
        await self.db.flush()
        await self.db.refresh(sub)
        return self._view(sub)

    async def set_ad_free(self, user_id: UUID, body: AdFreeRequest) -> SubscriptionResponse:
        sub = await self.get_or_create(user_id)
        sub.ad_free = body.enabled
        await self.db.flush()
        await self.db.refresh(sub)
        return self._view(sub)

    @staticmethod
    def plan_catalog() -> PlanCatalogResponse:
        features = [
            PlanFeature(label="Portable universal profile", free=True, pro=True),
            PlanFeature(label="Baseline readiness check", free=True, pro=True),
            PlanFeature(label="Limited program matching", free=True, pro=True),
            PlanFeature(label="Expanded matching with full reasoning", free=False, pro=True),
            PlanFeature(label="Real-time deadline alerts", free=False, pro=True),
            PlanFeature(label="Scholarship and affordability tools", free=False, pro=True),
            PlanFeature(label="Structured writing workflows", free=False, pro=True),
            PlanFeature(label="Priority support", free=False, pro=True),
        ]
        return PlanCatalogResponse(
            student=StudentPlanCatalog(
                id="student_pro",
                name="UniPaith Pro",
                tagline="Everyone's private college counselor",
                price_monthly=STUDENT_PRICE_MONTHLY,
                currency="USD",
                trial_days=TRIAL_DAYS,
                ad_free_addon_monthly=AD_FREE_ADDON_MONTHLY,
            ),
            institution=InstitutionPlanCatalog(
                id="institution",
                name="Institution",
                tagline="The admission operating system",
                price_per_applicant=INSTITUTION_PRICE_PER_APPLICANT,
                currency="USD",
                billing_model="per_applicant",
            ),
            features=features,
        )
