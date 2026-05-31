"""Billing API (Spec 07 §4, 21 §2.7/§3.6).

Student subscription state + management (trial → $15/mo plan + $5/mo ad-free)
and institution usage billing ($15/unique applicant). Real charge movement is
Phase-2 (Spec 39); this serves plan state + manage actions over a mock provider.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
from unipaith.schemas.billing import (
    AdFreeRequest,
    InstitutionBillingResponse,
    StudentBillingResponse,
)
from unipaith.services.billing_service import BillingService

router = APIRouter(tags=["billing"])


def _svc(db: AsyncSession) -> BillingService:
    return BillingService(db)


# ── Student ──────────────────────────────────────────────────────────────
@router.get("/students/me/billing", response_model=StudentBillingResponse)
async def get_student_billing(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_student_billing(user.id)


@router.post("/students/me/billing/upgrade", response_model=StudentBillingResponse)
async def upgrade_student_billing(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).upgrade(user.id)


@router.post("/students/me/billing/ad-free", response_model=StudentBillingResponse)
async def set_ad_free(
    body: AdFreeRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).set_ad_free(user.id, body.enabled)


@router.post("/students/me/billing/cancel", response_model=StudentBillingResponse)
async def cancel_student_billing(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).cancel(user.id)


@router.post("/students/me/billing/resume", response_model=StudentBillingResponse)
async def resume_student_billing(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).resume(user.id)


# ── Institution ────────────────────────────────────────────────────────────
@router.get("/institutions/me/billing", response_model=InstitutionBillingResponse)
async def get_institution_billing(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_institution_billing(user.id)
