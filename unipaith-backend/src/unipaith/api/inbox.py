"""Spec 17 — Student Inbox API. Mounted at /api/v1/students/me/inbox.

Application-threaded conversations + system notifications. A richer
student-side view over the shared conversations/messages tables; institution
messaging keeps using /api/v1/messages.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import get_current_user
from unipaith.models.user import User
from unipaith.schemas.inbox import (
    PostInboxMessageRequest,
    SuggestedReplyResponse,
    ThreadResponse,
    ThreadSummary,
)
from unipaith.services.inbox_service import InboxService

router = APIRouter(prefix="/students/me/inbox", tags=["inbox"])


def _svc(db: AsyncSession) -> InboxService:
    return InboxService(db)


@router.get("/threads", response_model=list[ThreadSummary])
async def list_threads(
    application_id: UUID | None = Query(None, description="Only threads for this application"),
    type: str | None = Query(None, pattern="^(human|system)$", description="Message type filter"),
    state: str | None = Query(
        None,
        pattern="^(needs_reply|requested|completed|status_update_only)$",
        description="Action-state filter",
    ),
    sort: str = Query("urgent", pattern="^(urgent|recent|action_required)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_threads(
        user.id,
        application_id=application_id,
        thread_type=type,
        action_state=state,
        sort=sort,
    )


@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_thread(user.id, thread_id)


@router.post(
    "/threads/{thread_id}/messages",
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    thread_id: UUID,
    body: PostInboxMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).post_message(
        user.id,
        thread_id,
        body=body.body,
        attachments=[a.model_dump() for a in body.attachments],
        ai_draft_used=body.ai_draft_used,
    )


@router.post("/threads/{thread_id}/mark-complete", response_model=ThreadResponse)
async def mark_complete(
    thread_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).mark_complete(user.id, thread_id)


@router.post("/threads/{thread_id}/suggested-reply", response_model=SuggestedReplyResponse | None)
async def suggested_reply(
    thread_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns the AI-drafted reply, or ``null`` when unavailable (flag off /
    consent denied / agent failure). The UI hides the card on null."""
    return await _svc(db).suggested_reply(user.id, thread_id)
