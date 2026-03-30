from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import get_current_user
from unipaith.models.user import User
from unipaith.schemas.messaging import (
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
    SendMessageRequest,
)
from unipaith.services.messaging_service import MessagingService

router = APIRouter(prefix="/messages", tags=["messaging"])


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    body: CreateConversationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MessagingService(db)
    return await svc.create_conversation(
        student_id=body.student_id,
        institution_id=body.institution_id,
        subject=body.subject,
        program_id=body.program_id,
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MessagingService(db)
    return await svc.list_conversations(user.id)


@router.post("/conversations/{conversation_id}", response_model=MessageResponse)
async def send_message(
    conversation_id: UUID,
    body: SendMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MessagingService(db)
    return await svc.send_message(
        conversation_id=conversation_id,
        sender_id=user.id,
        content=body.content,
    )


@router.get("/conversations/{conversation_id}", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    before: datetime | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = MessagingService(db)
    return await svc.get_messages(
        conversation_id=conversation_id,
        user_id=user.id,
        limit=limit,
        before=before,
    )
