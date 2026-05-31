"""Phase A — Discovery Pydantic schemas.

Request/response shapes for the Stage 1 (Discovery) journey API. Plan 2 (LLM)
is the producer of `extracted_signals` and assistant content; these schemas are
deliberately permissive on those fields so the LLM stack can evolve without
breaking the contract.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DiscoveryTrack = Literal["profile", "goals", "needs"]
DiscoveryLayer = Literal["basic", "personality", "identity"]
DiscoveryStatus = Literal["active", "completed", "abandoned"]
DiscoveryRole = Literal["student", "assistant", "system"]


class StartSessionRequest(BaseModel):
    track: DiscoveryTrack
    # Required when track='profile', forbidden otherwise. Validated server-side
    # because cross-field validation is clearer there than in pydantic.
    layer: DiscoveryLayer | None = None


class UpdateSessionRequest(BaseModel):
    status: DiscoveryStatus | None = None
    completion_pct: Decimal | None = Field(None, ge=0, le=1)
    exit_signal: dict | None = None


class AppendMessageRequest(BaseModel):
    role: DiscoveryRole
    content: str = Field(min_length=1, max_length=20_000)
    # Free-form JSON; Plan 2 owns the schema of what fields are written.
    extracted_signals: dict | None = None


class DiscoveryMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: DiscoveryRole
    content: str
    extracted_signals: dict | None = None
    created_at: datetime


class DiscoverySessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    track: DiscoveryTrack
    layer: DiscoveryLayer | None = None
    status: DiscoveryStatus
    completion_pct: Decimal
    exit_signal: dict | None = None
    started_at: datetime
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DiscoverySessionDetailResponse(DiscoverySessionResponse):
    messages: list[DiscoveryMessageResponse] = Field(default_factory=list)


class CompletionMapResponse(BaseModel):
    """Per-track completion 0–1, plus identity-layer completion as a separate
    signal. Identity is technically a layer of the 'profile' track but the UI
    surfaces it as its own progress dimension."""

    profile: Decimal = Field(ge=0, le=1)
    goals: Decimal = Field(ge=0, le=1)
    needs: Decimal = Field(ge=0, le=1)
    identity: Decimal = Field(ge=0, le=1)


class AppendMessageResponse(BaseModel):
    """Returned from POST /sessions/{id}/messages. Always includes the persisted
    student message; if the role was 'student', also includes the stub assistant
    reply that Plan 2 will replace with a real LLM-generated response."""

    student_message: DiscoveryMessageResponse
    assistant_message: DiscoveryMessageResponse | None = None


class PersonalitySignalResponse(BaseModel):
    """One personality-layer facet for the Discover artifact rail (spec 19 §6).
    Reconstructed from profile-session extractions; confidence 0–100 drives the
    widget's confidence dots."""

    facet: str
    value: str
    evidence: str | None = None
    confidence: int | None = Field(None, ge=0, le=100)


class HandoffJudgeResponse(BaseModel):
    """Deterministic DiscoveryJudge verdict (spec 19 §7/§10) — whether the
    student is match-ready across all three tracks."""

    should_handoff: bool
    handoff_target: Literal["recommendation"] | None = None
    reason: str
    completion: dict[str, float]
