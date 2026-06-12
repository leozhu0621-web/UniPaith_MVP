"""Thin async wrapper over the Anthropic managed-agents beta (``client.beta.*``).

Kept separate from ``ai/client.py`` (the Messages-API + cost-ledger singleton) so
the managed-agents surface is isolated and trivially fakeable in tests. The host
(``services/uni_agent_host.py``) depends only on the four methods here — never on
the raw SDK — so an SDK shape change is absorbed in one place.

SDK shapes verified against anthropic 0.105.x:
  - ``beta.sessions.create(agent=<id>, environment_id=..., title=...)`` → session
  - ``beta.sessions.events.stream(sid)`` → ``AsyncStream`` (async-iterable +
    async context manager) of session events
  - ``beta.sessions.events.send(sid, events=[...])`` for user.message /
    user.custom_tool_result
The Sessions resource auto-injects the ``managed-agents`` beta header.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from unipaith.config import settings


class ManagedAgentClient:
    """Async facade over the four managed-agents calls the Uni host needs."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or settings.anthropic_api_key
        self._sdk: Any = None

    def _client(self) -> Any:
        if self._sdk is None:
            from anthropic import AsyncAnthropic

            self._sdk = AsyncAnthropic(api_key=self._api_key)
        return self._sdk

    async def create_session(self, *, agent_id: str, environment_id: str, title: str) -> str:
        sess = await self._client().beta.sessions.create(
            agent=agent_id, environment_id=environment_id, title=title
        )
        return sess.id

    async def send_user_message(self, session_id: str, text: str) -> None:
        await self._client().beta.sessions.events.send(
            session_id,
            events=[{"type": "user.message", "content": [{"type": "text", "text": text}]}],
        )

    async def send_tool_result(
        self, session_id: str, tool_use_id: str, result: dict, *, is_error: bool = False
    ) -> None:
        await self._client().beta.sessions.events.send(
            session_id,
            events=[
                {
                    "type": "user.custom_tool_result",
                    "custom_tool_use_id": tool_use_id,
                    "is_error": is_error,
                    "content": [{"type": "text", "text": json.dumps(result, default=str)}],
                }
            ],
        )

    async def stream(self, session_id: str) -> AsyncIterator[Any]:
        """Yield live session events. The underlying ``AsyncStream`` is both an
        async context manager and an async iterator; entering it here keeps the
        HTTP connection scoped to one turn's iteration."""
        async with await self._client().beta.sessions.events.stream(session_id) as stream:
            async for event in stream:
                yield event
