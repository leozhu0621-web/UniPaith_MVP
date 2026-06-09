"""
Event service — event management, RSVP handling, and calendar integration.
Supports creating events, managing RSVPs with capacity control, and ICS export.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.config import settings
from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from unipaith.models.engagement import Conversation, Message, StudentCalendar
from unipaith.models.institution import Event, EventRSVP, Institution

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
        meeting_link: str | None = None,
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
            meeting_link=meeting_link,
            start_time=start_time,
            end_time=end_time,
            capacity=capacity,
            rsvp_count=0,
            status="upcoming",
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def update_event(
        self,
        institution_id: UUID,
        event_id: UUID,
        **kwargs: object,
    ) -> Event:
        """Update an event's mutable fields."""
        event = await self._get_event(event_id)
        if event.institution_id != institution_id:
            raise ForbiddenException("Event does not belong to this institution")
        for key, value in kwargs.items():
            if value is not None:
                setattr(event, key, value)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def cancel_event(self, institution_id: UUID, event_id: UUID) -> Event:
        """Cancel an event."""
        event = await self._get_event(event_id)
        if event.institution_id != institution_id:
            raise ForbiddenException("Event does not belong to this institution")
        if event.status == "cancelled":
            raise BadRequestException("Event is already cancelled")
        event.status = "cancelled"
        await self.db.flush()
        # Spec 27 §7 — every RSVP'd student is notified of the cancellation.
        await self._notify_cancellation(event)
        await self.db.refresh(event)
        await self._attach_counts([event])
        return event

    async def mark_attendance(
        self,
        institution_id: UUID,
        event_id: UUID,
        rsvp_id: UUID,
        attendance_status: str,
    ) -> EventRSVP:
        """Spec 27 §3.1 — record an attendee's attendance: attended | no_show."""
        if attendance_status not in ("attended", "no_show"):
            raise BadRequestException("attendance_status must be 'attended' or 'no_show'")
        event = await self._get_event(event_id)
        if event.institution_id != institution_id:
            raise ForbiddenException("Event does not belong to this institution")
        rsvp = await self.db.get(EventRSVP, rsvp_id)
        if rsvp is None or rsvp.event_id != event_id:
            raise NotFoundException("RSVP not found")
        rsvp.attendance_status = attendance_status
        rsvp.attended_at = datetime.now(UTC) if attendance_status == "attended" else None
        await self.db.flush()
        await self.db.refresh(rsvp)
        return rsvp

    async def _notify_cancellation(self, event: Event) -> None:
        """Spec 27 §7 — post an Inbox system message to every RSVP'd student and
        remove their calendar item. Best-effort: never blocks the cancellation."""
        try:
            rsvps = list(
                (await self.db.execute(select(EventRSVP).where(EventRSVP.event_id == event.id)))
                .scalars()
                .all()
            )
            if not rsvps:
                return
            inst = await self.db.get(Institution, event.institution_id)
            sender_id = inst.admin_user_id if inst else None
            now = datetime.now(UTC)
            when = event.start_time.strftime("%b %-d, %-I:%M %p")
            for rsvp in rsvps:
                await self.db.execute(
                    delete(StudentCalendar).where(
                        StudentCalendar.student_id == rsvp.student_id,
                        StudentCalendar.entry_type == "event",
                        StudentCalendar.reference_id == event.id,
                    )
                )
                if sender_id is None:
                    continue
                conv = await self.db.scalar(
                    select(Conversation).where(
                        Conversation.student_id == rsvp.student_id,
                        Conversation.institution_id == event.institution_id,
                        Conversation.thread_type == "system",
                    )
                )
                if conv is None:
                    conv = Conversation(
                        student_id=rsvp.student_id,
                        institution_id=event.institution_id,
                        subject="Event updates",
                        status="active",
                        thread_type="system",
                        started_at=now,
                        last_message_at=now,
                    )
                    self.db.add(conv)
                    await self.db.flush()
                self.db.add(
                    Message(
                        conversation_id=conv.id,
                        sender_id=sender_id,
                        sender_type="system",
                        message_body=(
                            f"{event.event_name} on {when} has been cancelled. "
                            "We're sorry for the inconvenience."
                        ),
                        sent_at=now,
                    )
                )
                conv.last_message_at = now
            await self.db.flush()
        except Exception as exc:  # noqa: BLE001 — notification is best-effort
            logger.warning("Event cancellation notification failed (non-fatal): %s", exc)

    async def _attach_counts(self, events: list[Event]) -> list[Event]:
        """Spec 27 §3.1 — attach confirmed/waitlist counts as transient attributes
        so EventResponse (from_attributes) can surface 'RSVP'd: N / capacity' + waitlist."""
        if not events:
            return events
        ids = [e.id for e in events]
        rows = await self.db.execute(
            select(EventRSVP.event_id, EventRSVP.rsvp_status, func.count())
            .where(EventRSVP.event_id.in_(ids))
            .group_by(EventRSVP.event_id, EventRSVP.rsvp_status)
        )
        waitlist: dict[UUID, int] = {}
        for ev_id, st, cnt in rows.all():
            if st == "waitlisted":
                waitlist[ev_id] = waitlist.get(ev_id, 0) + int(cnt)
        for e in events:
            e.confirmed_count = e.rsvp_count or 0
            e.waitlist_count = waitlist.get(e.id, 0)
        return events

    async def list_upcoming_events(
        self,
        program_id: UUID | None = None,
        institution_id: UUID | None = None,
        school_id: UUID | None = None,
        event_type: str | None = None,
        limit: int = 20,
        institution_scope: bool = False,
    ) -> list[Event]:
        """List published upcoming events with optional filters."""
        now = datetime.now(UTC)
        query = select(Event).where(
            Event.start_time > now,
            Event.status == "upcoming",
        )

        if program_id:
            query = query.where(Event.program_id == program_id)
        if institution_id:
            query = query.where(Event.institution_id == institution_id)
        if school_id:
            query = query.where(Event.school_id == school_id)
        if institution_scope:
            # Institution page: institution-wide events only (no school/program
            # copies), so the same event doesn't appear twice.
            query = query.where(Event.school_id.is_(None), Event.program_id.is_(None))
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
        return await self._attach_counts(list(result.scalars().all()))

    # ------------------------------------------------------------------
    # RSVP
    # ------------------------------------------------------------------

    async def rsvp(self, student_id: UUID, event_id: UUID, user_id: UUID) -> EventRSVP:
        """RSVP a student to an event (Spec 20 §5).

        At capacity the student joins the **waitlist** (no 409). A confirmed
        RSVP adds a Calendar item (Spec 16). Both confirmed and waitlisted
        RSVPs post an Inbox confirmation (Spec 17). ``rsvp_count`` tracks only
        confirmed seats.
        """
        event = await self._get_event(event_id)

        existing = await self.db.execute(
            select(EventRSVP).where(
                EventRSVP.event_id == event_id,
                EventRSVP.student_id == student_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Already RSVP'd to this event")

        now = datetime.now(UTC)
        at_capacity = event.capacity is not None and (event.rsvp_count or 0) >= event.capacity
        rsvp_status = "waitlisted" if at_capacity else "registered"

        rsvp = EventRSVP(
            event_id=event_id,
            student_id=student_id,
            rsvp_status=rsvp_status,
            registered_at=now,
        )
        self.db.add(rsvp)

        if rsvp_status == "registered":
            event.rsvp_count = (event.rsvp_count or 0) + 1
            self._add_calendar_item(student_id, event, now)

        await self._inbox_confirm(student_id, user_id, event, waitlisted=at_capacity)
        await self.db.flush()
        return rsvp

    async def cancel_rsvp(self, student_id: UUID, event_id: UUID) -> None:
        """Cancel an RSVP, free the calendar item, and promote the next
        waitlisted student if a confirmed seat opened up (Spec 20 §5)."""
        result = await self.db.execute(
            select(EventRSVP).where(
                EventRSVP.event_id == event_id,
                EventRSVP.student_id == student_id,
            )
        )
        rsvp = result.scalar_one_or_none()
        if not rsvp:
            raise NotFoundException("RSVP not found")

        was_registered = rsvp.rsvp_status == "registered"
        await self.db.delete(rsvp)
        await self.db.flush()

        event = await self._get_event(event_id)
        await self.db.execute(
            delete(StudentCalendar).where(
                StudentCalendar.student_id == student_id,
                StudentCalendar.entry_type == "event",
                StudentCalendar.reference_id == event_id,
            )
        )

        if was_registered:
            event.rsvp_count = max((event.rsvp_count or 0) - 1, 0)
            await self._promote_waitlist(event)

        await self.db.flush()

    async def _promote_waitlist(self, event: Event) -> None:
        """Promote the longest-waiting waitlisted student into the freed seat."""
        if event.capacity is not None and (event.rsvp_count or 0) >= event.capacity:
            return
        nxt = await self.db.scalar(
            select(EventRSVP)
            .where(EventRSVP.event_id == event.id, EventRSVP.rsvp_status == "waitlisted")
            .order_by(EventRSVP.registered_at.asc())
            .limit(1)
        )
        if nxt is None:
            return
        nxt.rsvp_status = "registered"
        event.rsvp_count = (event.rsvp_count or 0) + 1
        self._add_calendar_item(nxt.student_id, event, datetime.now(UTC))
        await self._inbox_confirm(nxt.student_id, None, event, waitlisted=False, promoted=True)

    def _add_calendar_item(self, student_id: UUID, event: Event, now: datetime) -> None:
        reminder_at = event.start_time - timedelta(hours=settings.event_rsvp_reminder_hours)
        self.db.add(
            StudentCalendar(
                student_id=student_id,
                entry_type="event",
                reference_id=event.id,
                title=event.event_name,
                description=event.description,
                start_time=event.start_time,
                end_time=event.end_time,
                location=event.location,
                meeting_link=event.meeting_link,
                reminder_at=reminder_at if reminder_at > now else None,
            )
        )

    async def _inbox_confirm(
        self,
        student_id: UUID,
        user_id: UUID | None,
        event: Event,
        *,
        waitlisted: bool,
        promoted: bool = False,
    ) -> None:
        """Post an Inbox confirmation (Spec 20 §5 → Spec 17) as a system message
        in the student's institution thread. Best-effort: never blocks the RSVP."""
        try:
            inst = await self.db.get(Institution, event.institution_id)
            sender_id = inst.admin_user_id if inst else user_id
            if sender_id is None:
                return
            now = datetime.now(UTC)
            conv = await self.db.scalar(
                select(Conversation).where(
                    Conversation.student_id == student_id,
                    Conversation.institution_id == event.institution_id,
                    Conversation.thread_type == "system",
                )
            )
            if conv is None:
                conv = Conversation(
                    student_id=student_id,
                    institution_id=event.institution_id,
                    subject="Event updates",
                    status="active",
                    thread_type="system",
                    started_at=now,
                    last_message_at=now,
                )
                self.db.add(conv)
                await self.db.flush()

            when = event.start_time.strftime("%b %-d, %-I:%M %p")
            if waitlisted:
                body = (
                    f"You've joined the waitlist for {event.event_name}. "
                    "We'll notify you if a spot opens up."
                )
            elif promoted:
                body = f"A spot opened up — you're now confirmed for {event.event_name} on {when}."
            else:
                body = f"You're confirmed for {event.event_name} on {when}."

            self.db.add(
                Message(
                    conversation_id=conv.id,
                    sender_id=sender_id,
                    sender_type="system",
                    message_body=body,
                    sent_at=now,
                )
            )
            conv.last_message_at = now
            await self.db.flush()
        except Exception as exc:  # noqa: BLE001 — confirmation is best-effort
            logger.warning("RSVP inbox confirmation failed (non-fatal): %s", exc)

    async def list_student_rsvps(self, student_id: UUID) -> list[EventRSVP]:
        """List all RSVPs for a student, with event details loaded."""
        result = await self.db.execute(
            select(EventRSVP)
            .where(EventRSVP.student_id == student_id)
            .options(selectinload(EventRSVP.event))
            .order_by(EventRSVP.registered_at.desc())
        )
        return list(result.scalars().all())

    async def get_event_attendees(self, institution_id: UUID, event_id: UUID) -> list[EventRSVP]:
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
        rsvps = list(result.scalars().all())
        # Spec 27 §3.1 — enrich the roster with student name + email.
        if rsvps:
            from unipaith.models.student import StudentProfile
            from unipaith.models.user import User

            sids = [r.student_id for r in rsvps]
            rows = await self.db.execute(
                select(
                    StudentProfile.id,
                    StudentProfile.first_name,
                    StudentProfile.last_name,
                    StudentProfile.preferred_name,
                    User.email,
                )
                .join(User, User.id == StudentProfile.user_id)
                .where(StudentProfile.id.in_(sids))
            )
            info: dict = {}
            for sid, fn, ln, pn, email in rows.all():
                name = pn or " ".join(x for x in [fn, ln] if x) or None
                info[sid] = (name, email)
            for r in rsvps:
                nm, em = info.get(r.student_id, (None, None))
                r.student_name = nm
                r.student_email = em
        return rsvps

    # ------------------------------------------------------------------
    # ICS Export
    # ------------------------------------------------------------------

    async def generate_ics(self, event_id: UUID) -> str:
        """
        Generate an iCalendar (.ics) string for an event.

        Uses the ``icalendar`` library to produce a standards-compliant
        VCALENDAR containing a single VEVENT.
        """
        from icalendar import Calendar
        from icalendar import Event as ICSEvent

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

        ics_event.add("dtstamp", datetime.now(UTC))

        cal.add_component(ics_event)
        return cal.to_ical().decode("utf-8")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_event(self, event_id: UUID) -> Event:
        result = await self.db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise NotFoundException("Event not found")
        return event
