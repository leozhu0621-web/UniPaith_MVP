"""Crawler engine — HTTP fetcher and page downloader.

Uses Playwright (headless Chromium) for JavaScript-rendered university pages.
Falls back to aiohttp for simple HTML pages.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import uuid
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.crawler import CrawlJob, SourceURLPattern
from unipaith.models.matching import DataSource, RawIngestedData

logger = logging.getLogger(__name__)

# Shared browser instance (created once, reused)
_browser = None
_playwright = None


async def _get_browser():
    """Get or create a shared headless browser instance."""
    global _browser, _playwright
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright

        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=True)
        logger.info("Headless browser started")
    return _browser


async def _fetch_with_browser(url: str, timeout: int = 30000) -> str:
    """Fetch a page using headless Chromium (handles JS-rendered sites)."""
    browser = await _get_browser()
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=timeout)
        html = await page.content()
        return html
    finally:
        await page.close()


class CrawlerEngine:
    """Fetches pages from data sources and stores raw HTML."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._semaphore = asyncio.Semaphore(settings.crawler_concurrent_requests)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start_crawl(self, source_id: uuid.UUID) -> CrawlJob:
        """Create a CrawlJob and crawl all URL patterns for a source."""
        source = await self.db.get(DataSource, source_id)
        if not source:
            from unipaith.core.exceptions import NotFoundException

            raise NotFoundException(f"Data source {source_id} not found")

        job = CrawlJob(
            source_id=source_id,
            status="running",
            started_at=datetime.now(UTC),
        )
        self.db.add(job)
        await self.db.flush()

        # Load patterns
        result = await self.db.execute(
            select(SourceURLPattern).where(SourceURLPattern.source_id == source_id)
        )
        patterns = list(result.scalars().all())

        if not patterns and source.source_url:
            # Crawl the root URL as a fallback
            patterns = [
                SourceURLPattern(
                    source_id=source_id,
                    url_pattern="/",
                    page_type="program_list",
                    follow_links=True,
                )
            ]

        errors: list[dict] = []
        try:
            for pattern in patterns:
                try:
                    await self._crawl_pattern(job, source, pattern)
                except Exception as exc:
                    logger.error("Pattern %s failed: %s", pattern.url_pattern, exc)
                    errors.append(
                        {
                            "pattern": pattern.url_pattern,
                            "error": str(exc),
                        }
                    )
                    job.pages_failed += 1

            job.status = "completed"
        except Exception as exc:
            job.status = "failed"
            errors.append({"error": str(exc)})
            logger.exception("Crawl job %s failed", job.id)

        job.completed_at = datetime.now(UTC)
        if errors:
            job.error_log = errors
        await self.db.flush()

        logger.info(
            "Crawl job %s finished: status=%s, pages=%d, failed=%d",
            job.id,
            job.status,
            job.pages_crawled,
            job.pages_failed,
        )
        return job

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _crawl_pattern(
        self,
        job: CrawlJob,
        source: DataSource,
        pattern: SourceURLPattern,
    ) -> None:
        """Fetch pages matching a URL pattern using headless browser.

        Uses Playwright to render JavaScript-heavy university sites.
        Falls back to aiohttp for simple pages.
        """
        base_url = source.source_url or ""
        # If pattern is a full URL, use it directly; otherwise join with base
        start_url = (
            pattern.url_pattern
            if pattern.url_pattern.startswith("http")
            else urljoin(base_url, pattern.url_pattern)
        )

        visited: set[str] = set()
        queue: list[str] = [start_url]
        max_pages = settings.crawler_max_pages_per_source

        while queue and job.pages_crawled < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                async with self._semaphore:
                    await asyncio.sleep(settings.crawler_download_delay)
                    html = await _fetch_with_browser(
                        url, timeout=settings.crawler_request_timeout * 1000
                    )
            except Exception as exc:
                logger.warning("Failed to fetch %s: %s", url, exc)
                job.pages_failed += 1
                continue

            # Skip pages that are just loading screens
            cleaned_preview = self.clean_html(html)
            if len(cleaned_preview) < 100:
                logger.debug(
                    "Page too short after cleaning (%d chars), skipping: %s",
                    len(cleaned_preview),
                    url,
                )
                job.pages_failed += 1
                continue

            # Deduplicate by content hash
            content_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
            existing = await self.db.execute(
                select(RawIngestedData).where(
                    RawIngestedData.content_hash == content_hash,
                    RawIngestedData.source_id == source.id,
                )
            )
            if existing.scalar_one_or_none():
                logger.debug("Duplicate content for %s, skipping", url)
                job.items_duplicate += 1
                continue

            # Store raw content
            raw = RawIngestedData(
                source_id=source.id,
                raw_content=html,
                content_hash=content_hash,
                processed=False,
            )
            self.db.add(raw)
            job.pages_crawled += 1
            logger.info("Crawled: %s (%d chars)", url, len(cleaned_preview))

            # Follow links if enabled
            if pattern.follow_links and job.pages_crawled < max_pages:
                links = self._extract_links(html, url, pattern.link_selector)
                for link in links:
                    if link not in visited:
                        queue.append(link)

            # Flush periodically
            if job.pages_crawled % 10 == 0:
                await self.db.flush()

        await self.db.flush()

    @staticmethod
    def _extract_links(html: str, base_url: str, link_selector: str | None) -> list[str]:
        """Extract same-domain links from HTML. Returns at most 50 URLs."""
        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(base_url).netloc

        if link_selector:
            elements = soup.select(link_selector)
        else:
            elements = soup.find_all("a", href=True)

        links: list[str] = []
        for el in elements:
            href = el.get("href")
            if not href or not isinstance(href, str):
                continue
            absolute = urljoin(base_url, href)
            parsed = urlparse(absolute)
            # Same domain only, no fragments, no query-heavy links
            if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
                clean = parsed._replace(fragment="").geturl()
                if clean not in links:
                    links.append(clean)
            if len(links) >= 50:
                break

        return links

    @staticmethod
    def clean_html(html: str) -> str:
        """Strip non-content elements and truncate for LLM consumption."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts, styles, nav, footer, header, aside
        for tag in soup.find_all(
            ["script", "style", "nav", "footer", "header", "aside", "noscript"]
        ):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Truncate
        max_chars = settings.crawler_max_html_chars
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[TRUNCATED]"

        return text
