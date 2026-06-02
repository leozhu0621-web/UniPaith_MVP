"""Spec 60 §4 / §12 — public reference-data API.

The world-reference projection (careers, tests, visas, cost, majors, rankings,
accreditation, scholarships) read with provenance on every row, so a student
surface can show "typical for this field · sourced from <domain> · updated N days
ago" and mark a fact provisional until confirmed (§4). Read-only, unauthenticated
— reference knowledge is public-non-personal data by definition (§1).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.services.crawler.reference_service import ReferenceService

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/summary", summary="Live counts per reference domain (with provenance)")
async def reference_summary(db: AsyncSession = Depends(get_db)) -> dict:
    return await ReferenceService(db).summary()


@router.get("/occupations", summary="Careers / occupations (BLS · O*NET)")
async def list_occupations(
    q: str | None = Query(None, description="Title contains"),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await ReferenceService(db).occupations(q=q, limit=limit)


@router.get("/tests", summary="Standardized tests (ETS · College Board · IELTS)")
async def list_tests(
    limit: int = Query(100, le=500), db: AsyncSession = Depends(get_db)
) -> list[dict]:
    return await ReferenceService(db).tests(limit=limit)


@router.get("/visas", summary="Visa & immigration (USCIS · IRCC · UKVI)")
async def list_visas(
    country: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await ReferenceService(db).visas(country=country, limit=limit)


@router.get("/geo-cost", summary="Cost of living & geography")
async def list_geo_cost(
    country: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await ReferenceService(db).geo_cost(country=country, limit=limit)


@router.get("/majors", summary="Majors / curriculum (CIP)")
async def list_majors(
    q: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await ReferenceService(db).majors(q=q, limit=limit)


@router.get("/rankings", summary="Rankings (reported by ranker · year)")
async def list_rankings(
    entity: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await ReferenceService(db).rankings(entity=entity, limit=limit)


@router.get("/accreditation", summary="Accreditation status")
async def list_accreditation(
    entity: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await ReferenceService(db).accreditation(entity=entity, limit=limit)


@router.get("/scholarships", summary="Scholarships (institutional or external)")
async def list_scholarships(
    type: str | None = Query(
        None, description="merit | need | external | institutional | departmental"
    ),
    q: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await ReferenceService(db).scholarships(scholarship_type=type, q=q, limit=limit)
