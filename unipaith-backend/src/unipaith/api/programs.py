from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.schemas.institution import (
    PaginatedResponse,
    ProgramResponse,
    ProgramSummaryResponse,
)
from unipaith.services.institution_service import InstitutionService

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=PaginatedResponse[ProgramSummaryResponse])
async def search_programs(
    q: str | None = Query(None),
    country: str | None = Query(None),
    degree_type: str | None = Query(None),
    min_tuition: int | None = Query(None),
    max_tuition: int | None = Query(None),
    sort_by: str | None = Query(
        None, description="Sort: relevance, tuition_asc, tuition_desc, deadline"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    svc = InstitutionService(db)
    return await svc.search_programs(
        query=q,
        country=country,
        degree_type=degree_type,
        min_tuition=min_tuition,
        max_tuition=max_tuition,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.get("/search/semantic", response_model=list[ProgramSummaryResponse])
async def semantic_program_search(
    q: str = Query(..., min_length=3, description="Natural language search query"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Search programs using semantic similarity (vector search)."""
    svc = InstitutionService(db)
    return await svc.semantic_search_programs(query=q, limit=limit)


@router.get("/{program_id}", response_model=ProgramResponse)
async def get_public_program(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    svc = InstitutionService(db)
    return await svc.get_public_program(program_id)
