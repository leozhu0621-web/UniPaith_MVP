from __future__ import annotations

from datetime import date, datetime
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
    due_date: date | None = None
    status: str | None


class AIReviewSummaryResponse(BaseModel):
    summary: str
    strengths: list[str]
    concerns: list[str]
    recommended_score_range: dict | None
    comparable_admitted_profiles: str | None = None


class EvidenceCitation(BaseModel):
    field: str
    value: str
    citation: str | None = None


class CriterionAssessment(BaseModel):
    criterion_name: str
    score: float | None = None
    max_score: float = 10
    assessment: str
    evidence: list[EvidenceCitation] = []


class AIPacketSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID | None = None
    application_id: UUID
    rubric_id: UUID | None = None
    overall_summary: str
    strengths: list[dict] | None = None
    concerns: list[dict] | None = None
    criterion_assessments: list[dict] | None = None
    recommended_score: Decimal | None = None
    confidence_level: str | None = None
    model_used: str | None = None
    generated_at: datetime | None = None


class PipelineResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    total: int
    program_id: str | None = None
