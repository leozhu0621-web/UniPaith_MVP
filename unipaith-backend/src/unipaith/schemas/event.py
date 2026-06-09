from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateEventRequest(BaseModel):
    event_name: str
    event_type: str
    start_time: datetime
    end_time: datetime
    description: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    capacity: int | None = None
    program_id: UUID | None = None


class UpdateEventRequest(BaseModel):
    event_name: str | None = None
    event_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    description: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    capacity: int | None = None
    status: str | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
    program_id: UUID | None
    school_id: UUID | None = None
    event_name: str
    event_type: str | None
    description: str | None
    location: str | None
    meeting_link: str | None = None
    start_time: datetime
    end_time: datetime
    capacity: int | None
    rsvp_count: int
    # Spec 27 §3.1 — confirmed vs waitlisted split (computed against capacity).
    confirmed_count: int = 0
    waitlist_count: int = 0
    view_count: int = 0
    status: str | None
    source: str = "manual"
    source_url: str | None = None
    created_at: datetime


class AttendanceUpdateRequest(BaseModel):
    """Spec 27 §3.1 — mark a single RSVP's attendance after the event."""

    attendance_status: str  # 'attended' | 'no_show'


class RSVPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    student_id: UUID
    rsvp_status: str | None
    registered_at: datetime
    attended_at: datetime | None
    # Spec 27 §3.1 — attendance capture: attended | no_show | null.
    attendance_status: str | None = None
    # Convenience fields for the institution attendee roster (populated by route).
    student_name: str | None = None
    student_email: str | None = None
