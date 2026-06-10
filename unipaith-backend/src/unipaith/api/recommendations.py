from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.institution import Institution, Program
from unipaith.models.student import RecommendationRequest
from unipaith.models.user import User
from unipaith.schemas.recommendation import (
    CreateRecommendationRequest,
    RecommendationResponse,
    UpdateRecommendationRequest,
)
from unipaith.services.email_service import EmailSendError, send_email
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
    """Email the recommender (SES) and mark the request 'requested'.

    When ``email_send_enabled`` is on and the request has a recommender email,
    the request email is sent BEFORE the status flips — a failed send leaves
    the request untouched and returns 502. When sending is disabled or there is
    no recommender email, only the status flips and ``email_sent`` is false.
    """
    svc = StudentService(db)
    profile = await svc._get_student_profile(user.id)
    result = await db.execute(
        select(RecommendationRequest).where(
            RecommendationRequest.id == rec_id,
            RecommendationRequest.student_id == profile.id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        raise NotFoundException("Recommendation request not found")

    email_sent = False
    if settings.email_send_enabled and rec.recommender_email:
        student_name = (
            " ".join(part for part in [profile.first_name, profile.last_name] if part)
            or "A UniPaith student"
        )
        program_context = ""
        if rec.target_program_id:
            row = (
                await db.execute(
                    select(Program.program_name, Institution.name)
                    .join(Institution, Program.institution_id == Institution.id)
                    .where(Program.id == rec.target_program_id)
                )
            ).first()
            if row:
                program_context = (
                    f" in support of their application to {row[0]} at {row[1]}"
                )
        due_line = (
            f"\nThe letter is needed by {rec.due_date.isoformat()}."
            if rec.due_date
            else ""
        )
        body_text = (
            f"Hello {rec.recommender_name},\n\n"
            f"{student_name} is requesting a letter of recommendation from you"
            f"{program_context}.{due_line}\n\n"
            f"You can reach {student_name} directly at {user.email} with any "
            "questions or to share the letter.\n\n"
            "Sent via UniPaith on the student's behalf."
        )
        try:
            await send_email(
                to_address=rec.recommender_email,
                subject=f"Recommendation request from {student_name}",
                body_text=body_text,
            )
        except EmailSendError as exc:
            # The recommender was never contacted — do not flip the status.
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "The recommendation request email could not be delivered. "
                    "The request was not marked as sent — try again."
                ),
            ) from exc
        email_sent = True

    rec.status = "requested"
    rec.requested_at = datetime.now(UTC)
    await db.flush()
    await db.refresh(rec)  # populate server-generated updated_at for serialization
    response = RecommendationResponse.model_validate(rec)
    response.email_sent = email_sent
    return response
