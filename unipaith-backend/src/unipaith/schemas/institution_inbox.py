"""Spec 29 — Institution inbox request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from unipaith.schemas.inbox import InboxAttachment, InboxMessageResponse

REASON_CODES = frozenset(
    {
        "request_document",
        "request_clarification",
        "interview_invite",
        "status_update",
        "general_reply",
        "decision_notice",
    }
)

REASON_REQUIRES_DUE = frozenset({"request_document", "request_clarification", "interview_invite"})

REASON_TO_ACTION_LABEL: dict[str, str] = {
    "request_document": "document_requested",
    "request_clarification": "clarification_required",
    "interview_invite": "interview_invite",
    "status_update": "status_update_only",
    "general_reply": "needs_reply",
    "decision_notice": "status_update_only",
}


class InstStudentRef(BaseModel):
    id: UUID
    name: str


class InstProgramRef(BaseModel):
    id: UUID | None = None
    name: str | None = None


class InstThreadContext(BaseModel):
    stage: str | None = None
    checklist_complete: int = 0
    checklist_total: int = 0
    missing_items: list[str] = []


class InstThreadSummary(BaseModel):
    id: UUID
    application_id: UUID | None = None
    student_ref: InstStudentRef
    program_ref: InstProgramRef | None = None
    assigned_to: UUID | None = None
    reason_label: str | None = None
    action_label: str | None = None
    status: str = "open"
    due_date: datetime | None = None
    waiting_on: str = "none"
    unread_count: int = 0
    last_message_at: datetime | None = None
    subject: str | None = None
    context: InstThreadContext = Field(default_factory=InstThreadContext)


class InstThreadParticipant(BaseModel):
    id: str
    role: str
    name: str


class InstThreadResponse(InstThreadSummary):
    participants: list[InstThreadParticipant] = []
    messages: list[InboxMessageResponse] = []


class PostInstInboxMessageRequest(BaseModel):
    body: str = Field(min_length=1)
    attachments: list[InboxAttachment] = []
    reason_code: str
    due_date: datetime | None = None
    checklist_category: str | None = None
    ai_draft_used: bool = False


class AssignThreadRequest(BaseModel):
    staff_user_id: UUID | None = None


class InstSuggestedReplyResponse(BaseModel):
    draft: str
    tone: str = "professional"
    length: str = "medium"
    alternate_drafts: list[str] = []
    suggested_reason_code: str | None = None


class BulkMessageRequest(BaseModel):
    segment_id: UUID | None = None
    application_ids: list[UUID] = []
    template_id: UUID | None = None
    body: str | None = None
    variables: dict[str, str] = {}
    reason_code: str = "status_update"
    due_date: datetime | None = None


class BulkMessageResponse(BaseModel):
    batch_id: str
    sent_count: int
    skipped_count: int
    failed_ids: list[UUID] = []
