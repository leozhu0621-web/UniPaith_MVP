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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.safety import screen
from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.models.discovery import DiscoveryMessage, DiscoverySession
from unipaith.services.discovery_service import DiscoveryService, _msg_dict
from unipaith.services.uni_tools import SURFACED_TOOLS, dispatch_tool

_CALM = "Uni is catching her breath for a moment — please try again shortly."


class UniAgentHost:
    def __init__(self, db: AsyncSession, *, client: Any | None = None) -> None:
        self.db = db
        if client is None:
            from unipaith.ai.managed_agent_client import ManagedAgentClient

            client = ManagedAgentClient()
        self.client = client

    async def _lock_session_row(self, user_id: UUID, session_id: UUID) -> DiscoverySession:
        """Load the discovery session the client opened (validated for
        ownership) with a row lock.

        Binding to the URL session keeps the transcript on the session the
        client is rendering. The ``FOR UPDATE`` lock serializes two overlapping
        first turns so they can't each create a separate platform session
        (read-modify-write race on ``agent_session_id``)."""
        student_id = await DiscoveryService(self.db)._profile_id_for_user(user_id)
        result = await self.db.execute(
            select(DiscoverySession)
            .where(
                DiscoverySession.id == session_id,
                DiscoverySession.student_id == student_id,
            )
            .with_for_update()
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise NotFoundException("Discovery session not found")
        return row

    async def stream_turn(
        self, user_id: UUID, *, session_id: UUID, content: str
    ) -> AsyncIterator[tuple[str, dict]]:
        # ── Setup (may raise → API falls back to the orchestrator) ──
        row = await self._lock_session_row(user_id, session_id)
        if not row.agent_session_id:
            row.agent_session_id = await self.client.create_session(
                agent_id=settings.uni_agent_id,
                environment_id=settings.uni_environment_id,
                title="Uni discovery",
            )
        sid = row.agent_session_id

        # Persist the student turn up front and commit it together with the
        # session binding. This releases the row lock and guarantees the turn
        # is durable before the client is told it landed — a mid-stream failure
        # can never make it vanish.
        student_msg = DiscoveryMessage(session_id=row.id, role="student", content=content)
        self.db.add(student_msg)
        await self.db.commit()
        await self.db.refresh(student_msg)
        yield ("student_message", _msg_dict(student_msg))

        # ── Safety & crisis floor (Spec 61 §4) — always on, before the agent ──
        # Screen the student turn deterministically; on a self-harm / abuse /
        # acute-distress signal, serve the empathetic escalation and skip the
        # managed agent entirely. Never feature-flag-gated.
        crisis = screen(content or "")
        if crisis.is_crisis:
            crisis_assistant = DiscoveryMessage(
                session_id=row.id,
                role="assistant",
                content=crisis.response,
                extracted_signals={
                    "_phase": "safety_escalation",
                    "_mode": "crisis_escalation",
                    "safety_category": crisis.category,
                    "safety_subtype": crisis.subtype,
                },
            )
            self.db.add(crisis_assistant)
            await self.db.commit()
            yield ("delta", {"text": crisis.response})
            yield ("assistant_message", {"content": crisis.response})
            return

        # ── Turn (never 5xx — graceful envelope on mid-stream failure) ──
        reply_parts: list[str] = []
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
                    try:
                        result = await dispatch_tool(
                            self.db, user_id, event.name, event.input or {}, session_id=row.id
                        )
                        await self.client.send_tool_result(sid, event.id, result)
                    except Exception as tool_exc:
                        # A tool crash must still answer the platform tool call,
                        # or the agent stays blocked waiting for the result.
                        result = {"error": "tool_failed", "detail": str(tool_exc)[:200]}
                        await self.client.send_tool_result(sid, event.id, result, is_error=True)
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
            await self._mirror_assistant(row, text)
            yield ("assistant_message", {"content": text})
        except Exception as exc:  # mid-stream: close calmly, never 5xx
            # The student row is already persisted; mirror the calm reply too so
            # the transcript stays complete after an interruption.
            await self._mirror_assistant(row, _CALM)
            yield ("error", {"message": str(exc)[:200]})
            yield ("assistant_message", {"content": _CALM})

    async def _mirror_assistant(self, row: DiscoverySession, assistant_text: str) -> None:
        """Append the assistant reply to discovery_messages for transcript /
        audit / eval (the student row is persisted up front in ``stream_turn``).

        Best-effort — a mirror failure must not break the conversation."""
        try:
            self.db.add(
                DiscoveryMessage(session_id=row.id, role="assistant", content=assistant_text)
            )
            await self.db.commit()
        except Exception:
            await self.db.rollback()
