"""Auto-source a school's Events/Updates from its public channel feeds."""

from .base import ChannelSource, NormalizedItem
from .events_feed import EventsFeedSource
from .rss import NewsRssSource
from .service import ContentIngestService

__all__ = [
    "ChannelSource",
    "NormalizedItem",
    "NewsRssSource",
    "EventsFeedSource",
    "ContentIngestService",
]
