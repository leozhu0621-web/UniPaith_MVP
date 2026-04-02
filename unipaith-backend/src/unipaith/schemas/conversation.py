from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ConversationStage = Literal[
    "understand_context",
    "identify_issues",
    "define_demand",
    "translate_requirements",
    "ready_for_shortlist",
]

ConversationDomain = Literal[
    "academic_readiness",
    "budget_finance",
    "country_location",
    "timeline_intake",
    "career_outcome",
    "eligibility_compliance",
    "learning_preferences",
]

RequirementPriority = Literal["must_have", "should_have", "optional"]
RequirementSource = Literal["student_explicit", "inferred", "imported"]
RequirementStatus = Literal["draft", "confirmed", "rejected"]
ConfidenceLevel = Literal["insufficient", "provisional", "recommendation_ready", "high_confidence"]


class ConversationTurnRequest(BaseModel):
    session_id: UUID | None = None
    message: str = Field(min_length=1, max_length=4000)
    entrypoint: Literal["chat", "discover_shortcut", "resume"] = "chat"
    context_program_id: UUID | None = None
    client_event_id: str | None = None


class ConversationSessionResponse(BaseModel):
    session_id: UUID
    student_id: UUID
    current_stage: ConversationStage
    active_domain: ConversationDomain
    turn_count: int
    last_updated_at: datetime


class AssistantMessageResponse(BaseModel):
    message_id: UUID
    reply_text: str
    why_asked: str | None = None
    suggested_next_actions: list[str] = []


class ConversationStateDeltaResponse(BaseModel):
    updated_domains: list[ConversationDomain] = []
    new_requirements_count: int = 0
    new_conflicts_count: int = 0


class ConfidenceSummaryResponse(BaseModel):
    global_confidence: int = Field(ge=0, le=100)
    global_level: ConfidenceLevel


class ConversationTurnResponse(BaseModel):
    session: ConversationSessionResponse
    assistant_message: AssistantMessageResponse
    state_delta: ConversationStateDeltaResponse
    confidence_summary: ConfidenceSummaryResponse


class ConversationRequirementResponse(BaseModel):
    requirement_id: UUID
    domain: ConversationDomain
    field: str
    value: Any | None = None
    priority: RequirementPriority
    source: RequirementSource
    confidence: int = Field(ge=0, le=100)
    status: RequirementStatus
    evidence_turn_ids: list[UUID] = []
    updated_at: datetime


class ListConversationRequirementsResponse(BaseModel):
    requirements: list[ConversationRequirementResponse] = []


class UpdateConversationRequirementRequest(BaseModel):
    status: RequirementStatus | None = None
    value: Any | None = None
    priority: RequirementPriority | None = None


class DomainConfidenceResponse(BaseModel):
    domain: ConversationDomain
    status: Literal["unknown", "partial", "sufficient", "conflicting"]
    confidence: int = Field(ge=0, le=100)
    missing_fields: list[str] = []
    conflicts: list[str] = []


class ConfidenceReportResponse(BaseModel):
    global_confidence: int = Field(ge=0, le=100)
    global_level: ConfidenceLevel
    domain_scores: list[DomainConfidenceResponse] = []
    blocking_issues: list[str] = []
    computed_at: datetime


class ShortlistUnlockThresholdsResponse(BaseModel):
    global_min: int = Field(ge=0, le=100)
    domain_min: int = Field(ge=0, le=100)


class ShortlistUnlockResponse(BaseModel):
    eligible: bool
    reasons: list[str] = []
    thresholds: ShortlistUnlockThresholdsResponse
    blocking_conflicts: list[str] = []
    missing_required_fields: list[str] = []
    recommended_next_actions: list[str] = []


class ResumeCheckpointResponse(BaseModel):
    session: ConversationSessionResponse
    checkpoint_summary: str
    open_tasks: list[str] = []
    last_assistant_prompt: str | None = None


class ResolveConflictRequest(BaseModel):
    selected_resolution: str = Field(min_length=1, max_length=2000)


class ResolveConflictResponse(BaseModel):
    conflict_id: UUID
    resolved: bool
    selected_resolution: str
    updated_confidence: ConfidenceSummaryResponse


class ConversationError(BaseModel):
    code: Literal[
        "validation_error",
        "not_found",
        "forbidden",
        "conflict_unresolved",
        "insufficient_confidence",
        "rate_limited",
    ]
    message: str
    details: dict[str, Any] | None = None


class ConversationErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    error: ConversationError
