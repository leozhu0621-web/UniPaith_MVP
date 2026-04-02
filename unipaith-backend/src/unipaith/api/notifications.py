from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import get_current_user
from unipaith.models.user import User
from unipaith.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationResponse,
    UpdateNotificationPrefsRequest,
)
from unipaith.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    return await svc.list_notifications(
        user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=dict)
async def unread_count(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    return await svc.unread_count(user.id)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    return await svc.mark_read(user.id, notification_id)


@router.post("/read-all", response_model=dict)
async def mark_all_read(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    count = await svc.mark_all_read(user.id)
    return {"marked_read": count}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_preferences(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    return await svc.get_preferences(user.id)


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_preferences(
    body: UpdateNotificationPrefsRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    svc = NotificationService(db)
    return await svc.update_preferences(user.id, body)
