"""Phase A — StudentGoal Pydantic schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

GoalCategory = Literal["academic", "social", "personal"]
GoalStatus = Literal["active", "met", "revised", "dropped"]
GoalSource = Literal["discovery", "manual"]


class CreateGoalRequest(BaseModel):
    category: GoalCategory
    specific: str = Field(min_length=1, max_length=2000)
    measurable: str | None = Field(None, max_length=2000)
    achievable_notes: str | None = Field(None, max_length=2000)
    relevant_notes: str | None = Field(None, max_length=2000)
    time_bound: date | None = None
    status: GoalStatus = "active"
    source: GoalSource = "manual"
    source_session_id: UUID | None = None
    confidence: Decimal | None = Field(None, ge=0, le=1)


class UpdateGoalRequest(BaseModel):
    """All fields optional — partial updates. Source/provenance is immutable
    once set; you can't flip a manual goal to discovery-sourced."""

    category: GoalCategory | None = None
    specific: str | None = Field(None, min_length=1, max_length=2000)
    measurable: str | None = Field(None, max_length=2000)
    achievable_notes: str | None = Field(None, max_length=2000)
    relevant_notes: str | None = Field(None, max_length=2000)
    time_bound: date | None = None
    status: GoalStatus | None = None
    confidence: Decimal | None = Field(None, ge=0, le=1)


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    category: GoalCategory
    specific: str
    measurable: str | None = None
    achievable_notes: str | None = None
    relevant_notes: str | None = None
    time_bound: date | None = None
    status: GoalStatus
    source: GoalSource
    source_session_id: UUID | None = None
    confidence: Decimal | None = None
    created_at: datetime
    updated_at: datetime
