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
        page=page,
        page_size=page_size,
    )


@router.get("/{program_id}", response_model=ProgramResponse)
async def get_public_program(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    svc = InstitutionService(db)
    return await svc.get_public_program(program_id)
