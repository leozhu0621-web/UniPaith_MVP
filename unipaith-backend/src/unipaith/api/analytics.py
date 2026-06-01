"""Spec 28 — Attribution & Funnel Analytics endpoints.

Mounted before ``institutions_router`` so the literal ``/institutions/me/
analytics/*`` paths are unambiguous. All routes are institution-admin scoped and
resolve the caller's institution from the authenticated user.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.schemas.analytics import (
    AppliedFilters,
    AttributionReport,
    FunnelReport,
    OverviewReport,
)
from unipaith.services.attribution_service import AttributionService
from unipaith.services.institution_service import InstitutionService

router = APIRouter(prefix="/institutions/me/analytics", tags=["analytics"])


def _filters(
    program_id: UUID | None = Query(None),
    intake_id: UUID | None = Query(None),
    segment_id: UUID | None = Query(None),
    campaign_id: UUID | None = Query(None),
    source_kind: str | None = Query(None),
    source_id: UUID | None = Query(None),
    time_window: str = Query("30d"),
    range_from: datetime | None = Query(None, alias="from"),
    range_to: datetime | None = Query(None, alias="to"),
) -> AppliedFilters:
    return AppliedFilters(
        program_id=program_id,
        intake_id=intake_id,
        segment_id=segment_id,
        campaign_id=campaign_id,
        source_kind=source_kind,
        source_id=source_id,
        time_window=time_window,
        range_from=range_from,
        range_to=range_to,
    )


async def _institution_id(user: User, db: AsyncSession) -> UUID:
    inst = await InstitutionService(db).get_institution(user.id)
    return inst.id


@router.get("/overview", response_model=OverviewReport)
async def get_overview(
    flt: AppliedFilters = Depends(_filters),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst_id = await _institution_id(user, db)
    return await AttributionService(db).get_overview(inst_id, flt)


@router.get("/funnel", response_model=FunnelReport)
async def get_funnel(
    flt: AppliedFilters = Depends(_filters),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst_id = await _institution_id(user, db)
    return await AttributionService(db).get_funnel(inst_id, flt)


@router.get("/attribution", response_model=AttributionReport)
async def get_attribution(
    flt: AppliedFilters = Depends(_filters),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst_id = await _institution_id(user, db)
    return await AttributionService(db).get_attribution(inst_id, flt)


@router.get("/export")
async def export_csv(
    kind: str = Query("funnel", pattern="^(overview|funnel|attribution)$"),
    format: str = Query("csv"),
    flt: AppliedFilters = Depends(_filters),
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst_id = await _institution_id(user, db)
    csv_str = await AttributionService(db).export_csv(inst_id, kind, flt)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="analytics-{kind}.csv"'},
    )


@router.post("/backfill")
async def backfill(
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
):
    inst_id = await _institution_id(user, db)
    count = await AttributionService(db).backfill_institution(inst_id)
    await db.commit()
    return {"backfilled": count}
