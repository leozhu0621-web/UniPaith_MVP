from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmbeddedProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    institution_id: UUID
    program_name: str
    degree_type: str | None = None
    department: str | None = None
    duration_months: int | None = None
    tuition: int | None = None
    acceptance_rate: Decimal | None = None
    delivery_format: str | None = None
    campus_setting: str | None = None
    application_deadline: date | None = None


class CreateApplicationRequest(BaseModel):
    program_id: UUID


class UpdateApplicationRequest(BaseModel):
    status: Literal["draft", "submitted", "under_review", "interview", "decision_made"] | None = (
        None
    )
    completeness_status: Literal["complete", "incomplete", "pending_verification"] | None = None
    missing_items: list[str] | None = None


class SubmitApplicationRequest(BaseModel):
    pass


class DecisionRequest(BaseModel):
    decision: Literal["admitted", "rejected", "waitlisted", "deferred"]
    decision_notes: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    student_id: UUID
    program_id: UUID
    status: str | None
    match_score: Decimal | None
    match_reasoning_text: str | None
    submitted_at: datetime | None
    decision: str | None
    decision_at: datetime | None
    completeness_status: str | None
    missing_items: dict | None
    created_at: datetime
    updated_at: datetime
    program: EmbeddedProgramResponse | None = None


class ApplicationDetailResponse(ApplicationResponse):
    decision_notes: str | None = None
    decision_by: UUID | None = None


class CreateOfferRequest(BaseModel):
    offer_type: Literal["full_admission", "conditional", "waitlist_offer"]
    tuition_amount: int | None = None
    scholarship_amount: int = 0
    assistantship_details: dict | None = None
    financial_package_total: int | None = None
    conditions: dict | None = None
    response_deadline: date | None = None


class OfferLetterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    application_id: UUID
    offer_type: str | None
    tuition_amount: int | None
    scholarship_amount: int
    financial_package_total: int | None
    conditions: dict | None
    response_deadline: date | None
    status: str | None
    student_response: str | None
    response_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OfferRespondRequest(BaseModel):
    response: Literal["accepted", "declined"]
    decline_reason: str | None = None
