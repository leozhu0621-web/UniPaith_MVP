from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.database import get_db
from unipaith.models.institution import Program
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


@router.get("/search/semantic", response_model=list[ProgramSummaryResponse])
async def semantic_program_search(
    q: str = Query(..., min_length=3, description="Natural language search query"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Search programs using semantic similarity (vector search)."""
    from unipaith.ai.embedding_client import get_embedding_client

    client = get_embedding_client()
    query_embedding = await client.embed_text(q)

    vec_str = "[" + ",".join(str(float(v)) for v in query_embedding) + "]"

    query = text(
        "SELECT e.entity_id, 1 - (e.embedding <=> cast(:query_vec as vector)) as similarity "
        "FROM embeddings e "
        "JOIN programs p ON e.entity_id = p.id "
        "WHERE e.entity_type = 'program' "
        "AND p.is_published = true "
        "ORDER BY e.embedding <=> cast(:query_vec as vector) "
        "LIMIT :limit"
    )
    result = await db.execute(
        query, {"query_vec": vec_str, "limit": limit}
    )
    rows = result.fetchall()

    program_ids = [row[0] for row in rows]
    if not program_ids:
        return []

    programs_result = await db.execute(
        select(Program)
        .where(Program.id.in_(program_ids))
        .options(selectinload(Program.institution))
    )
    programs = {p.id: p for p in programs_result.scalars().all()}

    results = []
    for pid, _sim in rows:
        p = programs.get(pid)
        if p:
            results.append(ProgramSummaryResponse(
                id=p.id,
                program_name=p.program_name,
                degree_type=p.degree_type,
                department=p.department,
                tuition=p.tuition,
                application_deadline=p.application_deadline,
                institution_name=p.institution.name if p.institution else "",
                institution_country=p.institution.country if p.institution else "",
            ))
    return results


@router.get("/{program_id}", response_model=ProgramResponse)
async def get_public_program(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    svc = InstitutionService(db)
    return await svc.get_public_program(program_id)
