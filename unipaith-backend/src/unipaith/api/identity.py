"""Phase A — Identity API. Mounted at /api/v1/students/me/identity.

Single-row-per-student. GET auto-creates an empty row if none exists, so the
client never has to special-case "first read" vs "subsequent read." PUT is
upsert with field preservation.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.identity import IdentityResponse, UpsertIdentityRequest
from unipaith.services.identity_service import IdentityService
from unipaith.services.match_service import invalidate_matches_for_user

router = APIRouter(prefix="/students/me/identity", tags=["identity"])


def _svc(db: AsyncSession) -> IdentityService:
    return IdentityService(db)


@router.get("", response_model=IdentityResponse)
async def get_identity(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    identity = await _svc(db).get(user.id)
    return IdentityResponse.model_validate(identity)


@router.put("", response_model=IdentityResponse)
async def upsert_identity(
    body: UpsertIdentityRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    identity = await _svc(db).upsert(user.id, body)
    await invalidate_matches_for_user(db, user.id)  # spec 06 §5.1
    return IdentityResponse.model_validate(identity)


@router.post("/regenerate-summary", response_model=IdentityResponse)
async def regenerate_summary(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    identity = await _svc(db).regenerate_summary(user.id)
    return IdentityResponse.model_validate(identity)
