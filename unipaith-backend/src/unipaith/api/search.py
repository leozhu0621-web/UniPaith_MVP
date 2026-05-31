"""Spec 10 — Discovery type-first program search API.

Authed student endpoints:
  POST /students/me/search/interpret  — NL query → constraint chips
  POST /students/me/search/programs   — chips + filters + sort → programs
  GET  /students/me/compare           — current compare set
  POST /students/me/compare/add       — add a program (cap 4)
  DELETE /students/me/compare/{id}    — remove a program
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.search import (
    CompareAddRequest,
    CompareListResponse,
    InterpretRequest,
    InterpretResponse,
    SearchRequest,
    SearchResponse,
)
from unipaith.services.compare_service import CompareService
from unipaith.services.search_service import SearchService
from unipaith.services.student_service import StudentService

router = APIRouter(prefix="/students/me", tags=["discovery-search"])


@router.post("/search/interpret", response_model=InterpretResponse)
async def interpret_query(
    body: InterpretRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> InterpretResponse:
    profile = await StudentService(db)._get_student_profile(user.id)
    return await SearchService(db).interpret(body.query, student_id=profile.id)


@router.post("/search/programs", response_model=SearchResponse)
async def search_programs_typed(
    body: SearchRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    profile = await StudentService(db)._get_student_profile(user.id)
    return await SearchService(db).search(body, student_profile_id=profile.id)


@router.get("/compare", response_model=CompareListResponse)
async def get_compare(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> CompareListResponse:
    profile = await StudentService(db)._get_student_profile(user.id)
    return await CompareService(db).list(profile.id)


@router.post("/compare/add", response_model=CompareListResponse)
async def add_to_compare(
    body: CompareAddRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> CompareListResponse:
    profile = await StudentService(db)._get_student_profile(user.id)
    return await CompareService(db).add(profile.id, body.program_id)


@router.delete("/compare/{program_id}", response_model=CompareListResponse)
async def remove_from_compare(
    program_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
) -> CompareListResponse:
    profile = await StudentService(db)._get_student_profile(user.id)
    return await CompareService(db).remove(profile.id, program_id)
