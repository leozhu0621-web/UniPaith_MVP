"""Institution fairness dashboard + auto-halt override (G-I5 / Spec 43 §6)."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.institution import Program
from unipaith.models.user import User
from unipaith.services.audit_service import AuditService
from unipaith.services.fairness_service import FairnessService
from unipaith.services.institution_service import InstitutionService

router = APIRouter(prefix="/institutions/me/fairness", tags=["fairness"])


class FairnessSignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    program_id: UUID
    protected_attribute: str
    week_start: date
    reference_group: str | None
    disadvantaged_group: str | None
    disparate_impact_ratio: float | None
    disparate_impact_delta: float | None
    sample_size: int
    breached: bool


class ProgramFairnessStatus(BaseModel):
    program_id: UUID
    program_name: str
    matching_halted: bool
    signals: list[FairnessSignalResponse]


class OverrideRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


async def _institution_programs(db: AsyncSession, user: User) -> tuple[UUID, list[Program]]:
    inst = await InstitutionService(db).get_institution(user.id)
    rows = (
        (await db.execute(select(Program).where(Program.institution_id == inst.id))).scalars().all()
    )
    return inst.id, list(rows)


@router.get("", response_model=list[ProgramFairnessStatus])
async def list_fairness(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Per-program halt status + recent disparate-impact signals."""
    _, programs = await _institution_programs(db, user)
    svc = FairnessService(db)
    out: list[ProgramFairnessStatus] = []
    for p in programs:
        signals = await svc.list_signals(p.id)
        out.append(
            ProgramFairnessStatus(
                program_id=p.id,
                program_name=p.program_name,
                matching_halted=bool(p.matching_halted),
                signals=[FairnessSignalResponse.model_validate(s) for s in signals],
            )
        )
    return out


@router.post("/{program_id}/compute", response_model=list[FairnessSignalResponse])
async def compute_fairness(
    program_id: UUID,
    week_start: date,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Compute the week's disparate-impact signals and evaluate the auto-halt.

    Normally driven by a weekly job; exposed for on-demand recompute.
    """
    inst_id, programs = await _institution_programs(db, user)
    if program_id not in {p.id for p in programs}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    svc = FairnessService(db)
    signals = await svc.compute_weekly_signals(program_id, week_start)
    halted = await svc.evaluate_auto_halt(program_id)
    if halted:
        await AuditService(db).log(
            institution_id=inst_id,
            actor_user_id=user.id,
            action="fairness_signal_override",
            entity_type="program",
            entity_id=str(program_id),
            description="Matching auto-halted: disparate impact breached for 2 consecutive weeks",
            new_value={"matching_halted": True},
        )
    return [FairnessSignalResponse.model_validate(s) for s in signals]


@router.post("/{program_id}/override", response_model=ProgramFairnessStatus)
async def override_halt(
    program_id: UUID,
    body: OverrideRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Clear a fairness matching-halt (admin override) — audit-logged."""
    inst_id, programs = await _institution_programs(db, user)
    if program_id not in {p.id for p in programs}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    svc = FairnessService(db)
    program = await svc.override_halt(program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Program not found")
    await AuditService(db).log(
        institution_id=inst_id,
        actor_user_id=user.id,
        action="fairness_signal_override",
        entity_type="program",
        entity_id=str(program_id),
        description=f"Fairness matching-halt cleared by admin: {body.reason}",
        old_value={"matching_halted": True},
        new_value={"matching_halted": False, "reason": body.reason},
    )
    signals = await svc.list_signals(program_id)
    return ProgramFairnessStatus(
        program_id=program.id,
        program_name=program.program_name,
        matching_halted=bool(program.matching_halted),
        signals=[FairnessSignalResponse.model_validate(s) for s in signals],
    )
