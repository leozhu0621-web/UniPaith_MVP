from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.student import RecommendationRequest
from unipaith.models.user import User
from unipaith.schemas.recommendation import (
    CreateRecommendationRequest,
    RecommendationResponse,
    UpdateRecommendationRequest,
)
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students/me/recommendations", tags=["recommendations"])


async def _get_student_id(user: User, db: AsyncSession) -> UUID:
    svc = StudentService(db)
    profile = await svc._get_student_profile(user.id)
    return profile.id


@router.get("", response_model=list[RecommendationResponse])
async def list_recommendations(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_id = await _get_student_id(user, db)
    result = await db.execute(
        select(RecommendationRequest)
        .where(RecommendationRequest.student_id == student_id)
        .order_by(RecommendationRequest.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_recommendation(
    body: CreateRecommendationRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_id = await _get_student_id(user, db)
    data = body.model_dump()
    if "relationship" in data:
        data["recommender_relationship"] = data.pop("relationship")
    rec = RecommendationRequest(
        student_id=student_id,
        **data,
    )
    db.add(rec)
    await db.flush()
    return rec


@router.get("/{rec_id}", response_model=RecommendationResponse)
async def get_recommendation(
    rec_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_id = await _get_student_id(user, db)
    result = await db.execute(
        select(RecommendationRequest).where(
            RecommendationRequest.id == rec_id,
            RecommendationRequest.student_id == student_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise NotFoundException("Recommendation request not found")
    return rec


@router.put("/{rec_id}", response_model=RecommendationResponse)
async def update_recommendation(
    rec_id: UUID,
    body: UpdateRecommendationRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_id = await _get_student_id(user, db)
    result = await db.execute(
        select(RecommendationRequest).where(
            RecommendationRequest.id == rec_id,
            RecommendationRequest.student_id == student_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise NotFoundException("Recommendation request not found")

    update_data = body.model_dump(exclude_unset=True)
    if "relationship" in update_data:
        update_data["recommender_relationship"] = update_data.pop("relationship")

    # If status changes to 'requested', set requested_at
    if update_data.get("status") == "requested" and rec.status != "requested":
        update_data["requested_at"] = datetime.now(UTC)

    for key, value in update_data.items():
        setattr(rec, key, value)

    await db.flush()
    return rec


@router.delete("/{rec_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recommendation(
    rec_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_id = await _get_student_id(user, db)
    result = await db.execute(
        select(RecommendationRequest).where(
            RecommendationRequest.id == rec_id,
            RecommendationRequest.student_id == student_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise NotFoundException("Recommendation request not found")
    await db.delete(rec)


@router.post("/{rec_id}/send", response_model=RecommendationResponse)
async def send_recommendation_request(
    rec_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Mark a recommendation as 'requested' (in production, this would send an email)."""
    student_id = await _get_student_id(user, db)
    result = await db.execute(
        select(RecommendationRequest).where(
            RecommendationRequest.id == rec_id,
            RecommendationRequest.student_id == student_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise NotFoundException("Recommendation request not found")

    rec.status = "requested"
    rec.requested_at = datetime.now(UTC)
    await db.flush()
    return rec
