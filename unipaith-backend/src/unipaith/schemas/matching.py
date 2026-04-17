from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MatchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    program_id: UUID
    match_score: Decimal | None
    match_tier: int | None
    score_breakdown: dict | None
    reasoning_text: str | None
    model_version: str | None
    computed_at: datetime
    is_stale: bool

    program_name: str | None = None
    institution_name: str | None = None
    degree_type: str | None = None
    tuition: int | None = None


class MatchListResponse(BaseModel):
    matches: list[MatchResultResponse]
    total: int
    tier_counts: dict
    computed_at: datetime | None
    is_fresh: bool


class EngagementSignalRequest(BaseModel):
    program_id: UUID
    signal_type: str
    signal_value: int = 1


class EngagementSignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    program_id: UUID
    signal_type: str
    signal_value: int | None
    created_at: datetime
