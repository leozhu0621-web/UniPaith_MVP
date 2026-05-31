"""ConnectFeedRanker — Spec 20 §8.

Haiku-tier (cheap) relevance ranker for the Connect Updates feed. Given the
already-built feed items plus a little student context, it returns the item ids
in relevance order. The calling ``ConnectService`` always has a deterministic
relevance heuristic, so any failure here (consent deny, parse error, provider
error) returns ``None`` and the feed silently falls back (Spec 20 §9).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.connect_ranker_schema import SUBMIT_RANKING_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_PROMPT = (PROMPTS_DIR / "connect_ranker.md").read_text(encoding="utf-8").rstrip()


class ConnectFeedRankerAgent:
    AGENT_NAME = "connect_ranker"

    def __init__(self, client: AIClient | None = None, *, max_tokens: int = 1200):
        self.client = client or get_client()
        self.max_tokens = max_tokens

    async def rank(
        self,
        *,
        items: list[dict],
        applied_programs: list[str],
        saved_programs: list[str],
        student_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> list[str] | None:
        """Return item ids in relevance order, or ``None`` to signal fallback."""
        if not items:
            return None
        try:
            payload = self._payload(items, applied_programs, saved_programs)
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="haiku",
                system=[{"type": "text", "text": _PROMPT, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": payload}],
                tools=[{**SUBMIT_RANKING_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_ranking"},
                max_tokens=self.max_tokens,
                temperature=0.0,
                student_id=student_id,
                surface="connect",
                db=db,
            )
            ranked = self._parse(response.content_blocks)
            return ranked or None
        except Exception as exc:  # noqa: BLE001 — ranking is best-effort
            logger.info("ConnectFeedRanker fell back to deterministic order: %s", exc)
            return None

    @staticmethod
    def _payload(items: list[dict], applied: list[str], saved: list[str]) -> str:
        compact = [
            {
                "id": it["id"],
                "kind": it["kind"],
                "institution": it.get("institution_name"),
                "program": it.get("program_name"),
                "title": it.get("title") or it.get("change_summary"),
                "days_until": it.get("days_until"),
                "date": it.get("date"),
            }
            for it in items
        ]
        return json.dumps(
            {"applied_programs": applied, "saved_programs": saved, "items": compact},
            ensure_ascii=False,
        )

    @staticmethod
    def _parse(blocks: list[dict[str, Any]]) -> list[str]:
        for b in blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_ranking":
                ids = (b.get("input") or {}).get("ranked_ids") or []
                return [str(x) for x in ids if isinstance(x, str | int)]
        return []


_default: ConnectFeedRankerAgent | None = None


def get_connect_ranker() -> ConnectFeedRankerAgent:
    global _default
    if _default is None:
        _default = ConnectFeedRankerAgent()
    return _default


def reset_connect_ranker() -> None:
    global _default
    _default = None
