"""Spec 43 — Major-Specific Field Catalog request/response schemas.

Shared by ``MajorSpecificService`` (which builds them) and
``api/major_specific.py`` (which serves them). The frontend types in
``frontend/src/types/majorSpecific.ts`` are the wire mirror of these.

The per-track ``signals`` is a free-form ``{field_key: value}`` dict validated
against the catalog schema (``services.major_track_catalog``) at the service
layer — values out of range / off-vocabulary are dropped, never 422'd, so the
form is forgiving (Spec 43 §1 / §17).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Catalog (the 15-track field schema, for the FE form renderer) ─────────────
class CatalogResponse(BaseModel):
    tracks: list[dict]
    # track_key(s) inferred from the student's stated major (Spec 43 §1).
    suggested_tracks: list[str] = Field(default_factory=list)


# ── Per-track signals ─────────────────────────────────────────────────────────
class TrackSignalsUpsert(BaseModel):
    # {field_key: value}. Validated/coerced against the track schema in-service.
    signals: dict = Field(default_factory=dict)


class TrackSignalsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    track_key: str
    label: str
    signals: dict
    # SignalRecord metadata (Spec 42 §5).
    source: str
    confidence: int
    record_version: int
    updated_at: datetime | None = None
    # §4.18 coach overlay — populated only when ai_major_specific_v2_enabled.
    coach: dict | None = None


class TracksResponse(BaseModel):
    active_tracks: list[str]
    suggested_tracks: list[str] = Field(default_factory=list)
    tracks: list[TrackSignalsOut]


# ── Summary (§4.18 overlay) ──────────────────────────────────────────────────
class MajorSpecificSummary(BaseModel):
    active_track_count: int
    inference_enabled: bool
    primary_track: str | None = None
    major_track_fit_score_per_target_track: dict | None = None
    tracks: list[dict] | None = None
