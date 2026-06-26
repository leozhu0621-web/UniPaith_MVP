"""Reminder delivery loop — a ``student_calendar.reminder_at`` row that is due
gets exactly one in-app notification (idempotent on re-run), future reminders
wait, and completed ones are skipped.

Regression for the bug where reminder_at was persisted but never delivered.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.engagement import StudentCalendar
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import Notification
from unipaith.services.calendar_service import CalendarService

# asyncio_mode = "auto" (pyproject) runs these async tests without an explicit mark.

_REMINDER_TYPE = "deadline_reminders"


async def _student(db: AsyncSession) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"s-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.flush()
    return profile


async def _reminders_for(db: AsyncSession, user_id) -> int:
    return await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.notification_type == _REMINDER_TYPE,
        )
    )


async def _add_reminder(
    db: AsyncSession, profile, *, reminder_at, title="Deadline"
) -> StudentCalendar:
    cal = StudentCalendar(
        student_id=profile.id,
        entry_type="reminder",
        title=title,
        start_time=reminder_at,
        reminder_at=reminder_at,
    )
    db.add(cal)
    await db.flush()
    return cal


async def test_due_reminder_delivered_once_and_idempotent(db_session: AsyncSession):
    profile = await _student(db_session)
    now = datetime.now(UTC)
    due = await _add_reminder(
        db_session, profile, reminder_at=now - timedelta(hours=1), title="Past due"
    )
    future = await _add_reminder(
        db_session, profile, reminder_at=now + timedelta(days=1), title="Later"
    )

    svc = CalendarService(db_session)
    sent = await svc.deliver_due_reminders()
    assert sent == 1
    assert await _reminders_for(db_session, profile.user_id) == 1

    # The due row is stamped; the future row stays pending.
    assert due.reminder_sent_at is not None
    assert future.reminder_sent_at is None

    # Re-running must NOT double-send (the marker skips it; event_id is the hard
    # guarantee even if the marker were lost).
    sent_again = await svc.deliver_due_reminders()
    assert sent_again == 0
    assert await _reminders_for(db_session, profile.user_id) == 1


async def test_completed_reminder_is_skipped(db_session: AsyncSession):
    profile = await _student(db_session)
    now = datetime.now(UTC)
    cal = await _add_reminder(
        db_session, profile, reminder_at=now - timedelta(hours=2), title="Done"
    )
    cal.status = "completed"
    await db_session.flush()

    sent = await CalendarService(db_session).deliver_due_reminders()
    assert sent == 0
    assert await _reminders_for(db_session, profile.user_id) == 0
