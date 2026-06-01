"""Spec 29 — Institution Messaging & Inbox API.

Mounted at /api/v1/institutions/me/inbox. The institution-side mirror of the
student inbox (/students/me/inbox, spec 17): a richer institution view over the
shared conversations/messages tables, with reason codes, assignment, AI drafts,
and bulk/segment messaging. All endpoints require the institution_admin role.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.schemas.institution_inbox import (
    AssignRequest,
    BulkMessageRequest,
    BulkMessageResult,
    InstSuggestedReplyResponse,
    InstThreadResponse,
    InstThreadSummary,
    IntentSuggestionResponse,
    PostInstMessageRequest,
    StaffMember,
)
from unipaith.services.institution_inbox_service import InstitutionInboxService

router = APIRouter(prefix="/institutions/me/inbox", tags=["institution-inbox"])


def _svc(db: AsyncSession) -> InstitutionInboxService:
    return InstitutionInboxService(db)


@router.get("/threads", response_model=list[InstThreadSummary])
async def list_threads(
    filter: str = Query("all", pattern="^(mine|unassigned|all)$"),
    reason: str | None = Query(None, description="Filter by reason code"),
    program_id: UUID | None = Query(None),
    state: str | None = Query(
        None, pattern="^(open|awaiting_student|awaiting_us|closed)$", description="Status filter"
    ),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_threads(
        user.id, filter=filter, reason=reason, program_id=program_id, status=state
    )


@router.get("/staff", response_model=list[StaffMember])
async def staff_roster(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).staff_roster(user.id)


@router.get("/threads/{thread_id}", response_model=InstThreadResponse)
async def get_thread(
    thread_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_thread(user.id, thread_id)


@router.post("/threads/{thread_id}/messages", status_code=status.HTTP_201_CREATED)
async def post_message(
    thread_id: UUID,
    body: PostInstMessageRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).post_message(
        user.id,
        thread_id,
        body=body.body,
        reason_code=body.reason_code,
        attachments=[a.model_dump() for a in body.attachments],
        due_date=body.due_date,
        request_document=body.request_document,
        requested_item=body.requested_item,
        ai_draft_used=body.ai_draft_used,
    )


@router.post("/threads/{thread_id}/assign", response_model=InstThreadResponse)
async def assign_thread(
    thread_id: UUID,
    body: AssignRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).assign(user.id, thread_id, body.staff_user_id)


@router.post("/threads/{thread_id}/close", response_model=InstThreadResponse)
async def close_thread(
    thread_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).close(user.id, thread_id)


@router.post(
    "/threads/{thread_id}/ai-draft",
    response_model=InstSuggestedReplyResponse | None,
)
async def ai_draft(
    thread_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Returns the AI-drafted reply, or ``null`` when unavailable (flag off /
    agent failure). The UI hides the card on null."""
    return await _svc(db).ai_draft(user.id, thread_id)


@router.post(
    "/threads/{thread_id}/intent-suggestion",
    response_model=IntentSuggestionResponse | None,
)
async def intent_suggestion(
    thread_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    """Suggested reason code for the latest inbound message (suggestion-only).
    Returns ``null`` when the flag is off or no suggestion is available."""
    return await _svc(db).intent_suggestion(user.id, thread_id)


@router.post("/bulk-message", response_model=BulkMessageResult)
async def bulk_message(
    body: BulkMessageRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).bulk_message(
        user.id,
        segment_id=body.segment_id,
        application_ids=body.application_ids,
        template_id=body.template_id,
        body=body.body,
        variables=body.variables,
        reason_code=body.reason_code,
        due_date=body.due_date,
    )
