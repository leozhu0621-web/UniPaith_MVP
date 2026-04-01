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
    capacity: int | None = None
    program_id: UUID | None = None


class UpdateEventRequest(BaseModel):
    event_name: str | None = None
    event_type: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    description: str | None = None
    location: str | None = None
    capacity: int | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
    program_id: UUID | None
    event_name: str
    event_type: str | None
    description: str | None
    location: str | None
    start_time: datetime
    end_time: datetime
    capacity: int | None
    rsvp_count: int
    status: str | None
    created_at: datetime


class RSVPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_id: UUID
    student_id: UUID
    rsvp_status: str | None
    registered_at: datetime
    attended_at: datetime | None
