from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateIntakeRoundRequest(BaseModel):
    round_name: str = Field(min_length=1, max_length=100)
    intake_term: str | None = None
    application_open: date | None = None
    application_deadline: date | None = None
    decision_date: date | None = None
    program_start: date | None = None
    capacity: int | None = Field(None, ge=1)
    requirements: dict | None = None
    sort_order: int = 0


class UpdateIntakeRoundRequest(BaseModel):
    round_name: str | None = Field(None, min_length=1, max_length=100)
    intake_term: str | None = None
    application_open: date | None = None
    application_deadline: date | None = None
    decision_date: date | None = None
    program_start: date | None = None
    capacity: int | None = Field(None, ge=1)
    requirements: dict | None = None
    status: str | None = Field(
        None,
        pattern=r"^(upcoming|open|closed|completed)$",
    )
    is_active: bool | None = None
    sort_order: int | None = None


class IntakeRoundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    program_id: UUID
    round_name: str
    intake_term: str | None
    application_open: date | None
    application_deadline: date | None
    decision_date: date | None
    program_start: date | None
    capacity: int | None
    enrolled_count: int
    requirements: dict | None
    status: str
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime
    spots_remaining: int | None = None
