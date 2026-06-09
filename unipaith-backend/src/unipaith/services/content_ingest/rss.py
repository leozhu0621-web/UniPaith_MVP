"""News-RSS channel source → Updates (InstitutionPost)."""

from __future__ import annotations

from calendar import timegm
from datetime import UTC, datetime

import feedparser

from .base import ChannelSource, NormalizedItem, clean_text


def _entry_dt(entry) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return None
    try:
        return datetime.fromtimestamp(timegm(parsed), tz=UTC)
    except (ValueError, OverflowError):
        return None


class NewsRssSource(ChannelSource):
    """Parse an RSS/Atom news feed into post items (guid → external_id)."""

    name = "news_rss"

    def parse(self, text: str) -> list[NormalizedItem]:
        feed = feedparser.parse(text)
        items: list[NormalizedItem] = []
        for entry in feed.entries[: self.max_items]:
            ext = (
                getattr(entry, "id", None)
                or getattr(entry, "link", None)
                or getattr(entry, "title", None)
            )
            title = (getattr(entry, "title", "") or "").strip()
            if not ext or not title:
                continue
            items.append(
                NormalizedItem(
                    kind="post",
                    external_id=str(ext)[:500],
                    title=title[:255],
                    body=clean_text(getattr(entry, "summary", "") or ""),
                    url=getattr(entry, "link", None),
                    published_at=_entry_dt(entry),
                )
            )
        return items
