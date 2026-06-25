"""Phase A — Discovery API.

Endpoints for the Stage 1 (Discovery) journey. Mounted at
/api/students/me/discovery via the students router prefix; the LLM contract
boundary is `POST /sessions/{id}/messages`, which Plan 2 owns.

Phase A3.2 adds an SSE streaming variant at
`/sessions/{id}/messages/stream` so first-token latency lands under the
1.2s p95 target. The non-streaming endpoint is preserved for backwards
compat.
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
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
    HandoffJudgeResponse,
    PersonalitySignalResponse,
    StartSessionRequest,
    UpdateSessionRequest,
)
from unipaith.services.discovery_service import DiscoveryService
from unipaith.services.uni_agent_host import UniAgentHost

logger = logging.getLogger(__name__)

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


@router.post(
    "/sessions/unified",
    response_model=DiscoverySessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_unified_session(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Start the unified, track-less Uni conversation (one session covers
    self/goals/needs by content). The student never picks a track."""
    session = await _svc(db).start_unified_session(user.id)
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


@router.post("/sessions/{session_id}/messages/stream")
async def append_message_stream(
    session_id: UUID,
    body: AppendMessageRequest,
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Server-Sent Events variant of `append_message`.

    Each event is `event: <name>\\ndata: <json>\\n\\n`:

      - `student_message`  — the persisted student row (so the client
                              can correlate without a separate fetch)
      - `delta`            — incremental text chunk from the orchestrator
      - `tool_use`         — completed `record_artifact` /
                              `request_layer_advance` tool call
      - `assistant_message` — the persisted assistant row, fired once
                              streaming completes
      - `error`            — fatal error; stream ends after this
      - `done`             — terminal sentinel

    The role on the request body must be 'student'; staff/system messages
    use the non-streaming endpoint.
    """

    async def _orchestrator_stream():
        async for event_name, payload in _svc(db).stream_message(
            user.id,
            session_id,
            role=body.role,
            content=body.content,
            extracted_signals=body.extracted_signals,
        ):
            yield f"event: {event_name}\ndata: {json.dumps(payload, default=str)}\n\n"
        yield "event: done\ndata: {}\n\n"

    async def _event_stream():
        # Cutover: when the managed agent is on, the platform Uni drives the turn.
        # Its setup either succeeds (we stream its events) or RAISES before any
        # output, in which case we fall back to the in-app orchestrator for the
        # whole turn — students never lose Uni if the platform is unreachable.
        if settings.ai_uni_managed_agent_v1:
            host = UniAgentHost(db)
            turn = host.stream_turn(user.id, content=body.content)
            try:
                first = await turn.__anext__()
            except StopAsyncIteration:
                first = None
            except Exception:
                # The managed agent failed to set up (e.g. a missing/rotated AI key
                # → auth failure). We fall back to the in-app orchestrator so the
                # student never loses Uni — but log it loudly (todo 4.1) so the
                # silent canned-swap leaves an alertable trace instead of vanishing.
                logger.error(
                    "Uni managed-agent setup failed for user=%s — falling back to the "
                    "in-app orchestrator (chat is in limited mode). Check ANTHROPIC_API_KEY "
                    "and platform availability.",
                    user.id,
                    exc_info=True,
                )
                async for frame in _orchestrator_stream():
                    yield frame
                return
            yield f"event: student_message\ndata: {json.dumps({'content': body.content})}\n\n"
            if first is not None:
                name, payload = first
                yield f"event: {name}\ndata: {json.dumps(payload, default=str)}\n\n"
            async for event_name, payload in turn:
                yield f"event: {event_name}\ndata: {json.dumps(payload, default=str)}\n\n"
            yield "event: done\ndata: {}\n\n"
            return
        async for frame in _orchestrator_stream():
            yield frame

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # disables nginx response buffering
        },
    )


@router.post("/opener/stream")
async def discovery_opener_stream(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Uni speaks first. Streamed when the student opens the conversation with no
    messages yet, so Uni greets and leads instead of waiting. Same SSE contract
    as `messages/stream` minus the `student_message` event (the student said
    nothing). When the managed agent is off or its setup fails, a warm
    interactive fallback greeting is served so the conversation always opens."""

    async def _static_opener():
        from unipaith.models.discovery import DiscoveryMessage

        text = (
            "Hi — I'm Uni, your admissions counselor. No forms here, just a "
            "conversation to figure out your path together. To start: what's "
            "drawing you toward your next step?"
        )
        signals = {
            # This static opener only runs when the managed agent is off or its
            # setup failed — i.e. limited mode. Tag it so the UI shows the
            # "Limited mode active — your replies are still saved" banner
            # consistently (it already does for the orchestrator's rule_based
            # turns), instead of silently serving a scripted greeting.
            "_mode": "rule_based",
            "suggested_options": [
                "A field I love",
                "A career goal",
                "A change of direction",
                "I'm not sure yet",
            ],
        }
        try:
            session = await _svc(db).start_unified_session(user.id)
            db.add(
                DiscoveryMessage(
                    session_id=session.id,
                    role="assistant",
                    content=text,
                    extracted_signals=signals,
                )
            )
            await db.commit()
        except Exception:
            await db.rollback()
        yield f"event: delta\ndata: {json.dumps({'text': text})}\n\n"
        yield f"event: assistant_message\ndata: {json.dumps({'content': text})}\n\n"
        yield "event: done\ndata: {}\n\n"

    async def _event_stream():
        if settings.ai_uni_managed_agent_v1:
            host = UniAgentHost(db)
            opener = host.stream_opener(user.id)
            try:
                first = await opener.__anext__()
            except StopAsyncIteration:
                first = None
            except Exception:
                async for frame in _static_opener():
                    yield frame
                return
            if first is not None:
                name, payload = first
                yield f"event: {name}\ndata: {json.dumps(payload, default=str)}\n\n"
            async for event_name, payload in opener:
                yield f"event: {event_name}\ndata: {json.dumps(payload, default=str)}\n\n"
            yield "event: done\ndata: {}\n\n"
            return
        async for frame in _static_opener():
            yield frame

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/completion", response_model=CompletionMapResponse)
async def get_completion_map(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    completion = await _svc(db).get_completion_map(user.id)
    return CompletionMapResponse(**completion)


@router.get("/personality-signals", response_model=list[PersonalitySignalResponse])
async def get_personality_signals(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Spec 19 §6 — personality-layer facets for the Discover artifact rail."""
    signals = await _svc(db).get_personality_signals(user.id)
    return [PersonalitySignalResponse.model_validate(s) for s in signals]


@router.get("/handoff", response_model=HandoffJudgeResponse)
async def get_handoff_verdict(
    user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """Spec 19 §7/§10 — deterministic DiscoveryJudge: is the student
    match-ready across all three tracks?"""
    verdict = await _svc(db).evaluate_handoff(user.id)
    return HandoffJudgeResponse(**verdict)


# Re-export types so importers don't need to dig into schemas; harmless
# convenience for the router layer.
__all__ = ["router", "DiscoveryLayer"]
