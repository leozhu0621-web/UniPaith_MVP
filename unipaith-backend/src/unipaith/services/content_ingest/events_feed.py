"""Events channel source → Events. iCal (default) or RSS."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

from icalendar import Calendar

from .base import ChannelSource, NormalizedItem, clean_text, to_utc
from .rss import NewsRssSource


def _ical_dt(prop) -> datetime | None:
    """An iCal DTSTART/DTEND value to UTC datetime (all-day dates → midnight)."""
    if prop is None:
        return None
    val = getattr(prop, "dt", None)
    if val is None:
        return None
    if isinstance(val, datetime):
        return to_utc(val)
    if isinstance(val, date):
        return datetime.combine(val, time.min, tzinfo=UTC)
    return None


class EventsFeedSource(ChannelSource):
    """Parse a school's events feed (iCal default, or RSS) into event items."""

    name = "events_feed"

    def __init__(self, feed_type: str = "ical") -> None:
        self.feed_type = (feed_type or "ical").lower()

    def parse(self, text: str) -> list[NormalizedItem]:
        if self.feed_type == "rss":
            return self._parse_rss(text)
        return self._parse_ical(text)

    def _parse_ical(self, text: str) -> list[NormalizedItem]:
        try:
            cal = Calendar.from_ical(text)
        except Exception:  # noqa: BLE001 — malformed feed → no items
            return []
        items: list[NormalizedItem] = []
        for comp in cal.walk("VEVENT"):
            uid = str(comp.get("UID") or "").strip()
            start = _ical_dt(comp.get("DTSTART"))
            title = str(comp.get("SUMMARY") or "").strip()
            if not uid or not start or not title:
                continue
            url = str(comp.get("URL") or "").strip() or None
            loc = str(comp.get("LOCATION") or "").strip() or None
            items.append(
                NormalizedItem(
                    kind="event",
                    external_id=uid[:500],
                    title=title[:255],
                    body=clean_text(str(comp.get("DESCRIPTION") or "")),
                    url=url,
                    start_time=start,
                    end_time=_ical_dt(comp.get("DTEND")),
                    location=loc[:500] if loc else None,
                )
            )
        # Soonest upcoming first; cap.
        items.sort(key=lambda i: i.start_time or datetime.max.replace(tzinfo=UTC))
        return items[: self.max_items]

    def _parse_rss(self, text: str) -> list[NormalizedItem]:
        # Reuse the RSS parser, but tag the items as events (no precise times).
        posts = NewsRssSource().parse(text)
        return [
            NormalizedItem(
                kind="event",
                external_id=p.external_id,
                title=p.title,
                body=p.body,
                url=p.url,
                start_time=p.published_at,
                image_url=p.image_url,
            )
            for p in posts
            if p.published_at
        ][: self.max_items]
