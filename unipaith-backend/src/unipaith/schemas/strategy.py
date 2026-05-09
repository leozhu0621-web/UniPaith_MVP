"""Phase A — StudentStrategy Pydantic schemas.

Strategy is the broad-strategy artifact that bridges Discovery and Match. The
academic/financial/geographic_path fields are typed list-of-dicts to keep the
contract clear; downstream UI (Phase C) renders sectioned cards.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

StrategyStatus = Literal["draft", "active", "archived"]


class AcademicPathStep(BaseModel):
    step: str = Field(min_length=1, max_length=400)
    options: list[str] = Field(default_factory=list)
    rationale: str = Field(min_length=1, max_length=2000)


class FinancialPathItem(BaseModel):
    aid_type: str = Field(min_length=1, max_length=200)
    eligibility: str = Field(min_length=1, max_length=2000)
    estimated_value: str | None = Field(None, max_length=200)


class GeographicPathItem(BaseModel):
    region: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=2000)
    constraints: list[str] = Field(default_factory=list)


class UpdateStrategyRequest(BaseModel):
    """Manual edits. PATCH archives the original and creates a new draft —
    the new row carries these fields merged onto the original. Status is not
    in this schema: a new edit always lands as 'draft'; use POST /activate to
    promote it."""

    career_target: str | None = Field(None, max_length=500)
    target_degree: str | None = Field(None, max_length=120)
    academic_path: list[AcademicPathStep] | None = None
    financial_path: list[FinancialPathItem] | None = None
    geographic_path: list[GeographicPathItem] | None = None
    narrative: str | None = Field(None, max_length=20_000)


class StrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_id: UUID
    version: int
    status: StrategyStatus
    career_target: str | None = None
    target_degree: str | None = None
    academic_path: list[AcademicPathStep] = Field(default_factory=list)
    financial_path: list[FinancialPathItem] = Field(default_factory=list)
    geographic_path: list[GeographicPathItem] = Field(default_factory=list)
    narrative: str | None = None
    generated_at: datetime
    generated_from_session_ids: list[UUID] = Field(default_factory=list)
    is_stub: bool
    created_at: datetime
    updated_at: datetime
