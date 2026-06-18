"""Scholarships API — Spec 2026-06-14 (Resources › Financial).

Read-only student surface over the external CareerOneStop catalog:
- ``GET /scholarships`` — paginated keyword / level / award-type search.
- ``GET /scholarships/matches`` — a "for your level" list.

Routes mount under ``/api/v1/scholarships`` and require a student.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.services.scholarship_service import ScholarshipService

router = APIRouter(prefix="/scholarships", tags=["scholarships"])


class ScholarshipResponse(BaseModel):
    """Mirrors the model fields. ``award_amount`` / ``deadline`` are verbatim
    source text — shown as-is, never parsed (spec §Data)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    external_id: str
    name: str
    organization: str | None = None
    purpose: str | None = None
    level_of_study: str | None = None
    award_type: str | None = None
    award_amount: str | None = None
    deadline: str | None = None
    url: str | None = None
    source: str


def _serialize(row) -> ScholarshipResponse:  # noqa: ANN001 — ORM row
    return ScholarshipResponse(
        id=str(row.id),
        external_id=row.external_id,
        name=row.name,
        organization=row.organization,
        purpose=row.purpose,
        level_of_study=row.level_of_study,
        award_type=row.award_type,
        award_amount=row.award_amount,
        deadline=row.deadline,
        url=row.url,
        source=row.source,
    )


@router.get("")
async def search_scholarships(
    q: str | None = Query(None, description="Keyword over name / organization / purpose"),
    level: str | None = Query(None, description="level_of_study substring, e.g. 'Bachelor'"),
    award_type: str | None = Query(None, description="Exact award type, e.g. 'Scholarship'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Paginated scholarship search (spec §Slice 2). Default (no filters) lists
    all awards alphabetically; the frontend defaults to ``/matches`` instead."""
    result = await ScholarshipService(db).search(
        q=q,
        level=level,
        award_type=award_type,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return {
        "items": [_serialize(r) for r in result["items"]],
        "total": result["total"],
        "page": page,
    }


@router.get("/matches")
async def scholarship_matches(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """A "for your level" list derived from the student's profile (spec §Slice
    2). Falls back to a general list when no level is derivable — never a fake
    match."""
    rows = await ScholarshipService(db).matches_for_student(user.id, limit=limit)
    return {"items": [_serialize(r) for r in rows]}
