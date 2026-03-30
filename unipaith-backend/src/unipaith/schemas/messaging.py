from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateConversationRequest(BaseModel):
    institution_id: UUID
    student_id: UUID
    subject: str | None = None
    program_id: UUID | None = None


class SendMessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_id: UUID
    sender_type: str | None
    message_body: str
    sent_at: datetime
    read_at: datetime | None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    institution_id: UUID
    program_id: UUID | None
    subject: str | None
    status: str | None
    started_at: datetime
    last_message_at: datetime | None
    unread_count: int = 0
