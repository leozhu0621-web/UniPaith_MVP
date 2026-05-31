"""Spec 07 (Product Context §4) — subscription / billing API.

Student endpoints under ``/api/v1/students/me/subscription`` plus a public plan
catalog at ``/api/v1/billing/plans`` that drives the pricing page.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.billing import (
    AdFreeRequest,
    PlanCatalogResponse,
    SubscribeRequest,
    SubscriptionResponse,
)
from unipaith.services.subscription_service import SubscriptionService

router = APIRouter(tags=["billing"])


def _svc(db: AsyncSession) -> SubscriptionService:
    return SubscriptionService(db)


@router.get("/students/me/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Current student's subscription. Lazily starts a 7-day trial on first read."""
    return await _svc(db).status_view(user.id)


@router.post("/students/me/subscription/subscribe", response_model=SubscriptionResponse)
async def subscribe(
    body: SubscribeRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Convert to UniPaith Pro with a mock card-on-file (no real PSP)."""
    return await _svc(db).subscribe(user.id, body)


@router.post("/students/me/subscription/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).cancel(user.id)


@router.post("/students/me/subscription/resume", response_model=SubscriptionResponse)
async def resume_subscription(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).resume(user.id)


@router.put("/students/me/subscription/ad-free", response_model=SubscriptionResponse)
async def set_ad_free(
    body: AdFreeRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).set_ad_free(user.id, body)


@router.get("/billing/plans", response_model=PlanCatalogResponse)
async def get_plans():
    """Public — plan catalog for the pricing page. No auth required."""
    return SubscriptionService.plan_catalog()
