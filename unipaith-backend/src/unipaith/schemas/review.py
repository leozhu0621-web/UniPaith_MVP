from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreateRubricRequest(BaseModel):
    rubric_name: str
    criteria: list[dict]
    program_id: UUID | None = None


class RubricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
    program_id: UUID | None
    rubric_name: str
    criteria: Any | None
    is_active: bool
    created_at: datetime


class ScoreApplicationRequest(BaseModel):
    rubric_id: UUID
    criterion_scores: dict
    reviewer_notes: str | None = None


class ApplicationScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    reviewer_id: UUID
    rubric_id: UUID
    criterion_scores: dict | None
    total_weighted_score: Decimal | None
    reviewer_notes: str | None
    scored_by_type: str | None
    scored_at: datetime


class ReviewAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    reviewer_id: UUID
    assigned_at: datetime
    due_date: datetime | None = None
    status: str | None


class AIReviewSummaryResponse(BaseModel):
    summary: str
    strengths: list[str]
    concerns: list[str]
    recommended_score_range: dict | None


class PipelineResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    total: int
    program_id: str | None = None
