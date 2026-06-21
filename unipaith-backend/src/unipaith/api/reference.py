"""Public read API over the Spec 60 reference layer.

``GET /reference/institutions`` (search/filter) and ``/{unitid}`` (detail) expose the
College Scorecard institution directory (``ref_institutions``). Unauthenticated, like
``/health`` and ``/ai/agents``: non-personal, source-cited public reference data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.services.reference_service import ReferenceService

router = APIRouter(prefix="/reference", tags=["reference"])


class InstitutionCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    unitid: int
    name: str
    city: str | None = None
    state: str | None = None
    control: str | None = None
    size: int | None = None
    admit_rate: float | None = None
    earnings_10yr_median: int | None = None


class InstitutionDetail(InstitutionCard):
    opeid6: str | None = None
    zip: str | None = None
    accreditor: str | None = None
    url: str | None = None
    pred_degree: int | None = None
    high_degree: int | None = None
    sat_avg: int | None = None
    act_mid: int | None = None
    cost_attendance: int | None = None
    tuition_in: int | None = None
    tuition_out: int | None = None
    pct_pell: float | None = None
    completion_rate: float | None = None
    retention: float | None = None
    median_debt: int | None = None
    carnegie_basic: int | None = None
    program_pct: dict | None = None
    source: str | None = None
    source_vintage: str | None = None


class InstitutionList(BaseModel):
    items: list[InstitutionCard]


@router.get(
    "/institutions",
    response_model=InstitutionList,
    summary="Search the public College Scorecard institution directory",
)
async def list_institutions(
    q: str | None = None,
    state: str | None = None,
    control: str | None = None,
    min_size: int | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> InstitutionList:
    rows = await ReferenceService(db).search_institutions(
        q=q, state=state, control=control, min_size=min_size, limit=limit, offset=offset
    )
    return InstitutionList(items=[InstitutionCard.model_validate(r) for r in rows])


@router.get(
    "/institutions/{unitid}",
    response_model=InstitutionDetail,
    summary="Full reference record for one institution",
)
async def get_institution(unitid: int, db: AsyncSession = Depends(get_db)) -> InstitutionDetail:
    row = await ReferenceService(db).get_institution(unitid)
    if row is None:
        raise HTTPException(status_code=404, detail="Institution not found")
    return InstitutionDetail.model_validate(row)


class Major(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cip_code: str
    title: str
    description: str | None = None
    related_occupations: list | None = None


class MajorList(BaseModel):
    items: list[Major]


@router.get(
    "/majors",
    response_model=MajorList,
    summary="Search the NCES CIP major taxonomy",
)
async def list_majors(
    q: str | None = None,
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> MajorList:
    rows = await ReferenceService(db).search_majors(q=q, limit=limit, offset=offset)
    return MajorList(items=[Major.model_validate(r) for r in rows])


@router.get(
    "/majors/{cip_code}",
    response_model=Major,
    summary="One major (field of study) by CIP code",
)
async def get_major(cip_code: str, db: AsyncSession = Depends(get_db)) -> Major:
    row = await ReferenceService(db).get_major(cip_code)
    if row is None:
        raise HTTPException(status_code=404, detail="Major not found")
    return Major.model_validate(row)
