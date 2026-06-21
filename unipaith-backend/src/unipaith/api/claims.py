"""Claim API (AI Structure, Spec 2).

POST /institutions/me/claims   mark owned school/program profiles as first-party.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_institution_admin
from unipaith.models.user import User
from unipaith.services.claim_service import ClaimService

router = APIRouter(prefix="/institutions/me/claims", tags=["claims"])


class ClaimRequest(BaseModel):
    program_ids: list[UUID] | None = None
    school_ids: list[UUID] | None = None
    claim_institution: bool = False


@router.post("")
async def create_claims(
    body: ClaimRequest,
    user: User = Depends(require_institution_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await ClaimService(db).claim(
        user.id,
        program_ids=body.program_ids,
        school_ids=body.school_ids,
        claim_institution=body.claim_institution,
    )
