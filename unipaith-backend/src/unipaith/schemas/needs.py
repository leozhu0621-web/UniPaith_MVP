"""Phase A — StudentNeed Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MaslowLevel = Literal[
    "physiological",
    "safety",
    "social",
    "self_esteem",
    "self_actualization",
]
NeedSeverity = Literal["must_have", "strong_preference", "nice_to_have"]
NeedSource = Literal["discovery", "manual", "inferred"]


class CreateNeedRequest(BaseModel):
    maslow_level: MaslowLevel
    need_type: str = Field(min_length=1, max_length=120)
    signal: str = Field(min_length=1, max_length=4000)
    severity: NeedSeverity
    source: NeedSource = "manual"
    source_session_id: UUID | None = None
    source_quote: str | None = Field(None, max_length=4000)
    confidence: Decimal | None = Field(None, ge=0, le=1)


class UpdateNeedRequest(BaseModel):
    maslow_level: MaslowLevel | None = None
    need_type: str | None = Field(None, min_length=1, max_length=120)
    signal: str | None = Field(None, min_length=1, max_length=4000)
    severity: NeedSeverity | None = None
    source_quote: str | None = Field(None, max_length=4000)
    confidence: Decimal | None = Field(None, ge=0, le=1)


class NeedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    maslow_level: MaslowLevel
    need_type: str
    signal: str
    severity: NeedSeverity
    source: NeedSource
    source_session_id: UUID | None = None
    source_quote: str | None = None
    confidence: Decimal | None = None
    created_at: datetime
    updated_at: datetime
