"""Spec 57 §2 — realtime transport endpoints (SSE + WebSocket).

- ``GET  /me/stream``   — Server-Sent Events: the one-way server→client channel
  for the notification bell's live unread count, ``notification.created`` /
  ``notification.read`` pushes, and feed pills. Auth via a bearer header *or* a
  ``?access_token=`` query param (EventSource can't set headers). The long-lived
  stream holds **no** database connection — it only drains the in-process broker
  queue, with a periodic keepalive comment.
- ``WS   /ws/messages`` — WebSocket: the bidirectional messaging channel
  (typing indicators, read receipts, instant delivery). A send pump drains the
  broker to the socket while the receive loop handles ``typing`` / ``read`` /
  ``ping`` frames, fanning typing + read receipts to the other participants.

Both subscribe to ``core/realtime.broker`` so events fan out across ECS tasks via
its Redis bridge when configured.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Header,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse

from unipaith.config import settings
from unipaith.core.exceptions import ForbiddenException
from unipaith.core.realtime import broker, sse_frame
from unipaith.core.realtime import event as rt_event
from unipaith.database import async_session
from unipaith.dependencies import authenticate_token
from unipaith.models.engagement import Conversation
from unipaith.models.institution import Institution
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.services.notification_service import NotificationService

logger = logging.getLogger("unipaith.realtime.api")

router = APIRouter(tags=["realtime"])


def _extract_token(authorization: str | None, access_token: str | None) -> str | None:
    """Pull a bearer token from the Authorization header, else the query param."""
    if authorization:
        scheme, _, tok = authorization.partition(" ")
        if scheme.lower() == "bearer" and tok:
            return tok
    return access_token or None


async def get_stream_user(
    authorization: str | None = Header(None),
    access_token: str | None = Query(None),
) -> User:
    """Authenticate an SSE subscriber. Overridable in tests.

    Uses its own short-lived session so the long-lived SSE response never pins a
    pooled DB connection for the connection's lifetime.
    """
    token = _extract_token(authorization, access_token)
    if not token:
        raise ForbiddenException("Missing access token")
    async with async_session() as db:
        user = await authenticate_token(token, db)
        await db.commit()  # persist any dev-mode auto-provision
        return user


@router.get("/me/stream", summary="SSE stream of realtime events (Spec 57 §2)")
async def me_stream(
    request: Request,
    user: User = Depends(get_stream_user),
) -> StreamingResponse:
    user_id = user.id

    async def gen():
        # Subscribe BEFORE announcing connected, so an event published between
        # auth and subscription isn't missed.
        async with broker.subscribe(user_id) as queue:
            # Initial hello + current unread count so the bell is correct on connect.
            count = 0
            try:
                async with async_session() as db:
                    count = (await NotificationService(db).unread_count(user_id))["count"]
            except Exception:  # noqa: BLE001 — a count hiccup must not abort the stream
                logger.warning("stream initial unread-count failed", exc_info=True)
            yield sse_frame(rt_event("connected", {"unread": count}))

            while True:
                if await request.is_disconnected():
                    break
                try:
                    evt = await asyncio.wait_for(
                        queue.get(), timeout=settings.realtime_heartbeat_seconds
                    )
                    yield sse_frame(evt)
                except TimeoutError:
                    # Comment frame — keeps proxies from idling the connection out.
                    yield ": keepalive\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx/proxy buffering of the stream
        },
    )


# ── WebSocket messaging ──────────────────────────────────────────────────────
async def _other_participants(conversation_id: UUID, sender_user_id: UUID) -> list[UUID]:
    """Resolve the *other* participants' user IDs for a conversation.

    Maps the conversation's ``student_id`` (a StudentProfile) → user_id, the
    institution side (``assigned_to`` user, else the institution admin) and any
    ``peer_student_id`` → user_id, minus the sender. Best-effort: a missing
    conversation returns ``[]`` so a stray typing frame is simply dropped.
    """
    async with async_session() as db:
        conv = await db.get(Conversation, conversation_id)
        if conv is None:
            return []
        user_ids: set[UUID] = set()
        if conv.student_id:
            sp = await db.get(StudentProfile, conv.student_id)
            if sp is not None and sp.user_id:
                user_ids.add(sp.user_id)
        if conv.peer_student_id:
            peer = await db.get(StudentProfile, conv.peer_student_id)
            if peer is not None and peer.user_id:
                user_ids.add(peer.user_id)
        if conv.assigned_to:
            user_ids.add(conv.assigned_to)
        elif conv.institution_id:
            inst = await db.get(Institution, conv.institution_id)
            if inst is not None and inst.admin_user_id:
                user_ids.add(inst.admin_user_id)
        user_ids.discard(sender_user_id)
        return list(user_ids)


async def _handle_ws_inbound(user_id: UUID, msg: object, websocket: WebSocket) -> None:
    """Handle a client→server WS frame: ping/typing/read."""
    if not isinstance(msg, dict):
        return
    mtype = msg.get("type")
    if mtype == "ping":
        await websocket.send_json(rt_event("pong", {}))
        return
    if mtype in ("typing", "read"):
        conv_raw = msg.get("conversation_id")
        if not conv_raw:
            return
        try:
            conv_id = UUID(str(conv_raw))
        except (ValueError, TypeError):
            return
        try:
            others = await _other_participants(conv_id, user_id)
        except Exception:  # noqa: BLE001 — never let a bad frame kill the socket
            logger.warning("ws participant resolution failed", exc_info=True)
            others = []
        out_type = "messaging.typing" if mtype == "typing" else "messaging.read"
        data: dict = {"conversation_id": str(conv_id), "user_id": str(user_id)}
        if mtype == "typing":
            data["is_typing"] = bool(msg.get("is_typing", True))
        for uid in others:
            await broker.publish(uid, rt_event(out_type, data))


@router.websocket("/ws/messages")
async def ws_messages(websocket: WebSocket, access_token: str | None = Query(None)) -> None:
    token = _extract_token(websocket.headers.get("authorization"), access_token)
    user: User | None = None
    if token:
        try:
            async with async_session() as db:
                user = await authenticate_token(token, db)
                await db.commit()
        except Exception:  # noqa: BLE001 — auth failure → polite close below
            user = None
    if user is None:
        await websocket.close(code=4401)  # 4401: app-level "unauthorized"
        return

    await websocket.accept()
    user_id = user.id

    async def pump() -> None:
        # broker → client: drain this user's stream onto the socket.
        async with broker.subscribe(user_id) as queue:
            while True:
                evt = await queue.get()
                await websocket.send_json(evt)

    pump_task = asyncio.create_task(pump())
    try:
        while True:
            msg = await websocket.receive_json()
            await _handle_ws_inbound(user_id, msg, websocket)
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001 — client sent garbage / socket dropped
        logger.info("ws_messages closed", exc_info=True)
    finally:
        pump_task.cancel()
