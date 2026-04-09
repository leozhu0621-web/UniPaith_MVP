from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class BatchAssignRequest(BaseModel):
    application_ids: list[UUID] = Field(min_length=1)
    reviewer_id: UUID | None = None


class BatchRequestItemsRequest(BaseModel):
    application_ids: list[UUID] = Field(min_length=1)
    items: list[str] = Field(min_length=1)


class BatchInviteRequest(BaseModel):
    application_ids: list[UUID] = Field(min_length=1)
    interviewer_id: UUID
    interview_type: str = "standard"
    proposed_times: list[str] = Field(min_length=1)
    duration_minutes: int = 30
    location_or_link: str | None = None


class BatchStatusRequest(BaseModel):
    application_ids: list[UUID] = Field(min_length=1)
    status: str


class BatchDecisionRequest(BaseModel):
    application_ids: list[UUID] = Field(min_length=1)
    decision: Literal["admitted", "rejected", "waitlisted", "deferred"]
    decision_notes: str | None = None


class BatchOperationResult(BaseModel):
    success_count: int
    failed_ids: list[UUID]
    errors: list[str]
