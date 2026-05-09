"""Phase A — StudentIdentity Pydantic schemas.

Each list item carries a `confidence` and `source_quote` so provenance is
preserved on every claim. Plan 2 will write these via the discovery extractor;
Phase A accepts them via direct PUT for manual entry / testing.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CoreValue(BaseModel):
    value: str = Field(min_length=1, max_length=200)
    evidence: str = Field(min_length=1, max_length=4000)
    confidence: Decimal | None = Field(None, ge=0, le=1)
    source_quote: str | None = Field(None, max_length=4000)


class WorldviewItem(BaseModel):
    belief: str = Field(min_length=1, max_length=400)
    context: str = Field(min_length=1, max_length=4000)
    confidence: Decimal | None = Field(None, ge=0, le=1)
    source_quote: str | None = Field(None, max_length=4000)


class SelfAwarenessItem(BaseModel):
    insight: str = Field(min_length=1, max_length=400)
    trigger_event: str | None = Field(None, max_length=4000)
    confidence: Decimal | None = Field(None, ge=0, le=1)
    source_quote: str | None = Field(None, max_length=4000)


class UpsertIdentityRequest(BaseModel):
    """Partial update — fields not provided are PRESERVED. Pass `[]`
    explicitly to clear a list."""

    core_values: list[CoreValue] | None = None
    worldview: list[WorldviewItem] | None = None
    self_awareness: list[SelfAwarenessItem] | None = None
    identity_summary: str | None = Field(None, max_length=20_000)
    last_session_id: UUID | None = None


class IdentityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    student_id: UUID
    core_values: list[CoreValue] = Field(default_factory=list)
    worldview: list[WorldviewItem] = Field(default_factory=list)
    self_awareness: list[SelfAwarenessItem] = Field(default_factory=list)
    identity_summary: str | None = None
    last_session_id: UUID | None = None
    updated_at: datetime
