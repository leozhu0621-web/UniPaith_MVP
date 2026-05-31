from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateApplicationRequest(BaseModel):
    program_id: UUID


class UpdateApplicationRequest(BaseModel):
    status: Literal["draft", "submitted", "under_review", "interview", "decision_made"] | None = (
        None
    )
    completeness_status: Literal["complete", "incomplete", "pending_verification"] | None = None
    missing_items: list[str] | None = None


class PatchApplicationRequest(BaseModel):
    submission_mode: Literal["internal", "external"] | None = None
    intent_picker: (
        Literal["career_fit", "back_up", "dream", "cultural_fit", "family_input", "other"] | None
    ) = None
    intent_rationale: str | None = None
    ready_to_submit: bool | None = None
    checklist_item_completions: dict[str, bool] | None = None


class ChecklistToggleRequest(BaseModel):
    item_id: str
    completed: bool


class GuardrailScanResponse(BaseModel):
    fit_band: Literal["low", "medium", "high"]
    fitness_score: float | None = None
    recommended_action: Literal["proceed", "review", "reconsider"]
    blockers: list[str]
    is_rule_based: bool = Field(True, alias="rule_based")

    model_config = ConfigDict(populate_by_name=True)


class SubmitApplicationRequest(BaseModel):
    pass


class DecisionRequest(BaseModel):
    decision: Literal["admitted", "rejected", "waitlisted", "deferred"]
    decision_notes: str | None = None


class ProgramBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="allow")
    id: UUID
    program_name: str
    degree_type: str
    tuition: int | None = None
    duration_months: int | None = None
    application_deadline: date | None = None
    institution_name: str | None = None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _coerce_orm(cls, data: Any) -> Any:
        if not hasattr(data, "id"):
            return data
        prog = getattr(data, "program", None)
        inst_name = getattr(prog, "institution_name", None) if prog else None
        if prog and inst_name is None:
            inst = getattr(prog, "institution", None)
            inst_name = inst.name if inst is not None else None
        prog_payload = None
        if prog is not None:
            prog_payload = {
                "id": prog.id,
                "program_name": prog.program_name,
                "degree_type": prog.degree_type,
                "tuition": prog.tuition,
                "duration_months": prog.duration_months,
                "application_deadline": prog.application_deadline,
                "institution_name": inst_name,
            }
        return {
            "id": data.id,
            "student_id": data.student_id,
            "program_id": data.program_id,
            "status": data.status,
            "match_score": data.match_score,
            "match_reasoning_text": data.match_reasoning_text,
            "submitted_at": data.submitted_at,
            "decision": data.decision,
            "decision_at": data.decision_at,
            "completeness_status": data.completeness_status,
            "missing_items": data.missing_items,
            "submission_mode": getattr(data, "submission_mode", None) or "internal",
            "readiness_pct": int(getattr(data, "readiness_pct", None) or 0),
            "ready_to_submit": bool(getattr(data, "ready_to_submit", False)),
            "next_action": getattr(data, "next_action", None),
            "intent_picker": getattr(data, "intent_picker", None),
            "intent_rationale": getattr(data, "intent_rationale", None),
            "fit_band": getattr(data, "fit_band", None),
            "guardrail_blockers": getattr(data, "guardrail_blockers", None),
            "created_at": data.created_at,
            "updated_at": data.updated_at,
            "program": prog_payload,
        }

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
    submission_mode: str = "internal"
    readiness_pct: int = 0
    ready_to_submit: bool = False
    next_action: str | None = None
    intent_picker: str | None = None
    intent_rationale: str | None = None
    fit_band: str | None = None
    guardrail_blockers: list[str] | None = None
    created_at: datetime
    updated_at: datetime
    program: ProgramBrief | None = None


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
    plain_language_brief: str | None = None
    created_at: datetime
    updated_at: datetime


class OfferRespondRequest(BaseModel):
    response: Literal["accepted", "declined"]
    decline_reason: str | None = None
