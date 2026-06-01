"""Spec 29 (Institution Messaging & Inbox) — request/response schemas.

The institution inbox is the mirror of the student inbox (spec 17): a richer
*institution-side* view over the shared ``conversations`` / ``messages`` tables.
These schemas project the ORM rows into the ``InstThread`` shape (spec 29 §7).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from unipaith.schemas.inbox import InboxAttachment

# ── Reason codes (spec 29 §4) ──
REASON_CODES = {
    "request_document",
    "request_clarification",
    "interview_invite",
    "status_update",
    "general_reply",
    "decision_notice",
}

# Thread lifecycle statuses (spec 29 §7).
INST_THREAD_STATUSES = {"open", "awaiting_student", "awaiting_us", "closed"}


class InstThreadContext(BaseModel):
    """Denormalized applicant context for the right rail (spec 29 §3)."""

    stage: str | None = None
    checklist_complete: int = 0
    checklist_total: int = 0
    missing_items: list[str] = []


class InstThreadStudent(BaseModel):
    id: UUID
    name: str


class InstMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    sender: str  # 'student' | 'institution' | 'admissions_officer' | 'system'
    body: str
    attachments: list[dict] = []
    sent_at: datetime
    read_at: datetime | None = None
    status: str = "sent"
    ai_draft_used: bool = False


class InstThreadSummary(BaseModel):
    """Inbox list-row shape (no message bodies)."""

    id: UUID
    application_id: UUID | None = None
    student: InstThreadStudent
    program_name: str | None = None
    reason_label: str | None = None  # institution reason code (spec 29 §4)
    action_label: str | None = None  # derived student-facing label (spec 17 §5)
    status: str = "open"  # open | awaiting_student | awaiting_us | closed
    assigned_to: UUID | None = None
    assigned_to_name: str | None = None
    due_date: datetime | None = None
    unread_count: int = 0
    last_message_at: datetime | None = None
    context: InstThreadContext = InstThreadContext()


class InstThreadResponse(InstThreadSummary):
    """Full thread — summary + messages."""

    messages: list[InstMessageResponse] = []


class PostInstMessageRequest(BaseModel):
    body: str = Field(min_length=1)
    reason_code: str
    attachments: list[InboxAttachment] = []
    due_date: datetime | None = None
    # When True (typically with reason_code=request_document) the attach is a
    # *document request*: it links/creates a student checklist item (spec 29 §5).
    request_document: bool = False
    requested_item: str | None = None
    # Spec 29 §8 — record whether the staff member sent from an AI draft.
    ai_draft_used: bool = False

    @field_validator("reason_code")
    @classmethod
    def _valid_reason(cls, v: str) -> str:
        if v not in REASON_CODES:
            raise ValueError(f"reason_code must be one of {sorted(REASON_CODES)}")
        return v


class AssignRequest(BaseModel):
    staff_user_id: UUID | None = None  # None = unassign


class InstSuggestedReplyResponse(BaseModel):
    """InstitutionReplyDrafter output (spec 29 §8). The endpoint returns null
    when the agent is unavailable — the UI hides the card."""

    draft: str
    tone: str = "professional"
    length: str = "medium"
    alternate_drafts: list[str] = []


class IntentSuggestionResponse(BaseModel):
    """InboundIntentClassifier output (spec 29 §8, suggestion-only)."""

    reason_code: str
    confidence: float = 0.0
    rationale: str = ""


class StaffMember(BaseModel):
    id: UUID
    name: str
    email: str
    role: str = "admin"


class BulkMessageRequest(BaseModel):
    segment_id: UUID | None = None
    application_ids: list[UUID] = []
    template_id: UUID | None = None
    body: str | None = None
    variables: dict = {}
    reason_code: str
    due_date: datetime | None = None

    @field_validator("reason_code")
    @classmethod
    def _valid_reason(cls, v: str) -> str:
        if v not in REASON_CODES:
            raise ValueError(f"reason_code must be one of {sorted(REASON_CODES)}")
        return v


class BulkMessageResult(BaseModel):
    sent_count: int = 0
    suppressed_count: int = 0
    recipient_count: int = 0
    thread_ids: list[UUID] = []
