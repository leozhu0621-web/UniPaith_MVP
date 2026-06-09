"""Channel-source abstraction for ingesting a school's public feeds.

A ``ChannelSource`` is a pure parser: it turns raw feed text (already fetched by
the service) into ``NormalizedItem``s. Keeping fetch (network) out of the source
makes parsing trivially unit-testable with fixture strings and lets the Phase-2
social adapters slot in the same way.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def clean_text(raw: str) -> str:
    """Strip HTML tags and collapse whitespace from a feed summary."""
    if not raw:
        return ""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", raw)).strip()


def to_utc(dt: datetime | None) -> datetime | None:
    """Normalize a datetime to timezone-aware UTC (feeds mix naive/aware)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


@dataclass
class NormalizedItem:
    """A feed item normalized to our domain (a post or an event)."""

    kind: str  # "post" | "event"
    external_id: str
    title: str
    body: str = ""
    url: str | None = None
    published_at: datetime | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location: str | None = None


class ChannelSource(ABC):
    """Parses raw feed text into NormalizedItems. Pure — no network."""

    name: str = "channel"
    max_items: int = 25

    @abstractmethod
    def parse(self, text: str) -> list[NormalizedItem]:
        """Parse feed text into items (most-recent first, capped to max_items)."""
        raise NotImplementedError
