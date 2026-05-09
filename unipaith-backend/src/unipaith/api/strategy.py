"""Phase A — Strategy API. Mounted at /api/v1/students/me/strategy."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.strategy import StrategyResponse, UpdateStrategyRequest
from unipaith.services.strategy_service import StrategyService

router = APIRouter(prefix="/students/me/strategy", tags=["strategy"])


def _svc(db: AsyncSession) -> StrategyService:
    return StrategyService(db)


@router.post(
    "/generate",
    response_model=StrategyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_strategy(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new strategy from active goals + needs.

    Phase A: rule-based template generator. Plan 2: replaces with an LLM call
    that writes real prose. The new strategy lands as `draft` — call
    `POST /{id}/activate` to promote it.
    """
    strategy = await _svc(db).generate(user.id)
    return StrategyResponse.model_validate(strategy)


@router.get("/active", response_model=StrategyResponse | None)
async def get_active_strategy(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Returns null if the student has no active strategy yet — the UI
    should show a generate-strategy CTA in that case."""
    strategy = await _svc(db).get_active(user.id)
    if strategy is None:
        return None
    return StrategyResponse.model_validate(strategy)


@router.get("/versions", response_model=list[StrategyResponse])
async def list_strategy_versions(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    strategies = await _svc(db).list_versions(user.id)
    return [StrategyResponse.model_validate(s) for s in strategies]


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    strategy = await _svc(db).get_strategy(user.id, strategy_id)
    if strategy is None:
        raise NotFoundException("Strategy not found")
    return StrategyResponse.model_validate(strategy)


@router.post("/{strategy_id}/activate", response_model=StrategyResponse)
async def activate_strategy(
    strategy_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    strategy = await _svc(db).activate(user.id, strategy_id)
    return StrategyResponse.model_validate(strategy)


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: UUID,
    body: UpdateStrategyRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Manual edit. Archives the original (must be draft or active) and
    creates a new draft with the patch applied. The new draft is NOT
    auto-activated; call `POST /{new_id}/activate` to promote it."""
    new_draft = await _svc(db).update(user.id, strategy_id, body)
    return StrategyResponse.model_validate(new_draft)
