"""Auto-source a school's Events/Updates from its public channel feeds."""

from .base import ChannelSource, NormalizedItem, passes_relevance
from .events_feed import EventsFeedSource
from .rss import NewsRssSource
from .service import ContentIngestService

__all__ = [
    "ChannelSource",
    "NormalizedItem",
    "passes_relevance",
    "NewsRssSource",
    "EventsFeedSource",
    "ContentIngestService",
]
