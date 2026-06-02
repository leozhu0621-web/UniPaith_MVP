"""Spec 42 §3.19–§3.20 / §4.17 — Prompt Library request/response schemas.

Shared by ``PromptLibraryService`` (which builds them) and
``api/prompt_library.py`` (which serves them). The frontend types in
``frontend/src/types/promptLibrary.ts`` are the wire mirror of these.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from unipaith.models.prompt_library import (
    COMPETENCIES,
    CONFLICT_TYPES,
    DRAFT_STATUSES,
    ROLE_TYPES,
    STAKEHOLDER_TYPES,
)

# ── Catalog ──────────────────────────────────────────────────────────────────


class BehavioralPromptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prompt_key: str
    title: str
    intent_tag: str
    target_channel: str
    time_limit_seconds: int | None = None
    word_limit: int | None = None
    format_required: str
    evidence_required_flag: bool
    allowed_attachments_flag: bool
    language_option: str
    confidentiality_scope: str
    reuse_allowed_flag: str
    sort_order: int


# ── Responses (§3.19) ────────────────────────────────────────────────────────


class BehavioralResponseUpsert(BaseModel):
    response_text: str | None = Field(default=None, max_length=20000)
    draft_status: str = "draft"
    confidence_self_rating: int | None = Field(default=None, ge=1, le=5)
    needs_feedback_flag: bool = False
    linked_story_id: UUID | None = None

    def validated_draft(self) -> str:
        return self.draft_status if self.draft_status in DRAFT_STATUSES else "draft"


class StarFlags(BaseModel):
    situation: bool = False
    task: bool = False
    action: bool = False
    result: bool = False
    reflection: bool = False


class BehavioralResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prompt_key: str
    response_text: str | None = None
    draft_status: str
    version_count: int
    last_edited: datetime | None = None
    confidence_self_rating: int | None = None
    authenticity_confidence_flag: bool
    needs_feedback_flag: bool
    reviewer_feedback_received_flag: bool
    star_situation_present: bool
    star_task_present: bool
    star_action_present: bool
    star_result_present: bool
    star_reflection_present: bool
    impact_metric_present: bool
    impact_metric_type: str | None = None
    impact_metric_value_band: str | None = None
    linked_story_id: UUID | None = None
    # SignalRecord metadata (§5).
    source: str
    confidence: int
    record_version: int
    updated_at: datetime


# ── Story bank (§3.20) ───────────────────────────────────────────────────────


class StoryBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=8000)
    primary_competency: str | None = None
    secondary_competency: str | None = None
    competency_tags: list[str] = Field(default_factory=list)
    context_tags: list[str] = Field(default_factory=list)
    role_type: str | None = None
    stakeholder_type: str | None = None
    conflict_type: str | None = None
    difficulty_tier: int | None = Field(default=None, ge=1, le=5)
    recency: date | None = None
    duration: str | None = Field(default=None, max_length=80)
    scale_tier: int | None = Field(default=None, ge=1, le=5)
    evidence_link: str | None = Field(default=None, max_length=500)
    referenceable_contact_flag: bool = False

    def _norm_enum(self, value: str | None, allowed: tuple[str, ...]) -> str | None:
        return value if value in allowed else None

    def cleaned(self) -> dict:
        """Drop out-of-vocabulary enum values to None (DB CHECK safety)."""
        data = self.model_dump()
        data["primary_competency"] = self._norm_enum(self.primary_competency, COMPETENCIES)
        data["secondary_competency"] = self._norm_enum(self.secondary_competency, COMPETENCIES)
        data["role_type"] = self._norm_enum(self.role_type, ROLE_TYPES)
        data["stakeholder_type"] = self._norm_enum(self.stakeholder_type, STAKEHOLDER_TYPES)
        data["conflict_type"] = self._norm_enum(self.conflict_type, CONFLICT_TYPES)
        data["competency_tags"] = [t for t in self.competency_tags if t in COMPETENCIES]
        return data


class StoryCreate(StoryBase):
    pass


class StoryUpdate(StoryBase):
    pass


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    summary: str | None = None
    primary_competency: str | None = None
    secondary_competency: str | None = None
    competency_tags: list[str] = Field(default_factory=list)
    context_tags: list[str] = Field(default_factory=list)
    role_type: str | None = None
    stakeholder_type: str | None = None
    conflict_type: str | None = None
    difficulty_tier: int | None = None
    recency: date | None = None
    duration: str | None = None
    scale_tier: int | None = None
    evidence_link: str | None = None
    referenceable_contact_flag: bool
    source: str
    confidence: int
    record_version: int
    created_at: datetime
    updated_at: datetime


# ── Summary (§4.17 overlay + counts) ─────────────────────────────────────────


class PromptLibrarySummary(BaseModel):
    total_prompts: int
    answered_count: int
    final_count: int
    draft_count: int
    stories_count: int
    # §4.17 inference overlay — populated only when ai_prompt_library_v2_enabled.
    inference_enabled: bool
    interview_readiness_band: str | None = None
    interview_readiness_score: int | None = None
    readiness_detail: dict | None = None
    competency_coverage_map: dict | None = None
    competency_coverage_gaps: list[str] | None = None
    story_prompt_matching_table: list[dict] | None = None
    revision_priority_list: list[dict] | None = None
    suggested_practice_plan: str | None = None
