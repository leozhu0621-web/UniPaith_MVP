"""Spec 46 §9/§10/§1/§5 — institution Data & Privacy surface.

Mounted at /api/v1/institutions/me/data. The governance config (§9), the
sub-processor list (§10), the brand commitments (§1), and the retention schedule
(§5) behind /i/settings?tab=data. The §6 fairness auto-halt endpoints live in
``api/institutions.py`` (Spec 46 §6, PR #249) — this router is the §9/§10
governance counterpart. All endpoints require institution_admin and are scoped
to the caller's institution. Registered before ``institutions_router`` so the
literal ``/institutions/me/data/*`` paths win over ``/institutions/{id}``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
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
from unipaith.services.institution_service import InstitutionService

router = APIRouter(prefix="/institutions/me/data", tags=["governance"])


class GovernancePatch(BaseModel):
    override_expiry_weeks_default: int | None = Field(None, ge=1, le=4)
    protected_attributes_tracked: list[str] | None = None
    no_training_tier: bool | None = None
    data_residency: str | None = None


async def _institution(user: User, db: AsyncSession) -> Institution:
    return await InstitutionService(db).get_institution(user.id)


@router.get("/governance")
async def data_governance(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Everything the /i/settings?tab=data surface needs: the institution's
    governance settings (§9), per-program fairness thresholds (§6/§9), the
    sub-processor list (§10), the brand commitments (§1), and the retention
    schedule (§5)."""
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


@router.patch("/governance")
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
