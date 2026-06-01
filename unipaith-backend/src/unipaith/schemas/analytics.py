"""Spec 28 — Attribution & Funnel Analytics response schemas.

Shared by ``AttributionService`` (which builds them) and ``api/analytics.py``
(which serves them). Mirrors the §8 data shapes; the frontend types in
``frontend/src/types/index.ts`` are the wire mirror of these.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

# --- Filters (echoed back so saved views are self-describing) ----------------


class AppliedFilters(BaseModel):
    program_id: UUID | None = None
    intake_id: UUID | None = None
    segment_id: UUID | None = None
    campaign_id: UUID | None = None
    source_kind: str | None = None
    source_id: UUID | None = None
    time_window: str = "30d"
    range_from: datetime | None = None
    range_to: datetime | None = None


# --- Overview ----------------------------------------------------------------


class KpiMetric(BaseModel):
    """A headline number with a prior-period comparison (§11)."""

    value: float | None = None
    prior: float | None = None
    delta_pct: float | None = None
    # 'count' | 'percent' (0–1 fraction) | 'score' (0–1) — drives FE formatting.
    unit: str = "count"


class NamedCount(BaseModel):
    label: str
    count: int


class PeriodCount(BaseModel):
    period: str
    count: int


class OverviewReport(BaseModel):
    filter: AppliedFilters
    total_applications: KpiMetric
    acceptance_rate: KpiMetric
    avg_match_score: KpiMetric
    yield_rate: KpiMetric
    apps_by_status: dict[str, int]
    apps_by_program: list[NamedCount]
    apps_over_time: list[PeriodCount]
    decisions_breakdown: dict[str, int]
    has_data: bool
    generated_at: datetime


# --- Funnel ------------------------------------------------------------------


class FunnelStageItem(BaseModel):
    stage: str
    label: str
    count: int
    # Conversion from the previous stage (0–1). None for the first stage.
    conversion_from_prev: float | None = None


class SubFunnel(BaseModel):
    key: str  # 'discovery' | 'event' | 'application'
    label: str
    stages: list[FunnelStageItem]


class TopSource(BaseModel):
    source_id: UUID | None = None
    source_kind: str
    label: str
    action_count: int


class DropOffAlert(BaseModel):
    from_stage: str
    to_stage: str
    drop_pct: float
    hint: str


class FunnelReport(BaseModel):
    filter: AppliedFilters
    stages: list[FunnelStageItem]
    sub_funnels: list[SubFunnel]
    top_sources_by_clicks: list[TopSource]
    top_sources_by_apply_started: list[TopSource]
    drop_off_alerts: list[DropOffAlert]
    total_events: int
    has_data: bool
    generated_at: datetime


# --- Attribution (operational outreach metrics §6) ---------------------------


class CampaignMetricRow(BaseModel):
    campaign_id: UUID
    campaign_name: str
    channels: list[str]
    status: str | None = None
    send_volume: int
    delivered: int
    delivery_rate: float | None = None
    opened: int
    # None when open-tracking is not supported for the channel (honest, not 0).
    open_rate: float | None = None
    open_supported: bool = False
    clicked: int
    click_rate: float | None = None
    applications_started: int


class EventMetricRow(BaseModel):
    event_id: UUID
    event_name: str
    rsvps: int
    attended: int
    attendance_rate: float | None = None
    applications_after: int


class TopContentRow(BaseModel):
    source_id: UUID | None = None
    source_kind: str
    title: str
    clicks: int
    apply_started: int


class AttributionReport(BaseModel):
    filter: AppliedFilters
    campaigns: list[CampaignMetricRow]
    events: list[EventMetricRow]
    top_content_by_clicks: list[TopContentRow]
    top_content_by_apply_started: list[TopContentRow]
    has_data: bool
    generated_at: datetime
