"""Spec 42 §3.19–§3.20 / §4.17 — Prompt Library + Story Bank API.

Mounted at /api/v1/students/me/prompt-library. The student-facing behavioral
practice surface: the canonical prompt catalog, per-prompt responses (with
system-derived STAR/impact flags), a reusable story bank, and the §4.17
inference summary (interview readiness, competency coverage, story↔prompt
matching, revision priorities, practice plan). All endpoints require the
student role and are scoped to the caller's own profile.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.prompt_library import (
    BehavioralPromptOut,
    BehavioralResponseOut,
    BehavioralResponseUpsert,
    PromptLibrarySummary,
    StoryCreate,
    StoryOut,
    StoryUpdate,
)
from unipaith.services.prompt_library_service import PromptLibraryService

router = APIRouter(prefix="/students/me/prompt-library", tags=["prompt-library"])


def _svc(db: AsyncSession) -> PromptLibraryService:
    return PromptLibraryService(db)


@router.get("/prompts", response_model=list[BehavioralPromptOut])
async def list_prompts(
    intent: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).list_prompts(intent=intent, channel=channel)


@router.get("/responses", response_model=list[BehavioralResponseOut])
async def list_responses(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_responses(user.id)


@router.put("/responses/{prompt_key}", response_model=BehavioralResponseOut)
async def upsert_response(
    prompt_key: str,
    body: BehavioralResponseUpsert,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).upsert_response(
        user.id,
        prompt_key,
        response_text=body.response_text,
        draft_status=body.validated_draft(),
        confidence_self_rating=body.confidence_self_rating,
        needs_feedback_flag=body.needs_feedback_flag,
        linked_story_id=body.linked_story_id,
    )


@router.get("/stories", response_model=list[StoryOut])
async def list_stories(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).get_stories(user.id)


@router.post("/stories", response_model=StoryOut, status_code=status.HTTP_201_CREATED)
async def create_story(
    body: StoryCreate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).create_story(user.id, body.cleaned())


@router.put("/stories/{story_id}", response_model=StoryOut)
async def update_story(
    story_id: UUID,
    body: StoryUpdate,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).update_story(user.id, story_id, body.cleaned())


@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    await _svc(db).delete_story(user.id, story_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summary", response_model=PromptLibrarySummary)
async def summary(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    return await _svc(db).summary(user.id)
