"""Spec 43 — Major-Specific Field Catalog API.

Mounted at /api/v1/students/me/major-specific. The student-facing major-specific
readiness surface: the 15-track field catalog (for the form renderer), the
student's per-track signal subdocuments (validated + §5 provenance), and the
§4.18 inference summary (per-track fit score, readiness band, coverage map,
suggested artifacts, bridge plan). All endpoints require the student role and are
scoped to the caller's own profile.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.major_specific import (
    CatalogResponse,
    MajorSpecificSummary,
    TrackSignalsOut,
    TrackSignalsUpsert,
    TracksResponse,
)
from unipaith.services.major_specific_service import MajorSpecificService

router = APIRouter(prefix="/students/me/major-specific", tags=["major-specific"])


def _svc(db: AsyncSession) -> MajorSpecificService:
    return MajorSpecificService(db)


@router.get("/catalog", response_model=CatalogResponse)
async def get_catalog(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_catalog(user.id)


@router.get("/tracks", response_model=TracksResponse)
async def get_tracks(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_tracks(user.id)


@router.put("/tracks/{track_key}", response_model=TrackSignalsOut)
async def upsert_track(
    track_key: str,
    body: TrackSignalsUpsert,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).upsert_track(user.id, track_key, body.signals)


@router.get("/summary", response_model=MajorSpecificSummary)
async def summary(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).summary(user.id)
