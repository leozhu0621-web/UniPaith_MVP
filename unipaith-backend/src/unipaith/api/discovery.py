"""Phase A — Discovery API.

Endpoints for the Stage 1 (Discovery) journey. Mounted at
/api/students/me/discovery via the students router prefix; the LLM contract
boundary is `POST /sessions/{id}/messages`, which Plan 2 will own.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.database import get_db
from unipaith.dependencies import require_student
from unipaith.models.user import User
from unipaith.schemas.discovery import (
    AppendMessageRequest,
    AppendMessageResponse,
    CompletionMapResponse,
    DiscoveryLayer,
    DiscoveryMessageResponse,
    DiscoverySessionDetailResponse,
    DiscoverySessionResponse,
    DiscoveryStatus,
    DiscoveryTrack,
    StartSessionRequest,
    UpdateSessionRequest,
)
from unipaith.services.discovery_service import DiscoveryService

router = APIRouter(prefix="/students/me/discovery", tags=["discovery"])


def _svc(db: AsyncSession) -> DiscoveryService:
    return DiscoveryService(db)


@router.post(
    "/sessions",
    response_model=DiscoverySessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_session(
    body: StartSessionRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    session = await _svc(db).start_session(user.id, track=body.track, layer=body.layer)
    return DiscoverySessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[DiscoverySessionResponse])
async def list_sessions(
    track: DiscoveryTrack | None = Query(None),
    status_filter: DiscoveryStatus | None = Query(None, alias="status"),
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    sessions = await _svc(db).list_sessions(user.id, track=track, status=status_filter)
    return [DiscoverySessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=DiscoverySessionDetailResponse)
async def get_session(
    session_id: UUID,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    session = await _svc(db).get_session(user.id, session_id)
    return DiscoverySessionDetailResponse.model_validate(session)


@router.patch("/sessions/{session_id}", response_model=DiscoverySessionResponse)
async def update_session(
    session_id: UUID,
    body: UpdateSessionRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    session = await _svc(db).update_session(
        user.id,
        session_id,
        status=body.status,
        completion_pct=body.completion_pct,
        exit_signal=body.exit_signal,
    )
    return DiscoverySessionResponse.model_validate(session)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=AppendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def append_message(
    session_id: UUID,
    body: AppendMessageRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    student_msg, assistant_msg = await _svc(db).append_message(
        user.id,
        session_id,
        role=body.role,
        content=body.content,
        extracted_signals=body.extracted_signals,
    )
    return AppendMessageResponse(
        student_message=DiscoveryMessageResponse.model_validate(student_msg),
        assistant_message=(
            DiscoveryMessageResponse.model_validate(assistant_msg)
            if assistant_msg is not None
            else None
        ),
    )


@router.get("/completion", response_model=CompletionMapResponse)
async def get_completion_map(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    completion = await _svc(db).get_completion_map(user.id)
    return CompletionMapResponse(**completion)


# Re-export types so importers don't need to dig into schemas; harmless
# convenience for the router layer.
__all__ = ["router", "DiscoveryLayer"]
