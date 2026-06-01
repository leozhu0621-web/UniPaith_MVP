from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

# Spec 33 §2 interview types + §7 statuses.
INTERVIEW_TYPES = (
    "live",
    "recorded_async",
    "portfolio_review",
    "technical_assessment",
    "third_party_platform",
)
INTERVIEW_STATUSES = ("proposed", "confirmed", "completed", "cancelled", "no_show")
# Types that submit within a window rather than at a fixed live time (§5/§8).
ASYNC_INTERVIEW_TYPES = {"recorded_async", "technical_assessment"}


class ProposeInterviewRequest(BaseModel):
    # Either a single application_id (back-compat) or a list (§5 "applicant(s)").
    application_id: UUID | None = None
    application_ids: list[UUID] | None = None
    # Optional — defaults to the calling staff member's reviewer profile.
    interviewer_id: UUID | None = None
    interview_type: str
    proposed_times: list[str] = []  # ISO8601 slots for live
    duration_minutes: int = 30
    location_or_link: str | None = None
    async_window_end: str | None = None  # ISO8601 deadline for async types
    notes_to_student: str | None = None  # invite notes; mirrored into the Inbox
    ai_draft_used: bool = False

    @model_validator(mode="after")
    def _require_an_applicant(self) -> ProposeInterviewRequest:
        if not self.application_id and not self.application_ids:
            raise ValueError("Provide application_id or application_ids")
        return self

    def resolved_application_ids(self) -> list[UUID]:
        ids = list(self.application_ids or [])
        if self.application_id and self.application_id not in ids:
            ids.insert(0, self.application_id)
        return ids


class ConfirmInterviewRequest(BaseModel):
    # Required for live interviews (must match a proposed slot); optional for async
    # types where accepting the submission window is enough (§3 step 3).
    confirmed_time: str | None = None


class ScoreInterviewRequest(BaseModel):
    criterion_scores: dict
    total_weighted_score: float
    interviewer_notes: str | None = None
    recommendation: str | None = None
    rubric_id: UUID | None = None


class CancelInterviewRequest(BaseModel):
    reason: str | None = None


class RescheduleInterviewRequest(BaseModel):
    proposed_times: list[str] = []  # new ISO8601 slots for live
    async_window_end: str | None = None  # new deadline for async types
    duration_minutes: int | None = None
    location_or_link: str | None = None


# ── Rich response shapes (Spec 33 §7) ───────────────────────────────────────


class InterviewApplicant(BaseModel):
    student_id: UUID | None = None
    name: str = ""


class InterviewProgramRef(BaseModel):
    id: UUID | None = None
    name: str = ""


class InterviewScoreView(BaseModel):
    interviewer_id: UUID
    criterion_scores: dict | None = None
    total_weighted_score: float | None = None
    notes: str | None = None
    recommendation: str | None = None
    created_at: datetime | None = None


class InterviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    application_id: UUID
    applicant: InterviewApplicant = InterviewApplicant()
    program: InterviewProgramRef = InterviewProgramRef()
    interviewer_id: UUID | None = None
    interview_type: str | None = None
    status: str | None = None
    # Async submission window expired with no recording (§8 → "No submission
    # received"); the table renders this distinctly from the raw status.
    async_expired: bool = False
    proposed_times: list | dict | None = None
    proposed_slots: list | None = None  # spec alias for proposed_times
    confirmed_time: datetime | None = None
    scheduled_at: datetime | None = None  # spec alias for confirmed_time
    duration_minutes: int = 30
    location: str | None = None
    meeting_link: str | None = None
    location_or_link: str | None = None
    async_window_end: datetime | None = None
    recording_url: str | None = None
    notes_to_student: str | None = None
    recommendation: str | None = None
    scores: list[InterviewScoreView] = []
    created_at: datetime | None = None


class InterviewScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    interview_id: UUID
    interviewer_id: UUID
    criterion_scores: dict | None
    total_weighted_score: Decimal | None
    interviewer_notes: str | None
    recommendation: str | None


# ── AI helper shapes (Spec 33 §9, gated by ai_interview_v2_enabled) ──────────


class DraftInviteRequest(BaseModel):
    application_id: UUID
    interview_type: str
    proposed_times: list[str] = []
    async_window_end: str | None = None
    duration_minutes: int | None = None
    location_or_link: str | None = None


class DraftInviteResponse(BaseModel):
    available: bool = False
    draft: str | None = None
    tone: str | None = None
    length: str | None = None


class ScorePrefillRequest(BaseModel):
    rubric_id: UUID | None = None
    transcript_or_notes: str = ""


class ScorePrefillResponse(BaseModel):
    available: bool = False
    criterion_scores: dict = {}
    overall_note: str | None = None
    recommendation: str | None = None
