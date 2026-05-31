"""Spec 16 · Calendar — Pydantic schemas.

The ``CalendarItem`` response mirrors Spec 16 §6 exactly, plus a few
display-only helpers (``subtitle``, ``link``, ``institution_name``,
``recommender_name``, ``editable``) the frontend uses to render rows and
deep-links without re-deriving them.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CalendarItemType = Literal[
    "interview_live",
    "interview_recorded_window",
    "campus_visit",
    "info_session",
    "portfolio_review",
    "audition",
    "submission_deadline",
    "document_deadline",
    "recommendation_deadline",
    "interview_submission_deadline",
    "deposit_deadline",
    "reminder",
    "work_block",
]

CalendarItemStatus = Literal["scheduled", "completed", "cancelled", "overdue"]

ReminderChannel = Literal["email", "push", "in_app"]


class ReminderSettings(BaseModel):
    lead_time_minutes: int = Field(default=60, ge=0, le=20160)  # up to 14 days
    channels: list[ReminderChannel] = Field(default_factory=lambda: ["in_app"])


class CalendarItem(BaseModel):
    """Spec 16 §6 — one item on the unified admissions timeline."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: CalendarItemType
    title: str
    start_at: datetime
    end_at: datetime | None = None
    location: str | None = None
    meeting_link: str | None = None
    application_id: UUID | None = None
    status: CalendarItemStatus = "scheduled"
    notes: str | None = None
    reminder_settings: ReminderSettings | None = None
    # ── display helpers (not part of the §6 contract) ──
    subtitle: str | None = None
    link: str | None = None
    institution_name: str | None = None
    recommender_name: str | None = None
    confirmation_url: str | None = None
    editable: bool = False
    interview_id: UUID | None = None
    can_decline: bool = False
    can_reschedule: bool = False


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    start_at: datetime
    notes: str | None = Field(default=None, max_length=2000)
    application_id: UUID | None = None
    reminder_settings: ReminderSettings | None = None


class WorkBlockCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    start_at: datetime
    end_at: datetime | None = None
    duration_minutes: int | None = Field(default=None, ge=5, le=1440)
    category: str | None = Field(default=None, max_length=30)
    application_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=2000)


class CalendarItemPatch(BaseModel):
    status: CalendarItemStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)
    title: str | None = Field(default=None, max_length=255)
    start_at: datetime | None = None
    end_at: datetime | None = None
    confirmation_url: str | None = Field(default=None, max_length=1000)
