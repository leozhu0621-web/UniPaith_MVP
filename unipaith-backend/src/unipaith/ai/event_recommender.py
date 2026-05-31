"""EventRecommender — Spec 20 §8.

Haiku-tier agent that picks which upcoming events to nudge a student toward —
events on programs they've saved or applied to and haven't RSVP'd. The calling
``ConnectService`` has a deterministic ``recommended`` flag, so any failure here
returns ``None`` and the deterministic nudges stand (Spec 20 §9).
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.connect_ranker_schema import SUBMIT_EVENT_RECS_TOOL

logger = logging.getLogger(__name__)

_PROMPT = (
    "You recommend events for an admissions platform. Given a student's upcoming "
    "events from institutions they follow, return the ids of events worth nudging "
    "them to attend — prioritize events tied to programs they care about and "
    "high-signal formats (info session, Q&A, portfolio review) they haven't "
    "RSVP'd. Return ids via submit_event_recommendations, most relevant first. An "
    "empty list is valid. Never invent ids."
)


class EventRecommenderAgent:
    AGENT_NAME = "event_recommender"

    def __init__(self, client: AIClient | None = None, *, max_tokens: int = 600):
        self.client = client or get_client()
        self.max_tokens = max_tokens

    async def recommend(
        self,
        *,
        events: list[dict],
        student_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> list[str] | None:
        if not events:
            return None
        try:
            compact = [
                {
                    "id": e["id"],
                    "type": e.get("event_type"),
                    "name": e.get("event_name"),
                    "institution": e.get("institution_name"),
                    "program_id": e.get("program_id"),
                }
                for e in events
            ]
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="haiku",
                system=[{"type": "text", "text": _PROMPT, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": json.dumps({"events": compact})}],
                tools=[{**SUBMIT_EVENT_RECS_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_event_recommendations"},
                max_tokens=self.max_tokens,
                temperature=0.0,
                student_id=student_id,
                surface="connect",
                db=db,
            )
            for b in response.content_blocks:
                if b.get("type") == "tool_use" and b.get("name") == "submit_event_recommendations":
                    ids = (b.get("input") or {}).get("recommended_ids") or []
                    return [str(x) for x in ids if isinstance(x, str | int)]
            return None
        except Exception as exc:  # noqa: BLE001 — recommendations are best-effort
            logger.info("EventRecommender fell back to deterministic nudges: %s", exc)
            return None


_default: EventRecommenderAgent | None = None


def get_event_recommender() -> EventRecommenderAgent:
    global _default
    if _default is None:
        _default = EventRecommenderAgent()
    return _default


def reset_event_recommender() -> None:
    global _default
    _default = None
