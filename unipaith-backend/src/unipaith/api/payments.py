"""Payments API (Spec 39 — Fees & Payments).

Student: application-fee checkout / fee-waiver request / enrollment-deposit
checkout / in-app mock confirm / cost tracker.
Institution: fee config, waiver queue + decisions, payments list + refunds.

The public Stripe webhook (``POST /webhooks/stripe``) lives in ``router.py`` so
it sits outside this prefixed, auth-gated router.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin, require_student
from unipaith.models.user import User
from unipaith.schemas.payment import (
    FeeConfigUpdate,
    RefundRequest,
    RequestWaiverRequest,
    WaiverDecisionRequest,
)
from unipaith.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


def _svc(db: AsyncSession) -> PaymentService:
    return PaymentService(db)


# ── Student ──────────────────────────────────────────────────────────────────


@router.get("/applications/{application_id}")
async def get_cost_tracker(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Application cost tracker (Spec 15 §2A / 39 §6): fee + deposit status."""
    return await _svc(db).cost_tracker(user, application_id)


@router.post("/applications/{application_id}/pay-fee")
async def pay_application_fee(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Open checkout for the application fee → returns a checkout session."""
    return await _svc(db).create_fee_checkout(user, application_id)


@router.post("/applications/{application_id}/request-waiver")
async def request_fee_waiver(
    application_id: UUID,
    body: RequestWaiverRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    evidence: dict = {}
    if body.note:
        evidence["note"] = body.note
    if body.evidence_url:
        evidence["url"] = body.evidence_url
    return await _svc(db).request_waiver(user, application_id, body.basis, evidence or None)


@router.post("/applications/{application_id}/pay-deposit")
async def pay_enrollment_deposit(
    application_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).create_deposit_checkout(user, application_id)


@router.post("/{payment_id}/confirm-mock")
async def confirm_mock_payment(
    payment_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Complete an in-app mock checkout (mock provider only; 404 in stripe mode)."""
    return await _svc(db).confirm_mock_payment(user, payment_id)


# ── Institution ────────────────────────────────────────────────────────────────


@router.get("/institution/fee-config")
async def get_fee_config(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_fee_config(user)


@router.put("/institution/fee-config")
async def update_fee_config(
    body: FeeConfigUpdate,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).update_fee_config(user, body.model_dump(exclude_unset=True))


@router.get("/institution/waivers")
async def list_waivers(
    status: str = Query("pending"),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Fee-waiver queue (Spec 39 §2.3). ``status`` ∈ pending | decided | all."""
    return await _svc(db).list_waivers(user, status)


@router.post("/institution/waivers/{payment_id}/decide")
async def decide_waiver(
    payment_id: UUID,
    body: WaiverDecisionRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).decide_waiver(user, payment_id, body.decision, body.reason)


@router.get("/institution/payments")
async def list_payments(
    kind: str | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_payments(user, kind)


@router.post("/institution/payments/{payment_id}/refund")
async def refund_payment(
    payment_id: UUID,
    body: RefundRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Institution-approved refund (Spec 39 §5). Full or partial; audited."""
    return await _svc(db).refund(
        user, payment_id, amount_cents=body.amount_cents, reason=body.reason
    )
