from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.models.institution import StudentProgramReview
from unipaith.schemas.institution import (
    NLPSearchRequest,
    NLPSearchResponse,
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
    institution_id: UUID | None = Query(None),
    min_tuition: int | None = Query(None),
    max_tuition: int | None = Query(None),
    delivery_format: str | None = Query(None),
    campus_setting: str | None = Query(None),
    max_duration_months: int | None = Query(None),
    city: str | None = Query(None),
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
        institution_id=institution_id,
        min_tuition=min_tuition,
        max_tuition=max_tuition,
        delivery_format=delivery_format,
        campus_setting=campus_setting,
        max_duration_months=max_duration_months,
        city=city,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.post("/search/nlp", response_model=NLPSearchResponse)
async def nlp_search_programs(
    body: NLPSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Search programs using natural language. The LLM extracts structured
    filters from the query and returns matching programs."""
    svc = InstitutionService(db)
    return await svc.nlp_search_programs(body.query)


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


# --- Student Reviews ---


class ReviewResponse(BaseModel):
    id: UUID
    program_id: UUID
    rating_teaching: int | None = None
    rating_workload: int | None = None
    rating_career_support: int | None = None
    rating_roi: int | None = None
    rating_overall: int | None = None
    review_text: str | None = None
    who_thrives_here: str | None = None
    reviewer_context: dict | None = None
    is_verified: bool = False
    created_at: str


class ReviewSummaryResponse(BaseModel):
    total_reviews: int
    avg_teaching: float | None = None
    avg_workload: float | None = None
    avg_career_support: float | None = None
    avg_roi: float | None = None
    avg_overall: float | None = None
    reviews: list[ReviewResponse]


@router.get(
    "/{program_id}/reviews",
    response_model=ReviewSummaryResponse,
)
async def get_program_reviews(
    program_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get published reviews for a program with averages."""
    stmt = (
        select(StudentProgramReview)
        .where(
            StudentProgramReview.program_id == program_id,
            StudentProgramReview.is_published.is_(True),
        )
        .order_by(StudentProgramReview.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    reviews = list(result.scalars().all())

    avg_stmt = (
        select(
            func.count().label("cnt"),
            func.avg(StudentProgramReview.rating_teaching),
            func.avg(StudentProgramReview.rating_workload),
            func.avg(StudentProgramReview.rating_career_support),
            func.avg(StudentProgramReview.rating_roi),
            func.avg(StudentProgramReview.rating_overall),
        )
        .where(
            StudentProgramReview.program_id == program_id,
            StudentProgramReview.is_published.is_(True),
        )
    )
    agg = (await db.execute(avg_stmt)).one()

    return ReviewSummaryResponse(
        total_reviews=agg[0] or 0,
        avg_teaching=round(float(agg[1]), 1) if agg[1] else None,
        avg_workload=round(float(agg[2]), 1) if agg[2] else None,
        avg_career_support=(
            round(float(agg[3]), 1) if agg[3] else None
        ),
        avg_roi=round(float(agg[4]), 1) if agg[4] else None,
        avg_overall=round(float(agg[5]), 1) if agg[5] else None,
        reviews=[
            ReviewResponse(
                id=r.id,
                program_id=r.program_id,
                rating_teaching=r.rating_teaching,
                rating_workload=r.rating_workload,
                rating_career_support=r.rating_career_support,
                rating_roi=r.rating_roi,
                rating_overall=r.rating_overall,
                review_text=r.review_text,
                who_thrives_here=r.who_thrives_here,
                reviewer_context=r.reviewer_context,
                is_verified=r.is_verified,
                created_at=r.created_at.isoformat(),
            )
            for r in reviews
        ],
    )
