"""Universal ingestion adapters.

Pluggable adapter system that handles any public data format:
- Web pages (HTML)
- API responses (JSON)
- Video/audio transcripts (YouTube, podcasts via Whisper)
- RSS/Atom feeds
- Documents (PDF, Word)
- Structured data (CSV, government datasets)
- Social media (Reddit, forums)
- Search engine results

Each adapter normalizes content into (raw_text, metadata) tuples that
feed into KnowledgeExtractor.
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import urlparse

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger("unipaith.universal_ingestor")


class IngestedContent:
    """Normalized output from any adapter."""

    __slots__ = ("raw_text", "source_url", "content_format", "metadata")

    def __init__(
        self,
        raw_text: str,
        source_url: str,
        content_format: str = "webpage",
        metadata: dict[str, Any] | None = None,
    ):
        self.raw_text = raw_text
        self.source_url = source_url
        self.content_format = content_format
        self.metadata = metadata or {}


class BaseAdapter(ABC):
    @abstractmethod
    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]: ...

    @staticmethod
    def _clean_html(html: str) -> str:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return re.sub(r"\n{3,}", "\n\n", text)


class WebAdapter(BaseAdapter):
    """Fetches and extracts text from web pages."""

    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    logger.warning("HTTP %d for %s", resp.status, url)
                    return []
                html = await resp.text()

        text = self._clean_html(html)
        if len(text) < 50:
            return []

        soup = BeautifulSoup(html, "lxml")
        title = soup.title.string if soup.title else None
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            raw = meta_tag["content"]
            meta_desc = raw if isinstance(raw, str) else raw[0] if raw else ""

        return [
            IngestedContent(
                raw_text=text,
                source_url=url,
                content_format="webpage",
                metadata={"title": title, "meta_description": meta_desc},
            )
        ]


class APIAdapter(BaseAdapter):
    """Fetches and normalizes JSON API responses."""

    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]:
        headers = kwargs.get("headers", {})
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        import json

        text = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        return [
            IngestedContent(
                raw_text=text,
                source_url=url,
                content_format="api_response",
                metadata={"response_type": type(data).__name__},
            )
        ]


class TranscriptAdapter(BaseAdapter):
    """Fetches transcripts from YouTube videos."""

    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]:
        video_id = _extract_youtube_id(url)
        if not video_id:
            logger.warning("Could not extract YouTube video ID from %s", url)
            return []

        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            transcript = YouTubeTranscriptApi().fetch(video_id)
            text = " ".join(snippet.text for snippet in transcript)
        except Exception:
            logger.warning("Could not fetch transcript for %s", url)
            return []

        if len(text) < 50:
            return []

        return [
            IngestedContent(
                raw_text=text,
                source_url=url,
                content_format="video_transcript",
                metadata={"video_id": video_id, "platform": "youtube"},
            )
        ]


class RSSAdapter(BaseAdapter):
    """Parses RSS/Atom feeds and returns each entry as a content item."""

    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]:
        import feedparser

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return []
                raw = await resp.text()

        feed = feedparser.parse(raw)
        results = []
        for entry in feed.entries[:50]:
            text_parts = []
            if hasattr(entry, "title"):
                text_parts.append(entry.title)
            if hasattr(entry, "summary"):
                text_parts.append(self._clean_html(entry.summary))
            if hasattr(entry, "content"):
                for c in entry.content:
                    text_parts.append(self._clean_html(c.get("value", "")))

            text = "\n\n".join(text_parts)
            if len(text) < 30:
                continue

            results.append(
                IngestedContent(
                    raw_text=text,
                    source_url=entry.get("link", url),
                    content_format="rss_entry",
                    metadata={
                        "feed_url": url,
                        "feed_title": feed.feed.get("title", ""),
                        "published": entry.get("published", ""),
                    },
                )
            )
        return results


class DocumentAdapter(BaseAdapter):
    """Extracts text from PDF documents."""

    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    return []
                content = await resp.read()

        try:
            import io

            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            logger.warning("PDF extraction failed for %s", url)
            return []

        if len(text) < 50:
            return []

        return [
            IngestedContent(
                raw_text=text,
                source_url=url,
                content_format="document",
                metadata={"format": "pdf", "pages": len(reader.pages)},
            )
        ]


class StructuredDataAdapter(BaseAdapter):
    """Handles structured data (CSV/JSON datasets)."""

    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                if resp.status != 200:
                    return []
                text = await resp.text()

        if url.endswith(".csv") or "text/csv" in str(kwargs.get("content_type", "")):
            lines = text.strip().split("\n")
            header = lines[0] if lines else ""
            sample = "\n".join(lines[:100])
            return [
                IngestedContent(
                    raw_text=sample,
                    source_url=url,
                    content_format="government_dataset",
                    metadata={"format": "csv", "header": header, "total_rows": len(lines) - 1},
                )
            ]

        return [
            IngestedContent(
                raw_text=text[:200_000],
                source_url=url,
                content_format="government_dataset",
                metadata={"format": "text"},
            )
        ]


class SocialAdapter(BaseAdapter):
    """Handles social media content (Reddit, forums)."""

    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]:
        parsed = urlparse(url)
        if "reddit.com" in parsed.netloc:
            return await self._ingest_reddit(url)
        return await self._ingest_generic_forum(url)

    async def _ingest_reddit(self, url: str) -> list[IngestedContent]:
        json_url = url.rstrip("/") + ".json"
        headers = {"User-Agent": "UniPaith-KnowledgeEngine/1.0"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                json_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        results = []
        if isinstance(data, list) and len(data) > 0:
            post_data = data[0].get("data", {}).get("children", [])
            if post_data:
                post = post_data[0].get("data", {})
                title = post.get("title", "")
                selftext = post.get("selftext", "")
                text = f"{title}\n\n{selftext}"
                results.append(
                    IngestedContent(
                        raw_text=text,
                        source_url=url,
                        content_format="social_post",
                        metadata={
                            "platform": "reddit",
                            "subreddit": post.get("subreddit", ""),
                            "score": post.get("score", 0),
                        },
                    )
                )

            if len(data) > 1:
                comments = data[1].get("data", {}).get("children", [])
                for comment in comments[:30]:
                    body = comment.get("data", {}).get("body", "")
                    if len(body) > 30:
                        results.append(
                            IngestedContent(
                                raw_text=body,
                                source_url=url,
                                content_format="social_post",
                                metadata={
                                    "platform": "reddit",
                                    "type": "comment",
                                    "score": comment.get("data", {}).get("score", 0),
                                },
                            )
                        )

        return results

    async def _ingest_generic_forum(self, url: str) -> list[IngestedContent]:
        adapter = WebAdapter()
        return await adapter.ingest(url)


class SearchAdapter(BaseAdapter):
    """Uses search APIs to discover content."""

    async def ingest(self, url: str, **kwargs: Any) -> list[IngestedContent]:
        query = kwargs.get("query", "")
        if not query:
            return []

        search_url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {"User-Agent": "UniPaith-KnowledgeEngine/1.0"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                search_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()

        soup = BeautifulSoup(html, "lxml")
        links = []
        for result in soup.select(".result__a"):
            href = result.get("href", "")
            if isinstance(href, str) and href.startswith("http"):
                links.append(href)

        return [
            IngestedContent(
                raw_text="\n".join(links[:20]),
                source_url=search_url,
                content_format="api_response",
                metadata={"type": "search_results", "query": query, "result_count": len(links)},
            )
        ]


ADAPTER_REGISTRY: dict[str, type[BaseAdapter]] = {
    "web": WebAdapter,
    "api": APIAdapter,
    "transcript": TranscriptAdapter,
    "rss": RSSAdapter,
    "document": DocumentAdapter,
    "structured": StructuredDataAdapter,
    "social": SocialAdapter,
    "search": SearchAdapter,
}


def get_adapter(content_format: str) -> BaseAdapter:
    adapter_cls = ADAPTER_REGISTRY.get(content_format, WebAdapter)
    return adapter_cls()


def detect_adapter(url: str) -> str:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if "youtube.com" in domain or "youtu.be" in domain:
        return "transcript"
    if "reddit.com" in domain:
        return "social"
    if url.endswith(".pdf"):
        return "document"
    if url.endswith(".csv") or url.endswith(".json"):
        return "structured"
    if "rss" in url or "feed" in url or "atom" in url:
        return "rss"
    if "/api/" in url or "api." in domain:
        return "api"
    return "web"


def _extract_youtube_id(url: str) -> str | None:
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
