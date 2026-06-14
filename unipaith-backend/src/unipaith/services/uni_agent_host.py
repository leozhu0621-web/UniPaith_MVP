"""Host that drives a student's Uni managed-agent session and relays it to the
existing discovery SSE contract (student_message / delta / tool_use /
assistant_message / error / done).

Failure policy (the cutover safety net):
  - **Setup failure** (open session row / create platform session) RAISES before
    any event is yielded, so the API layer can fall back to the in-app
    orchestrator for the whole turn — students never lose Uni if the platform is
    unreachable.
  - **Mid-stream failure** (after deltas have started) is caught and closed with
    a calm message — never a 5xx mid-conversation.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.discovery import DiscoveryMessage, DiscoverySession
from unipaith.services.discovery_service import DiscoveryService
from unipaith.services.uni_tools import (
    SURFACED_TOOLS,
    build_suggested_signals,
    dispatch_tool,
)

_CALM = "Uni is catching her breath for a moment — please try again shortly."

# Sent to the platform session when the student opens the conversation but
# hasn't typed anything yet, so Uni speaks first. Never mirrored as a student
# message (the student didn't say it). The agent persona recognizes the marker.
_OPENER_TRIGGER = (
    "[SESSION_START] The student just opened Uni and hasn't typed anything yet. "
    "Greet them warmly (by name if you know it), then lead with your first "
    "question — you speak first."
)


class UniAgentHost:
    def __init__(self, db: AsyncSession, *, client: Any | None = None) -> None:
        self.db = db
        if client is None:
            from unipaith.ai.managed_agent_client import ManagedAgentClient

            client = ManagedAgentClient()
        self.client = client

    async def _get_or_create_session_row(self, user_id: UUID) -> DiscoverySession:
        """The canonical unified Uni discovery session (reuse-or-create), which
        also carries the bound managed-agent session id."""
        return await DiscoveryService(self.db).start_unified_session(user_id)

    async def stream_opener(self, user_id: UUID) -> AsyncIterator[tuple[str, dict]]:
        """Uni speaks first. Kick the platform session with a SESSION_START
        trigger so the agent greets and leads, persisting only her reply (the
        student said nothing). Same SSE contract as a normal turn."""
        async for event in self.stream_turn(user_id, content=_OPENER_TRIGGER, mirror_student=False):
            yield event

    async def stream_turn(
        self, user_id: UUID, *, content: str, mirror_student: bool = True
    ) -> AsyncIterator[tuple[str, dict]]:
        # ── Setup (may raise → API falls back to the orchestrator) ──
        row = await self._get_or_create_session_row(user_id)
        if not row.agent_session_id:
            row.agent_session_id = await self.client.create_session(
                agent_id=settings.uni_agent_id,
                environment_id=settings.uni_environment_id,
                title="Uni discovery",
            )
            await self.db.commit()
        sid = row.agent_session_id

        # ── Turn (never 5xx — graceful envelope on mid-stream failure) ──
        reply_parts: list[str] = []
        suggested_signals: dict | None = None
        try:
            stream = self.client.stream(sid)
            await self.client.send_user_message(sid, content)
            async for event in stream:
                etype = getattr(event, "type", "")
                if etype == "agent.message":
                    for block in getattr(event, "content", []) or []:
                        if getattr(block, "type", "") == "text":
                            reply_parts.append(block.text)
                            yield ("delta", {"text": block.text})
                elif etype == "agent.custom_tool_use":
                    if event.name == "suggest_replies":
                        # UI-only: capture the tap affordances for this turn and
                        # ack the agent. The chips are persisted onto the
                        # assistant message so the frontend renders them.
                        suggested_signals = build_suggested_signals(event.input or {})
                        await self.client.send_tool_result(sid, event.id, {"ok": True})
                        continue
                    result = await dispatch_tool(
                        self.db, user_id, event.name, event.input or {}, session_id=row.id
                    )
                    await self.client.send_tool_result(sid, event.id, result)
                    if event.name in SURFACED_TOOLS:
                        yield ("tool_use", {"tool": event.name, "result": result})
                elif etype == "session.status_idle":
                    sr = getattr(getattr(event, "stop_reason", None), "type", None)
                    if sr in ("end_turn", "retries_exhausted"):
                        break
                    # requires_action → the tool result was already sent above;
                    # keep streaming the agent's resumed events.
                elif etype in ("session.status_terminated", "session.deleted"):
                    break

            text = "".join(reply_parts).strip() or "…"
            await self._mirror(row, content, text, suggested_signals, mirror_student)
            yield ("assistant_message", {"content": text})
        except Exception as exc:  # mid-stream: close calmly, never 5xx
            yield ("error", {"message": str(exc)[:200]})
            yield ("assistant_message", {"content": _CALM})

    async def _mirror(
        self,
        row: DiscoverySession,
        student_text: str,
        assistant_text: str,
        suggested_signals: dict | None = None,
        mirror_student: bool = True,
    ) -> None:
        """Append the turn to discovery_messages for transcript / audit / eval.

        ``suggested_signals`` (from a ``suggest_replies`` tool call) is stamped
        onto the assistant message's ``extracted_signals`` so the Discover
        frontend renders tap-chips / the importance slider — preserving the
        interactive experience on the managed path with no frontend change.

        When ``mirror_student`` is False (the proactive opener), only Uni's reply
        is persisted — there was no student turn to record.

        Best-effort — a mirror failure must not break the conversation."""
        try:
            if mirror_student:
                self.db.add(
                    DiscoveryMessage(session_id=row.id, role="student", content=student_text)
                )
            self.db.add(
                DiscoveryMessage(
                    session_id=row.id,
                    role="assistant",
                    content=assistant_text,
                    extracted_signals=suggested_signals,
                )
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
