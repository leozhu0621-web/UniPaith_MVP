from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateRecommendationRequest(BaseModel):
    recommender_name: str
    recommender_email: str | None = None
    recommender_title: str | None = None
    recommender_institution: str | None = None
    relationship: str | None = None
    due_date: date | None = None
    notes: str | None = None
    target_program_id: UUID | None = None


class UpdateRecommendationRequest(BaseModel):
    recommender_name: str | None = None
    recommender_email: str | None = None
    recommender_title: str | None = None
    recommender_institution: str | None = None
    relationship: str | None = None
    status: str | None = None
    due_date: date | None = None
    notes: str | None = None
    target_program_id: UUID | None = None


class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    student_id: UUID
    recommender_name: str
    recommender_email: str | None = None
    recommender_title: str | None = None
    recommender_institution: str | None = None
    relationship: str | None = Field(None, validation_alias="recommender_relationship")
    status: str
    requested_at: datetime | None = None
    due_date: date | None = None
    notes: str | None = None
    target_program_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
