from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MySpaceOwner = Literal["student", "recommender", "institution", "system"]
MySpaceUrgency = Literal["focus_now", "priority_window", "gentle_attention", "neutral"]
MySpaceReadinessStatus = Literal["ready", "needs_attention", "blocked", "unknown"]


class MySpaceProvenance(BaseModel):
    source: str
    label: str
    href: str | None = None
    confidence: int | None = Field(default=None, ge=0, le=100)
    updated_at: datetime | None = None


class MySpaceTask(BaseModel):
    key: str
    title: str
    description: str
    owner: MySpaceOwner
    urgency: MySpaceUrgency
    category: str
    cta_label: str
    cta_route: str
    blocker: str | None = None
    missing_field: str | None = None
    due_at: datetime | None = None
    provenance: list[MySpaceProvenance] = Field(default_factory=list)
    dismissed: bool = False
    snoozed_until: datetime | None = None
    active: bool = True
    dismissible: bool = True


class MySpaceReadiness(BaseModel):
    key: str
    label: str
    status: MySpaceReadinessStatus
    pct: int | None = Field(default=None, ge=0, le=100)
    detail: str
    route: str
    provenance: list[MySpaceProvenance] = Field(default_factory=list)


class MySpaceMetric(BaseModel):
    key: str
    label: str
    value: int | str
    route: str
    status: MySpaceReadinessStatus | None = None


class MySpaceModuleItem(BaseModel):
    key: str
    title: str
    description: str
    route: str
    owner: MySpaceOwner | None = None
    urgency: MySpaceUrgency = "neutral"
    status: str | None = None
    due_at: datetime | None = None
    provenance: list[MySpaceProvenance] = Field(default_factory=list)


class MySpaceStudent(BaseModel):
    id: UUID
    first_name: str | None = None
    display_name: str | None = None


class MySpaceOverview(BaseModel):
    generated_at: datetime
    student: MySpaceStudent
    readiness: list[MySpaceReadiness]
    tasks: list[MySpaceTask]
    pipeline: list[MySpaceMetric]
    evidence_gaps: list[MySpaceTask]
    deadlines: list[MySpaceModuleItem]
    waiting_on: list[MySpaceModuleItem]
    application_portfolio: list[MySpaceModuleItem]
    messages: list[MySpaceModuleItem]
    feedback: list[MySpaceModuleItem]
    strategy: MySpaceModuleItem | None = None
    prep_readiness: list[MySpaceReadiness]
    offers: list[MySpaceModuleItem]
    saved_targets: list[MySpaceModuleItem]
    import_status: MySpaceModuleItem
    recent_changes: list[MySpaceModuleItem]
    access_issues: list[MySpaceProvenance] = Field(default_factory=list)


class MySpaceTaskPatch(BaseModel):
    dismissed: bool | None = None
    snoozed_until: datetime | None = None


class MySpaceTaskStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_key: str
    dismissed: bool
    snoozed_until: datetime | None = None
