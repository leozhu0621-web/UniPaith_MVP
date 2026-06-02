"""Spec 46 — Data Rights, Privacy & Fairness Governance (institution surface).

Mounted at /api/v1/institutions/me. Two concerns:

- ``/fairness/*`` — the disparate-impact auto-halt engine (§6): per-cohort
  status + 4-week trend, the signal ledger, the override workflow, per-program
  threshold config, and an ops recompute trigger.
- ``/data/*`` — institution data-governance config (§9) + the sub-processor list
  (§10) + the brand commitments (§1).

All endpoints require the institution_admin role and are scoped to the caller's
institution. Registered before ``institutions_router`` so the literal paths win
over ``/institutions/{id}``.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.institution import Institution, Program
from unipaith.models.user import User
from unipaith.services.data_governance import (
    BRAND_COMMITMENTS,
    RETENTION_POLICY,
    SUBPROCESSOR_NOTE,
    SUBPROCESSORS,
    resolve_governance,
    validate_governance_patch,
)
from unipaith.services.fairness_service import FairnessService
from unipaith.services.institution_service import InstitutionService

router = APIRouter(prefix="/institutions/me", tags=["governance"])


async def _institution(user: User, db: AsyncSession) -> Institution:
    return await InstitutionService(db).get_institution(user.id)


async def _institution_id(user: User, db: AsyncSession) -> UUID:
    inst = await InstitutionService(db).get_institution(user.id)
    return inst.id


# ── request bodies ───────────────────────────────────────────────────────────


class OverrideRequest(BaseModel):
    signal_id: UUID
    rationale: str = Field(..., min_length=100, max_length=4000)
    expires_weeks: int | None = Field(None, ge=1, le=4)


class ThresholdRequest(BaseModel):
    program_id: UUID
    threshold: Decimal = Field(..., ge=Decimal("0.05"), le=Decimal("0.40"))


class ComputeRequest(BaseModel):
    program_id: UUID | None = None


class GovernancePatch(BaseModel):
    override_expiry_weeks_default: int | None = Field(None, ge=1, le=4)
    protected_attributes_tracked: list[str] | None = None
    no_training_tier: bool | None = None
    data_residency: str | None = None


# ── fairness (§6) ────────────────────────────────────────────────────────────


@router.get("/fairness/status")
async def fairness_status(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Per-program halt status + 4-week DI trend + latest signals (§6.4).

    Lazily computes the current week so the dashboard/heatmap stay fresh.
    """
    inst_id = await _institution_id(user, db)
    return await FairnessService(db).get_status(inst_id)


@router.get("/fairness/signals")
async def fairness_signals(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst_id = await _institution_id(user, db)
    return await FairnessService(db).list_signals(inst_id, program_id=program_id)


@router.get("/fairness/overrides")
async def fairness_overrides(
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst_id = await _institution_id(user, db)
    return await FairnessService(db).list_overrides(inst_id, program_id=program_id)


@router.post("/fairness/overrides", status_code=201)
async def create_fairness_override(
    body: OverrideRequest,
    request: Request,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """§6.3 — lift a halt with a logged rationale (≥100 chars)."""
    inst_id = await _institution_id(user, db)
    override = await FairnessService(db).request_override(
        institution_id=inst_id,
        signal_id=body.signal_id,
        admin_user_id=user.id,
        rationale=body.rationale,
        expires_weeks=body.expires_weeks,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "id": str(override.id),
        "override_expires_at": override.override_expires_at.isoformat(),
    }


@router.patch("/fairness/threshold")
async def update_fairness_threshold(
    body: ThresholdRequest,
    request: Request,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """§9 — tune a program's fairness threshold (0.05–0.40)."""
    inst_id = await _institution_id(user, db)
    program = await FairnessService(db).set_threshold(
        institution_id=inst_id,
        program_id=body.program_id,
        threshold=body.threshold,
        admin_user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {
        "program_id": str(program.id),
        "fairness_threshold": float(program.fairness_threshold),
    }


@router.post("/fairness/compute")
async def fairness_compute(
    body: ComputeRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Ops trigger — the same compute the scheduled Monday job runs (§6.2)."""
    inst_id = await _institution_id(user, db)
    signals = await FairnessService(db).run_weekly_compute(
        institution_id=inst_id, program_id=body.program_id
    )
    return {"computed": len(signals)}


# ── data governance (§9) + sub-processor list (§10) + commitments (§1) ────────


@router.get("/data/governance")
async def data_governance(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Everything the /i/settings?tab=data surface needs: the institution's
    governance settings (§9), per-program fairness thresholds, the sub-processor
    list (§10), the brand commitments (§1), and the retention schedule (§5)."""
    inst = await _institution(user, db)
    programs = (
        (
            await db.execute(
                select(Program)
                .where(Program.institution_id == inst.id)
                .order_by(Program.program_name)
            )
        )
        .scalars()
        .all()
    )
    return {
        "settings": resolve_governance(inst.data_governance),
        "program_thresholds": [
            {
                "program_id": str(p.id),
                "program_name": p.program_name,
                "fairness_threshold": float(p.fairness_threshold),
                "matching_halted": p.matching_halted,
            }
            for p in programs
        ],
        "subprocessors": SUBPROCESSORS,
        "subprocessor_note": SUBPROCESSOR_NOTE,
        "brand_commitments": BRAND_COMMITMENTS,
        "retention_policy": RETENTION_POLICY,
        "no_data_sale": (
            "UniPaith never sells, licenses, or rents raw student data. Revenue is "
            "the platform subscription and the per-applicant fee — there is no "
            "data-broker line of business, and there never will be."
        ),
    }


@router.patch("/data/governance")
async def update_data_governance(
    body: GovernancePatch,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """§9 — update the institution's data-governance settings."""
    inst = await _institution(user, db)
    patch = validate_governance_patch(body.model_dump(exclude_unset=True, exclude_none=True))
    merged = dict(inst.data_governance or {})
    merged.update(patch)
    inst.data_governance = merged
    await db.flush()
    return {"settings": resolve_governance(inst.data_governance)}
