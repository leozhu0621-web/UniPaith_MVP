"""Spec 07 (Product Context §4) — billing / subscription Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SubscriptionStatus = Literal["trialing", "active", "canceled", "expired"]
SubscriptionPlan = Literal["free", "pro"]


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: SubscriptionStatus
    plan: SubscriptionPlan
    effective_plan: SubscriptionPlan
    ad_free: bool
    is_trialing: bool
    is_active: bool
    has_pro_access: bool
    trial_ends_at: datetime | None = None
    current_period_end: datetime | None = None
    days_left_in_trial: int | None = None
    card_brand: str | None = None
    card_last4: str | None = None
    entitlements: list[str]


class SubscribeRequest(BaseModel):
    """Mock card-on-file. NEVER send a real PAN — brand + last4 only."""

    card_brand: str = Field(default="visa", max_length=30)
    card_last4: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")
    ad_free: bool = False


class AdFreeRequest(BaseModel):
    enabled: bool


class PlanFeature(BaseModel):
    label: str
    free: bool
    pro: bool


class StudentPlanCatalog(BaseModel):
    id: str
    name: str
    tagline: str
    price_monthly: int
    currency: str
    trial_days: int
    ad_free_addon_monthly: int


class InstitutionPlanCatalog(BaseModel):
    id: str
    name: str
    tagline: str
    price_per_applicant: int
    currency: str
    billing_model: str


class PlanCatalogResponse(BaseModel):
    student: StudentPlanCatalog
    institution: InstitutionPlanCatalog
    features: list[PlanFeature]
