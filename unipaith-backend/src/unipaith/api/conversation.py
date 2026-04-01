from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.conversation import (
    ConfidenceReportResponse,
    ConversationRequirementResponse,
    ConversationSessionResponse,
    ConversationTurnRequest,
    ConversationTurnResponse,
    ListConversationRequirementsResponse,
    ResolveConflictRequest,
    ResolveConflictResponse,
    ResumeCheckpointResponse,
    ShortlistUnlockResponse,
    UpdateConversationRequirementRequest,
)
from unipaith.services.conversation_service import ConversationService

router = APIRouter(prefix="/students/me/conversation", tags=["conversation"])


def _svc(db: AsyncSession) -> ConversationService:
    return ConversationService(db)


@router.post("/turn", response_model=ConversationTurnResponse)
async def send_conversation_turn(
    body: ConversationTurnRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).send_turn(user.id, body)


@router.get("/session", response_model=ConversationSessionResponse)
async def get_conversation_session(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_session(user.id)


@router.get("/session/resume", response_model=ResumeCheckpointResponse)
async def get_conversation_resume_checkpoint(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_resume_checkpoint(user.id)


@router.get("/requirements", response_model=ListConversationRequirementsResponse)
async def list_conversation_requirements(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_requirements(user.id)


@router.patch("/requirements/{requirement_id}", response_model=ConversationRequirementResponse)
async def update_conversation_requirement(
    requirement_id: UUID,
    body: UpdateConversationRequirementRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).update_requirement(user.id, requirement_id, body)


@router.get("/confidence", response_model=ConfidenceReportResponse)
async def get_conversation_confidence_report(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_confidence_report(user.id)


@router.get("/shortlist-unlock", response_model=ShortlistUnlockResponse)
async def get_shortlist_unlock_report(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_shortlist_unlock(user.id)


@router.post("/conflicts/{conflict_id}/resolve", response_model=ResolveConflictResponse)
async def resolve_conversation_conflict(
    conflict_id: UUID,
    body: ResolveConflictRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).resolve_conflict(user.id, conflict_id, body.selected_resolution)
