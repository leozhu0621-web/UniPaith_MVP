"""Spec 29 — Institution Inbox API at /api/v1/institutions/me/inbox."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.schemas.inbox import InboxMessageResponse
from unipaith.schemas.institution_inbox import (
    AssignThreadRequest,
    BulkMessageRequest,
    BulkMessageResponse,
    InstSuggestedReplyResponse,
    InstThreadResponse,
    InstThreadSummary,
    PostInstInboxMessageRequest,
)
from unipaith.services.institution_inbox_service import InstitutionInboxService

router = APIRouter(prefix="/institutions/me/inbox", tags=["institution-inbox"])


def _svc(db: AsyncSession) -> InstitutionInboxService:
    return InstitutionInboxService(db)


@router.get("/threads", response_model=list[InstThreadSummary])
async def list_threads(
    filter: str = Query("all", pattern="^(mine|unassigned|all)$"),
    reason: str | None = Query(None),
    program_id: UUID | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_threads(user.id, filter=filter, reason=reason, program_id=program_id)


@router.get("/threads/{thread_id}", response_model=InstThreadResponse)
async def get_thread(
    thread_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_thread(user.id, thread_id)


@router.post(
    "/threads/{thread_id}/messages",
    status_code=status.HTTP_201_CREATED,
    response_model=InboxMessageResponse,
)
async def post_message(
    thread_id: UUID,
    body: PostInstInboxMessageRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).post_message(user.id, thread_id, body)


@router.post("/threads/{thread_id}/assign", response_model=InstThreadSummary)
async def assign_thread(
    thread_id: UUID,
    body: AssignThreadRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).assign_thread(user.id, thread_id, body)


@router.post("/threads/{thread_id}/close", response_model=InstThreadSummary)
async def close_thread(
    thread_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).close_thread(user.id, thread_id)


@router.post("/threads/{thread_id}/ai-draft", response_model=InstSuggestedReplyResponse | None)
async def ai_draft(
    thread_id: UUID,
    reason_code: str | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).ai_draft(user.id, thread_id, reason_code=reason_code)


@router.post("/bulk-message", response_model=BulkMessageResponse)
async def bulk_message(
    body: BulkMessageRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).bulk_message(user.id, body)
