"""Billing API (Spec 06 §4).

Student endpoints under ``/students/me/billing`` (trial status, card-on-file,
subscribe, ad-free, cancel, history) and an institution usage endpoint under
``/institutions/me/billing``. Also exposes ``require_entitlement(feature)`` — the
402 paywall guard other routers attach to paid surfaces.

All write endpoints raise 400 when ``billing_enabled`` is False (the service
enforces it); the read endpoints stay valid and report ``enabled: false`` so the
UI hides the paywall.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import PaymentRequiredException
from unipaith.database import get_db
from unipaith.dependencies import (
    get_current_user,
    require_institution_admin,
    require_student,
)
from unipaith.models.user import User
from unipaith.services.billing.provider import CardInput
from unipaith.services.billing_service import BillingService
from unipaith.services.entitlements import Feature, is_entitled
from unipaith.services.institution_service import InstitutionService

router = APIRouter(prefix="/students/me/billing", tags=["billing"])
institution_router = APIRouter(prefix="/institutions/me/billing", tags=["billing"])
# Public (unauthenticated) — Stripe posts here; auth is the signature, not a token.
webhook_router = APIRouter(prefix="/billing", tags=["billing"])


# --------------------------------------------------------------- request bodies


class PaymentMethodRequest(BaseModel):
    # Preferred: an opaque token from the client SDK (PCI-safe). Dev/mock also
    # accepts raw fields — never send a real PAN to a real provider.
    token: str | None = None
    number: str | None = Field(default=None, description="Mock/dev only — never a real PAN")
    exp_month: int | None = Field(default=None, ge=1, le=12)
    exp_year: int | None = Field(default=None, ge=2024, le=2099)
    cvc: str | None = None
    name: str | None = None

    def to_card(self) -> CardInput:
        return CardInput(
            token=self.token,
            number=self.number,
            exp_month=self.exp_month,
            exp_year=self.exp_year,
            cvc=self.cvc,
            name=self.name,
        )


class AdFreeRequest(BaseModel):
    enabled: bool


# ---------------------------------------------------------- entitlement guard


def require_entitlement(
    feature: Feature,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """Build a dependency that 402s when the student's plan does not include
    ``feature``. No-op when billing is disabled (effective plan = plus).

    Usage on a paid route:
        dependencies=[Depends(require_entitlement(Feature.WORKSHOPS))]
    """

    async def _guard(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        plan = await BillingService(db).effective_plan(user)
        if not is_entitled(plan, feature):
            raise PaymentRequiredException(
                "Your free plan does not include this feature. Start a subscription to continue.",
                feature=feature.value,
            )
        return user

    return _guard


# --------------------------------------------------------------- student routes


@router.get("", response_model=dict)
async def get_billing_status(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await BillingService(db).get_status(user)


@router.get("/entitlements", response_model=dict)
async def get_entitlements(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    status = await BillingService(db).get_status(user)
    return {
        "plan": status["plan"],
        "entitlements": status["entitlements"],
        "feature_matrix": status["feature_matrix"],
    }


@router.post("/payment-method", response_model=dict)
async def add_payment_method(
    body: PaymentMethodRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    pm = await BillingService(db).add_payment_method(user, body.to_card())
    return {"payment_method": pm}


@router.post("/subscribe", response_model=dict)
async def subscribe(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    result = await BillingService(db).subscribe(user)
    return result


@router.post("/ad-free", response_model=dict)
async def set_ad_free(
    body: AdFreeRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    result = await BillingService(db).set_ad_free(user, body.enabled)
    return result


@router.post("/cancel", response_model=dict)
async def cancel_subscription(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    result = await BillingService(db).cancel(user)
    return result


@router.get("/history", response_model=list)
async def get_history(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await BillingService(db).get_history(user)


# ----------------------------------------------------------- institution routes


@institution_router.get("/usage", response_model=dict)
async def get_institution_usage(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    institution = await InstitutionService(db).get_institution(user.id)
    return await BillingService(db).get_institution_usage(institution.id)


# ------------------------------------------------------------------ webhook


@webhook_router.post("/stripe/webhook", response_model=dict)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Stripe → us. Verifies the signature against STRIPE_WEBHOOK_SECRET and
    reconciles local subscription state (renewals, failures, cancellations).
    Public: the signature is the auth, so there is no bearer token."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    return await BillingService(db).handle_stripe_webhook(payload, sig)
