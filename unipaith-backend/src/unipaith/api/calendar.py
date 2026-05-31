"""Spec 16 · Calendar — student-facing API.

Routes (Spec 16 §6):
  GET    /me/calendar?from=&to=   — unified timeline in range
  POST   /me/calendar/reminders   — create a student reminder
  POST   /me/calendar/work-blocks — create a student work block
  PATCH  /me/calendar/{item_id}   — update status / notes / reschedule
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.calendar import (
    CalendarItem,
    CalendarItemPatch,
    ReminderCreate,
    WorkBlockCreate,
)
from unipaith.services.calendar_service import CalendarService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/me/calendar", tags=["calendar"])


@router.get("", response_model=list[CalendarItem])
async def get_calendar(
    from_: datetime | None = Query(None, alias="from", description="Range start (ISO 8601)"),
    to: datetime | None = Query(None, description="Range end (ISO 8601)"),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    return await CalendarService(db).get_calendar(profile.id, from_, to)


@router.post("/reminders", response_model=CalendarItem, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    body: ReminderCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    item = await CalendarService(db).create_reminder(profile.id, body)
    await db.commit()
    return item


@router.post("/work-blocks", response_model=CalendarItem, status_code=status.HTTP_201_CREATED)
async def create_work_block(
    body: WorkBlockCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    item = await CalendarService(db).create_work_block(profile.id, body)
    await db.commit()
    return item


@router.patch("/{item_id}", response_model=CalendarItem)
async def patch_calendar_item(
    item_id: str,
    body: CalendarItemPatch,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    profile = await StudentService(db)._get_student_profile(user.id)
    item = await CalendarService(db).patch_item(profile.id, item_id, body)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Calendar item not found")
    await db.commit()
    return item
