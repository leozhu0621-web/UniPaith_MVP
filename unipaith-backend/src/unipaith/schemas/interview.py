from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProposeInterviewRequest(BaseModel):
    application_id: UUID
    interviewer_id: UUID
    interview_type: str
    proposed_times: list[str]
    duration_minutes: int = 30
    location_or_link: str | None = None


class ConfirmInterviewRequest(BaseModel):
    confirmed_time: str


class ScoreInterviewRequest(BaseModel):
    criterion_scores: dict
    total_weighted_score: float
    interviewer_notes: str | None = None
    recommendation: str | None = None
    rubric_id: UUID | None = None


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    interviewer_id: UUID
    interview_type: str | None
    proposed_times: list | dict | None
    confirmed_time: datetime | None
    location_or_link: str | None
    status: str | None
    duration_minutes: int
    created_at: datetime


class InterviewScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interview_id: UUID
    interviewer_id: UUID
    criterion_scores: dict | None
    total_weighted_score: Decimal | None
    interviewer_notes: str | None
    recommendation: str | None
