from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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


class ProgramBrief(BaseModel):
    """Minimal program info embedded in application responses."""

    model_config = ConfigDict(from_attributes=True)
    id: UUID
    program_name: str
    degree_type: str
    tuition: int | None = None
    duration_months: int | None = None
    application_deadline: date | None = None


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
    intent_reason: str | None = None
    intent_rationale: str | None = None
    created_at: datetime
    updated_at: datetime
    program: ProgramBrief | None = None


class ApplicationDetailResponse(ApplicationResponse):
    decision_notes: str | None = None
    decision_by: UUID | None = None


# --- Guardrails (gap-audit G-S4) -----------------------------------------

GuardrailLevel = Literal["green", "amber", "red"]


class GuardrailScanRequest(BaseModel):
    """Optional client-side context for a guardrail scan.

    The scan is server-derived from the application + match record; clients
    can additionally pass the latest picker selection so it's persisted in
    the same request and reflected in the scan response.
    """

    intent_reason: str | None = None
    intent_rationale: str | None = None


class GuardrailScanResponse(BaseModel):
    """Result of a guardrail scan — see Spec/17 §guardrails."""

    level: GuardrailLevel
    fit_score_band: Literal["strong", "good", "stretch", "reach"]
    recommended_action: str
    blockers: list[str]
    message: str
    points: list[str]


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
