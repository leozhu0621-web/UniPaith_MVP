"""News-RSS channel source → Updates (InstitutionPost)."""

from __future__ import annotations

import re
from calendar import timegm
from datetime import UTC, datetime

import feedparser

from .base import ChannelSource, NormalizedItem, clean_text

_IMG_EXT = re.compile(r"\.(jpe?g|png|webp|avif|gif)(\?|#|$)", re.IGNORECASE)
_IMG_TAG = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.IGNORECASE)


def _entry_dt(entry) -> datetime | None:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return None
    try:
        return datetime.fromtimestamp(timegm(parsed), tz=UTC)
    except (ValueError, OverflowError):
        return None


def _entry_image(entry) -> str | None:
    """Cover image straight from the feed, in order of reliability: media:content,
    media:thumbnail, an image <enclosure>/link, then the first <img> in the
    content:encoded / summary HTML (WordPress feeds like Harvard's Gazette put the
    cover there, not in media:content). Never fabricated — None when absent."""
    for attr in ("media_content", "media_thumbnail"):
        media = getattr(entry, attr, None)
        if isinstance(media, list) and media:
            url = media[0].get("url")
            if url:
                return str(url)
    # <enclosure> / links rel="enclosure" with an image type or extension.
    for link in getattr(entry, "links", None) or []:
        if not isinstance(link, dict):
            continue
        href = link.get("href")
        if not href:
            continue
        ltype = (link.get("type") or "").lower()
        rel = (link.get("rel") or "").lower()
        if ltype.startswith("image/") or (rel == "enclosure" and _IMG_EXT.search(href)):
            return str(href)
    # First <img src> inside content:encoded / summary HTML.
    blobs = [
        c["value"]
        for c in (getattr(entry, "content", None) or [])
        if isinstance(c, dict) and c.get("value")
    ]
    blobs.append(getattr(entry, "summary", "") or "")
    for blob in blobs:
        m = _IMG_TAG.search(blob or "")
        if m:
            return m.group(1)
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
                    image_url=_entry_image(entry),
                )
            )
        return items
