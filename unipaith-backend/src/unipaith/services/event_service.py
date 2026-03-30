"""
Event service — event management, RSVP handling, and calendar integration.
Supports creating events, managing RSVPs with capacity control, and ICS export.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.config import settings
from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from unipaith.models.engagement import StudentCalendar
from unipaith.models.institution import Event, EventRSVP

logger = logging.getLogger(__name__)


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Event CRUD
    # ------------------------------------------------------------------

    async def create_event(
        self,
        institution_id: UUID,
        event_name: str,
        event_type: str,
        start_time: datetime,
        end_time: datetime,
        description: str | None = None,
        location: str | None = None,
        capacity: int | None = None,
        program_id: UUID | None = None,
    ) -> Event:
        """Create a new event for an institution."""
        if end_time <= start_time:
            raise BadRequestException("Event end time must be after start time")

        event = Event(
            institution_id=institution_id,
            program_id=program_id,
            event_name=event_name,
            event_type=event_type,
            description=description,
            location=location,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            rsvp_count=0,
            status="upcoming",
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def list_upcoming_events(
        self,
        program_id: UUID | None = None,
        institution_id: UUID | None = None,
        event_type: str | None = None,
        limit: int = 20,
    ) -> list[Event]:
        """List published upcoming events with optional filters."""
        now = datetime.now(timezone.utc)
        query = select(Event).where(
            Event.start_time > now,
            Event.status == "upcoming",
        )

        if program_id:
            query = query.where(Event.program_id == program_id)
        if institution_id:
            query = query.where(Event.institution_id == institution_id)
        if event_type:
            query = query.where(Event.event_type == event_type)

        query = query.order_by(Event.start_time.asc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_institution_events(
        self,
        institution_id: UUID,
        status_filter: str | None = None,
    ) -> list[Event]:
        """List all events for an institution (admin view)."""
        query = select(Event).where(Event.institution_id == institution_id)
        if status_filter:
            query = query.where(Event.status == status_filter)
        query = query.order_by(Event.start_time.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # RSVP
    # ------------------------------------------------------------------

    async def rsvp(
        self, student_id: UUID, event_id: UUID, user_id: UUID
    ) -> EventRSVP:
        """
        RSVP a student to an event.

        Checks capacity constraints and duplicate RSVPs.
        Automatically adds the event to the student's calendar.
        """
        event = await self._get_event(event_id)

        # Check capacity
        if event.capacity is not None and event.rsvp_count >= event.capacity:
            raise ConflictException("Event is at full capacity")

        # Check for existing RSVP
        existing = await self.db.execute(
            select(EventRSVP).where(
                EventRSVP.event_id == event_id,
                EventRSVP.student_id == student_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Already RSVP'd to this event")

        now = datetime.now(timezone.utc)
        rsvp = EventRSVP(
            event_id=event_id,
            student_id=student_id,
            rsvp_status="registered",
            registered_at=now,
        )
        self.db.add(rsvp)

        # Increment RSVP count
        event.rsvp_count = (event.rsvp_count or 0) + 1

        # Add to student calendar
        reminder_hours = settings.event_rsvp_reminder_hours
        reminder_at = event.start_time - timedelta(hours=reminder_hours)

        calendar_entry = StudentCalendar(
            student_id=student_id,
            entry_type="event",
            reference_id=event_id,
            title=event.event_name,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            reminder_at=reminder_at if reminder_at > now else None,
        )
        self.db.add(calendar_entry)

        await self.db.flush()
        return rsvp

    async def cancel_rsvp(self, student_id: UUID, event_id: UUID) -> None:
        """
        Cancel an RSVP and remove the event from the student's calendar.
        """
        # Find existing RSVP
        result = await self.db.execute(
            select(EventRSVP).where(
                EventRSVP.event_id == event_id,
                EventRSVP.student_id == student_id,
            )
        )
        rsvp = result.scalar_one_or_none()
        if not rsvp:
            raise NotFoundException("RSVP not found")

        await self.db.delete(rsvp)

        # Decrement RSVP count
        event = await self._get_event(event_id)
        event.rsvp_count = max((event.rsvp_count or 0) - 1, 0)

        # Remove from student calendar
        await self.db.execute(
            delete(StudentCalendar).where(
                StudentCalendar.student_id == student_id,
                StudentCalendar.entry_type == "event",
                StudentCalendar.reference_id == event_id,
            )
        )

        await self.db.flush()

    async def list_student_rsvps(self, student_id: UUID) -> list[EventRSVP]:
        """List all RSVPs for a student, with event details loaded."""
        result = await self.db.execute(
            select(EventRSVP)
            .where(EventRSVP.student_id == student_id)
            .options(selectinload(EventRSVP.event))
            .order_by(EventRSVP.registered_at.desc())
        )
        return list(result.scalars().all())

    async def get_event_attendees(
        self, institution_id: UUID, event_id: UUID
    ) -> list[EventRSVP]:
        """
        List attendees for an event (institution admin view).
        Verifies the event belongs to the given institution.
        """
        event = await self._get_event(event_id)
        if event.institution_id != institution_id:
            raise ForbiddenException("Event does not belong to this institution")

        result = await self.db.execute(
            select(EventRSVP)
            .where(EventRSVP.event_id == event_id)
            .order_by(EventRSVP.registered_at.asc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # ICS Export
    # ------------------------------------------------------------------

    async def generate_ics(self, event_id: UUID) -> str:
        """
        Generate an iCalendar (.ics) string for an event.

        Uses the ``icalendar`` library to produce a standards-compliant
        VCALENDAR containing a single VEVENT.
        """
        from icalendar import Calendar, Event as ICSEvent

        event = await self._get_event(event_id)

        cal = Calendar()
        cal.add("prodid", "-//UniPaith//Events//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")

        ics_event = ICSEvent()
        ics_event.add("uid", str(event.id))
        ics_event.add("summary", event.event_name)
        ics_event.add("dtstart", event.start_time)
        ics_event.add("dtend", event.end_time)

        if event.location:
            ics_event.add("location", event.location)
        if event.description:
            ics_event.add("description", event.description)

        ics_event.add("dtstamp", datetime.now(timezone.utc))

        cal.add_component(ics_event)
        return cal.to_ical().decode("utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_event(self, event_id: UUID) -> Event:
        result = await self.db.execute(
            select(Event).where(Event.id == event_id)
        )
        event = result.scalar_one_or_none()
        if not event:
            raise NotFoundException("Event not found")
        return event
