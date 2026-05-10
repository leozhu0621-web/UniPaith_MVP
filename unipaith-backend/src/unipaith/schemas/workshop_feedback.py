"""Phase A — Workshop feedback Pydantic schemas (feedback-only).

The output schema deliberately has NO field that could carry a generated
essay / answer / draft back to the student. The fields exist to express
COACHING:

  rubric_scores       — {dimension: 0..5}
  structural_issues   — [{issue, severity, location_ref}]
  missing_elements    — [{element, importance}]
  suggested_questions — [{question, why}]    (interview / test contexts)

A CI test (tests/test_workshop_no_generation_contract.py) asserts this
schema cannot ever sprout a `revised_text`, `improved_text`,
`generated_essay`, `draft`, `model_answer`, etc. field. If a future change
re-introduces generation, CI breaks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

WorkshopDomain = Literal["essay", "interview", "test"]
IssueSeverity = Literal["minor", "moderate", "major"]
ElementImportance = Literal["nice_to_have", "should_have", "required"]


# ── Request shapes ────────────────────────────────────────────────────────


class EssayFeedbackRequest(BaseModel):
    """Request a structured rubric on an essay the student already wrote.
    `essay_text` is what they want feedback ON; we never rewrite it."""

    essay_text: str = Field(min_length=20, max_length=20_000)
    prompt_text: str | None = Field(None, max_length=4000)
    target_program_id: UUID | None = None
    document_id: UUID | None = None  # optional pointer to student_documents


class InterviewPracticeRequest(BaseModel):
    target_program_id: UUID | None = None
    interview_type: Literal["behavioral", "technical", "general"] = "general"
    # If set, ask narrower questions framed for this role/program. Free-form
    # so program-specific phrasing can be passed without a schema enum.
    focus_area: str | None = Field(None, max_length=200)


class TestGuidanceRequest(BaseModel):
    # `__test__ = False` tells pytest not to treat this Pydantic model as a
    # test class just because its name starts with `Test`. Pytest can't
    # actually collect it (Pydantic has __init__) but the warning is noise.
    __test__ = False

    test_type: Literal["GRE", "GMAT", "TOEFL", "IELTS", "MCAT", "LSAT", "SAT", "ACT"]
    current_score: float | None = Field(None, ge=0, le=2000)
    target_score: float | None = Field(None, ge=0, le=2000)


# ── Response shapes (FEEDBACK-ONLY) ───────────────────────────────────────


class StructuralIssue(BaseModel):
    issue: str = Field(min_length=1, max_length=500)
    severity: IssueSeverity
    # Free-form anchor back into the input ("paragraph 2", "intro",
    # "lines 14-18"). Plan 2 may upgrade this to char offsets.
    location_ref: str | None = Field(None, max_length=120)


class MissingElement(BaseModel):
    element: str = Field(min_length=1, max_length=300)
    importance: ElementImportance


class SuggestedQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    why: str = Field(min_length=1, max_length=1000)


class WorkshopFeedbackResponse(BaseModel):
    """Returned from POST /me/workshops/{essay|interview|test}/feedback.

    NOTE: this is the contract that test_workshop_no_generation_contract.py
    inspects. Adding any field that could carry generated prose
    (`revised_text`, `improved_text`, `model_answer`, etc.) will break that
    test on purpose.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    domain: WorkshopDomain
    input_artifact_id: str | None = None
    prompt_text: str | None = None
    rubric_scores: dict[str, float] = Field(default_factory=dict)
    structural_issues: list[StructuralIssue] = Field(default_factory=list)
    missing_elements: list[MissingElement] = Field(default_factory=list)
    suggested_questions: list[SuggestedQuestion] = Field(default_factory=list)
    is_stub: bool
    created_at: datetime
