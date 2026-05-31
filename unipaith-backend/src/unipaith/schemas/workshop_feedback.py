"""Phase A — Workshop feedback Pydantic schemas (feedback-only)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

WorkshopDomain = Literal["essay", "interview", "test"]
WorkshopMode = Literal["general", "program_specific"]
IssueSeverity = Literal["minor", "moderate", "major"]
ElementImportance = Literal["nice_to_have", "should_have", "required"]
PrepPriority = Literal["low", "med", "high"]


class EssayFeedbackRequest(BaseModel):
    essay_text: str = Field(min_length=20, max_length=20_000)
    prompt_text: str | None = Field(None, max_length=4000)
    target_program_id: UUID | None = None
    mode: WorkshopMode = "general"
    document_id: UUID | None = None


class InterviewPracticeRequest(BaseModel):
    target_program_id: UUID | None = None
    mode: WorkshopMode = "general"
    interview_type: Literal["behavioral", "technical", "general"] = "general"
    focus_area: str | None = Field(None, max_length=200)
    response_text: str | None = Field(None, max_length=20_000)
    question_text: str | None = Field(None, max_length=4000)


class TestGuidanceRequest(BaseModel):
    __test__ = False

    test_type: Literal["GRE", "GMAT", "TOEFL", "IELTS", "MCAT", "LSAT", "SAT", "ACT"]
    current_score: float | None = Field(None, ge=0, le=2000)
    target_score: float | None = Field(None, ge=0, le=2000)
    target_program_id: UUID | None = None
    mode: WorkshopMode = "general"


class StructuralIssue(BaseModel):
    issue: str = Field(min_length=1, max_length=500)
    severity: IssueSeverity
    location_ref: str | None = Field(None, max_length=120)


class MissingElement(BaseModel):
    element: str = Field(min_length=1, max_length=300)
    importance: ElementImportance


class SuggestedQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    why: str = Field(min_length=1, max_length=1000)


class GapAnalysisItem(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    recommendation: str = Field(min_length=1, max_length=500)


class PrepRecommendation(BaseModel):
    action: str = Field(min_length=1, max_length=500)
    time_commitment: str = Field(min_length=1, max_length=120)
    priority: PrepPriority


class WorkshopFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    domain: WorkshopDomain
    mode: WorkshopMode = "general"
    target_program_id: UUID | None = None
    input_text: str | None = None
    input_artifact_id: str | None = None
    prompt_text: str | None = None
    rubric_scores: dict[str, float] = Field(default_factory=dict)
    structural_issues: list[StructuralIssue] = Field(default_factory=list)
    missing_elements: list[MissingElement] = Field(default_factory=list)
    suggested_questions: list[SuggestedQuestion] = Field(default_factory=list)
    current_band: str | None = None
    target_band: str | None = None
    gap_analysis: list[GapAnalysisItem] = Field(default_factory=list)
    prep_recommendations: list[PrepRecommendation] = Field(default_factory=list)
    readiness_summary: str | None = None
    is_stub: bool
    created_at: datetime
