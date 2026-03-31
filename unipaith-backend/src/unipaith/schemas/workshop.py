from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Essay schemas
# ---------------------------------------------------------------------------


class CreateEssayRequest(BaseModel):
    program_id: UUID
    essay_type: str
    content: str
    prompt_text: str | None = None


class UpdateEssayRequest(BaseModel):
    content: str
    prompt_text: str | None = None


class RequestEssayFeedbackRequest(BaseModel):
    feedback_type: str = "full_review"


class EssayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    program_id: UUID
    prompt_text: str | None
    essay_version: int
    content: str | None
    word_count: int | None
    ai_feedback: dict | None
    status: str | None
    created_at: datetime
    updated_at: datetime


class EssayFeedbackResponse(BaseModel):
    overall_score: int | None
    strengths: list[str] | None
    improvements: list[str] | None
    prompt_alignment_score: int | None
    feedback_text: str | None


# ---------------------------------------------------------------------------
# Resume schemas
# ---------------------------------------------------------------------------


class AutoGenerateResumeRequest(BaseModel):
    format_type: str = "standard"
    target_program_id: UUID | None = None


class UpdateResumeRequest(BaseModel):
    content: dict


class RequestResumeFeedbackRequest(BaseModel):
    feedback_type: str = "full_review"


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    resume_version: int
    content: dict | None
    rendered_pdf_url: str | None
    ai_suggestions: dict | None
    target_program_id: UUID | None
    status: str | None
    created_at: datetime
    updated_at: datetime


class ResumeFeedbackResponse(BaseModel):
    overall_score: int | None
    section_scores: dict | None
    suggestions: list[dict] | None
    feedback_text: str | None
