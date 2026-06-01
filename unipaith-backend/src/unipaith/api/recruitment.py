"""Spec 40 — Recruitment CRM (Pre-Applicant) API.

Mounted at /api/v1/institutions/me/recruitment. The institution top-of-funnel:
prospects (with import / convert / push-to-segment), the travel calendar
(trips + visits), the HS / college-fair directory (with lead capture), and
territory management (dashboards + AI optimization). All endpoints require the
institution_admin role; everything is scoped to the caller's institution.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.prospect_prioritizer import priority_band
from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.recruitment import Prospect, RecruitmentTrip
from unipaith.models.user import User
from unipaith.schemas.recruitment import (
    ConvertProspectRequest,
    CreateFairRequest,
    CreateProspectRequest,
    CreateTerritoryRequest,
    CreateTripRequest,
    CreateTripVisitRequest,
    FairCaptureRequest,
    FairCaptureResult,
    FairResponse,
    ProspectImportRequest,
    ProspectImportResult,
    ProspectListResponse,
    ProspectResponse,
    ProspectToSegmentRequest,
    ProspectToSegmentResult,
    RecruitmentSummaryResponse,
    TerritoryDashboardResponse,
    TerritoryOptimizeResponse,
    TerritoryResponse,
    TripResponse,
    UpdateFairRequest,
    UpdateProspectRequest,
    UpdateTerritoryRequest,
    UpdateTripRequest,
    UpdateTripVisitRequest,
)
from unipaith.services.recruitment_service import RecruitmentService

router = APIRouter(prefix="/institutions/me/recruitment", tags=["recruitment"])


def _svc(db: AsyncSession) -> RecruitmentService:
    return RecruitmentService(db)


def _prospect_out(p: Prospect, score: dict | None = None) -> ProspectResponse:
    resp = ProspectResponse.model_validate(p)
    if score:
        # Read-time ProspectPrioritizer score overlaid onto the response.
        resp.apply_likelihood = score["apply_likelihood"]
        resp.priority_reason = score["reason"]
        resp.priority_band = score["band"]
    elif p.apply_likelihood is not None:
        resp.priority_band = priority_band(p.apply_likelihood)
    return resp


def _trip_out(trip: RecruitmentTrip, over_budget: bool, conflict: bool) -> TripResponse:
    resp = TripResponse.model_validate(trip)
    resp.over_budget = over_budget
    resp.conflict = conflict
    return resp


# ── summary ───────────────────────────────────────────────────────────────────


@router.get("/summary", response_model=RecruitmentSummaryResponse)
async def get_summary(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.summary(inst.id)


# ── prospects ───────────────────────────────────────────────────────────────


@router.get("/prospects", response_model=ProspectListResponse)
async def list_prospects(
    stage: str | None = Query(None),
    source: str | None = Query(None),
    territory_id: UUID | None = Query(None),
    owner_user_id: UUID | None = Query(None),
    search: str | None = Query(None),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    rows, score_map, prioritized, stage_counts = await svc.list_prospects(
        inst.id,
        stage=stage,
        source=source,
        territory_id=territory_id,
        owner_user_id=owner_user_id,
        search=search,
    )
    return ProspectListResponse(
        items=[_prospect_out(p, score_map.get(str(p.id))) for p in rows],
        total=len(rows),
        prioritized=prioritized,
        stage_counts=stage_counts,
    )


@router.post("/prospects", response_model=ProspectResponse, status_code=201)
async def create_prospect(
    data: CreateProspectRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return _prospect_out(await svc.create_prospect(inst.id, data))


@router.post("/prospects/import", response_model=ProspectImportResult)
async def import_prospects(
    data: ProspectImportRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.import_prospects(inst.id, data)


@router.post("/prospects/to-segment", response_model=ProspectToSegmentResult)
async def prospects_to_segment(
    data: ProspectToSegmentRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.prospects_to_segment(inst.id, user.id, data)


@router.get("/prospects/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(
    prospect_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return _prospect_out(await svc.get_prospect(inst.id, prospect_id))


@router.patch("/prospects/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: UUID,
    data: UpdateProspectRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return _prospect_out(await svc.update_prospect(inst.id, prospect_id, data))


@router.post("/prospects/{prospect_id}/convert", response_model=ProspectResponse)
async def convert_prospect(
    prospect_id: UUID,
    data: ConvertProspectRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return _prospect_out(await svc.convert_prospect(inst.id, prospect_id, data))


# ── travel calendar ───────────────────────────────────────────────────────────


@router.get("/trips", response_model=list[TripResponse])
async def list_trips(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    trips = await svc.list_trips(inst.id)
    out = []
    for t in trips:
        ob, cf = svc.trip_flags(t, trips)
        out.append(_trip_out(t, ob, cf))
    return out


@router.post("/trips", response_model=TripResponse, status_code=201)
async def create_trip(
    data: CreateTripRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    trip = await svc.create_trip(inst.id, data)
    all_trips = await svc.list_trips(inst.id)
    ob, cf = svc.trip_flags(trip, all_trips)
    return _trip_out(trip, ob, cf)


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    trip = await svc.get_trip(inst.id, trip_id)
    all_trips = await svc.list_trips(inst.id)
    ob, cf = svc.trip_flags(trip, all_trips)
    return _trip_out(trip, ob, cf)


@router.patch("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: UUID,
    data: UpdateTripRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    trip = await svc.update_trip(inst.id, trip_id, data)
    all_trips = await svc.list_trips(inst.id)
    ob, cf = svc.trip_flags(trip, all_trips)
    return _trip_out(trip, ob, cf)


@router.post("/trips/{trip_id}/visits", response_model=TripResponse, status_code=201)
async def add_visit(
    trip_id: UUID,
    data: CreateTripVisitRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    trip = await svc.add_visit(inst.id, trip_id, data)
    all_trips = await svc.list_trips(inst.id)
    ob, cf = svc.trip_flags(trip, all_trips)
    return _trip_out(trip, ob, cf)


@router.patch("/trips/{trip_id}/visits/{visit_id}", response_model=TripResponse)
async def update_visit(
    trip_id: UUID,
    visit_id: UUID,
    data: UpdateTripVisitRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    trip = await svc.update_visit(inst.id, trip_id, visit_id, data)
    all_trips = await svc.list_trips(inst.id)
    ob, cf = svc.trip_flags(trip, all_trips)
    return _trip_out(trip, ob, cf)


# ── fairs ─────────────────────────────────────────────────────────────────────


@router.get("/fairs", response_model=list[FairResponse])
async def list_fairs(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return [FairResponse.model_validate(f) for f in await svc.list_fairs(inst.id)]


@router.post("/fairs", response_model=FairResponse, status_code=201)
async def create_fair(
    data: CreateFairRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return FairResponse.model_validate(await svc.create_fair(inst.id, data))


@router.patch("/fairs/{fair_id}", response_model=FairResponse)
async def update_fair(
    fair_id: UUID,
    data: UpdateFairRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return FairResponse.model_validate(await svc.update_fair(inst.id, fair_id, data))


@router.post("/fairs/{fair_id}/capture", response_model=FairCaptureResult)
async def capture_leads(
    fair_id: UUID,
    data: FairCaptureRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.capture_leads(inst.id, fair_id, data)


# ── territories ───────────────────────────────────────────────────────────────


@router.get("/territories/dashboard", response_model=TerritoryDashboardResponse)
async def territory_dashboard(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.territory_dashboard(inst.id)


@router.get("/territories", response_model=list[TerritoryResponse])
async def list_territories(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.list_territories(inst.id)


@router.post("/territories", response_model=TerritoryResponse, status_code=201)
async def create_territory(
    data: CreateTerritoryRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.create_territory(inst.id, data)


@router.patch("/territories/{territory_id}", response_model=TerritoryResponse)
async def update_territory(
    territory_id: UUID,
    data: UpdateTerritoryRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.update_territory(inst.id, territory_id, data)


@router.post("/territories/{territory_id}/optimize", response_model=TerritoryOptimizeResponse)
async def optimize_territory(
    territory_id: UUID,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    svc = _svc(db)
    inst = await svc.get_institution(user.id)
    return await svc.optimize_territory(inst.id, territory_id)
