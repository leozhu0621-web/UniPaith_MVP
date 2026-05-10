from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MatchResultResponse(BaseModel):
    """Phase A: dual scores (fitness + confidence). The legacy `match_score`
    and `score_breakdown` fields stay in the response for one release so the
    frontend can update without coordination — they get dropped in Phase E.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    program_id: UUID

    # Phase A — dual scores (preferred).
    fitness_score: Decimal
    confidence_score: Decimal
    fitness_breakdown: dict | None = None
    confidence_breakdown: dict | None = None
    rationale_text: str | None = None
    rationale_generated_at: datetime | None = None
    strategy_version_id: UUID | None = None

    # DEPRECATED — drop in Phase E. Now nullable so post-Phase-A writes that
    # only set the dual scores still validate.
    match_score: Decimal | None = None
    score_breakdown: dict | None = None

    match_tier: int | None = None
    reasoning_text: str | None = None
    model_version: str | None = None
    computed_at: datetime
    is_stale: bool

    program_name: str | None = None
    institution_name: str | None = None
    degree_type: str | None = None
    tuition: int | None = None


class ExplainMatchResponse(BaseModel):
    """Returned by POST /me/matches/{program_id}/explain. The rationale_text
    is generated on demand — Phase A synthesizes a deterministic 3-line
    explanation from the breakdown columns; Plan 2 will replace with an LLM
    call. Cached on the row, so subsequent reads via /me/matches return it
    inline."""

    model_config = ConfigDict(from_attributes=True)

    program_id: UUID
    rationale_text: str
    rationale_generated_at: datetime
    is_stub: bool = True


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
    signal_value: int
    created_at: datetime
