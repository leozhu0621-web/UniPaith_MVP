"""Spec 17 (Inbox) — request/response schemas.

The Inbox is a richer student-side *view* over the shared
``conversations`` / ``messages`` tables. These schemas project the ORM rows
into the Thread / Message shape defined in spec 17 §8.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Action labels (spec 17 §5) ──
ACTION_LABELS = {
    "needs_reply",
    "document_requested",
    "clarification_required",
    "interview_invite",
    "status_update_only",
    "completed",
}


class InboxAttachment(BaseModel):
    """An attached document or link on an inbox message."""

    id: str | None = None
    name: str
    kind: str = "document"  # 'document' | 'link'
    url: str | None = None


class InboxMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    thread_id: UUID
    sender: str  # 'student' | 'admissions_officer' | 'system'
    body: str
    attachments: list[dict] = []
    sent_at: datetime
    read_at: datetime | None = None
    status: str = "sent"


class ThreadApplication(BaseModel):
    program_name: str | None = None
    institution_name: str | None = None


class ThreadParticipant(BaseModel):
    id: str
    role: str  # 'student' | 'admissions_officer' | 'system'
    name: str


class ThreadSummary(BaseModel):
    """Inbox list-row shape (no message bodies)."""

    id: UUID
    application_id: UUID | None = None
    application: ThreadApplication
    type: str  # 'human' | 'system'
    subject: str | None = None
    action_label: str | None = None
    due_date: datetime | None = None
    waiting_on: str = "none"  # 'student' | 'school' | 'none'
    unread: bool = False
    last_message_at: datetime | None = None
    linked_checklist_item_category: str | None = None
    linked_calendar_item_id: UUID | None = None


class ThreadResponse(ThreadSummary):
    """Full thread — summary + participants + messages."""

    participants: list[ThreadParticipant] = []
    messages: list[InboxMessageResponse] = []


class PostInboxMessageRequest(BaseModel):
    body: str = Field(min_length=1)
    attachments: list[InboxAttachment] = []
    # Spec 17 §14 — record whether the student sent from an AI draft vs typed.
    ai_draft_used: bool = False


class SuggestedReplyResponse(BaseModel):
    """InboxReplyDrafter output (spec 45 §13). The endpoint returns 204/null
    when the agent is unavailable — the UI hides the card."""

    draft: str
    tone: str = "professional"
    length: str = "medium"
    alternate_drafts: list[str] = []
