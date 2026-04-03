"""Autonomous source discovery.

The engine discovers its own knowledge sources. No hardcoded list boundaries.
Strategies:
- Link extraction from processed documents (cross-domain discovery)
- Gap-driven search (identifies what topics lack coverage and searches for them)
- Domain expansion (finds related domains from known good sources)
- Frontier queue management with priority and dedup
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.crawler.universal_ingestor import SearchAdapter, detect_adapter
from unipaith.models.knowledge import (
    CrawlFrontier,
    EngineDirective,
    KnowledgeDocument,
    KnowledgeLink,
)

logger = logging.getLogger("unipaith.source_discoverer")

EXCLUDED_DOMAINS = {
    "google.com",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "tiktok.com",
    "amazon.com",
    "ebay.com",
    "wikipedia.org",
}

EDUCATION_DOMAIN_SIGNALS = [
    ".edu",
    "admissions",
    "graduate",
    "university",
    "college",
    "scholarship",
    "ranking",
    "niche.com",
    "gradcafe",
    "unigo",
    "usnews.com",
    "topuniversities.com",
    "timeshighereducation.com",
    "insidehighered.com",
    "chronicle.com",
    "collegeboard.org",
    "commonapp.org",
    "petersons.com",
    "program",
    "school",
    "faculty",
    "research",
    "student",
    "academic",
    "degree",
    "phd",
    "master",
    "mba",
    "engineering",
    "science",
    "department",
    "apply",
    "tuition",
    "campus",
    "prepscholar.com",
    "cappex.com",
    "collegedata.com",
    "bigfuture",
    "princetonreview.com",
    "collegeraptor.com",
    "collegesimply.com",
    "bestcolleges.com",
]

GAP_SEARCH_TEMPLATES = [
    "{entity} graduate admissions requirements",
    "{entity} student reviews experiences",
    "{entity} acceptance rate admission statistics",
    "{entity} scholarship financial aid",
    "{entity} program ranking comparison",
    "best {field} programs graduate school",
    "graduate admissions trends {year}",
]

# No KnowledgeLink rows yet: entity queries are empty; add generic gap searches.
COLD_START_GAP_QUERIES: tuple[str, ...] = (
    "graduate school admissions requirements computer science",
    "international student financial aid US university graduate",
    "PhD application deadlines engineering programs",
    "GRE requirements top graduate programs",
)


class SourceDiscoverer:
    """Autonomously discovers new knowledge sources."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_discovery_cycle(self, max_new_urls: int = 50) -> dict:
        """Run a complete discovery cycle using all strategies."""
        results = {"link_extraction": 0, "gap_search": 0, "domain_expansion": 0}

        directives = await self._get_active_directives()
        exclusions = _extract_exclusions(directives)

        new_from_links = await self._discover_from_links(
            max_urls=max_new_urls // 2,
            exclusions=exclusions,
        )
        results["link_extraction"] = new_from_links

        new_from_gaps = await self._discover_from_gaps(
            max_urls=max_new_urls // 3,
            exclusions=exclusions,
            directives=directives,
        )
        results["gap_search"] = new_from_gaps

        new_from_domains = await self._discover_from_domains(
            max_urls=max_new_urls // 4,
            exclusions=exclusions,
        )
        results["domain_expansion"] = new_from_domains

        await self.db.flush()
        total = sum(results.values())
        logger.info("Discovery cycle: %d new URLs added (%s)", total, results)
        return results

    async def add_to_frontier(
        self,
        url: str,
        priority: int = 50,
        discovery_method: str | None = None,
        discovered_from_id: UUID | None = None,
        content_format_hint: str | None = None,
    ) -> CrawlFrontier | None:
        url = url.strip()
        if not url.startswith("http"):
            return None

        domain = urlparse(url).netloc.lower()
        if any(excluded in domain for excluded in EXCLUDED_DOMAINS):
            return None

        existing = await self.db.execute(
            select(CrawlFrontier).where(CrawlFrontier.url == url).limit(1)
        )
        if existing.scalar_one_or_none():
            return None

        frontier_item = CrawlFrontier(
            url=url,
            domain=domain,
            priority=priority,
            content_format_hint=content_format_hint or detect_adapter(url),
            discovery_method=discovery_method,
            discovered_from_id=discovered_from_id,
        )
        self.db.add(frontier_item)
        return frontier_item

    async def ensure_bootstrap_frontier(self, urls: list[str]) -> int:
        """If there are no pending URLs, insert high-priority seeds so the engine can ingest."""
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(func.count())
            .select_from(CrawlFrontier)
            .where(
                CrawlFrontier.status == "pending",
                (CrawlFrontier.next_crawl_after.is_(None))
                | (CrawlFrontier.next_crawl_after <= now),
            )
        )
        pending_ready = int(result.scalar() or 0)
        if pending_ready > 0:
            return 0

        added = 0
        for url in urls:
            item = await self.add_to_frontier(
                url,
                priority=100,
                discovery_method="bootstrap_seed",
            )
            if item:
                added += 1
        await self.db.flush()
        if added:
            logger.info("Bootstrap frontier: added %d seed URLs (pending was 0)", added)
        return added

    async def get_next_batch(self, batch_size: int = 10) -> list[CrawlFrontier]:
        """Get the next batch of URLs to crawl, respecting domain rate limits."""
        now = datetime.now(UTC)
        result = await self.db.execute(
            select(CrawlFrontier)
            .where(
                CrawlFrontier.status == "pending",
                (CrawlFrontier.next_crawl_after.is_(None))
                | (CrawlFrontier.next_crawl_after <= now),
            )
            .order_by(CrawlFrontier.priority.desc(), CrawlFrontier.created_at.asc())
            .limit(batch_size * 3)
        )
        candidates = result.scalars().all()

        seen_domains: dict[str, int] = {}
        selected: list[CrawlFrontier] = []
        for item in candidates:
            domain_count = seen_domains.get(item.domain, 0)
            if domain_count >= 2:
                continue
            selected.append(item)
            seen_domains[item.domain] = domain_count + 1
            if len(selected) >= batch_size:
                break

        return selected

    async def mark_crawled(
        self,
        frontier_id: UUID,
        success: bool,
        error: str | None = None,
    ) -> None:
        result = await self.db.execute(select(CrawlFrontier).where(CrawlFrontier.id == frontier_id))
        item = result.scalar_one_or_none()
        if not item:
            return

        now = datetime.now(UTC)
        item.last_crawled_at = now
        item.crawl_count += 1

        if success:
            item.status = "completed"
            item.consecutive_failures = 0
            item.next_crawl_after = now + timedelta(days=7)
        else:
            item.consecutive_failures += 1
            item.last_error = error
            if item.consecutive_failures >= 3:
                item.status = "failed"
            else:
                backoff = min(24 * item.consecutive_failures, 72)
                item.next_crawl_after = now + timedelta(hours=backoff)

    async def _discover_from_links(
        self,
        max_urls: int,
        exclusions: set[str],
    ) -> int:
        """Extract URLs from recently processed documents."""
        total_docs = await self.db.scalar(
            select(func.count()).select_from(KnowledgeDocument)
            .where(KnowledgeDocument.processing_status == "completed")
        ) or 0
        cold_start = total_docs < 100

        recent_docs = await self.db.execute(
            select(KnowledgeDocument)
            .where(
                KnowledgeDocument.processing_status == "completed",
                KnowledgeDocument.raw_text.isnot(None),
            )
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(100 if cold_start else 50)
        )

        added = 0
        for doc in recent_docs.scalars().all():
            if added >= max_urls:
                break
            urls = _extract_urls(doc.raw_text or "")
            for url in urls:
                if added >= max_urls:
                    break
                domain = urlparse(url).netloc.lower()
                if domain in exclusions:
                    continue
                if cold_start:
                    if not _is_plausible_content_url(url):
                        continue
                else:
                    if not _is_education_relevant(url):
                        continue
                item = await self.add_to_frontier(
                    url,
                    priority=40,
                    discovery_method="link_extraction",
                    discovered_from_id=doc.id,
                )
                if item:
                    added += 1

        if added > 0:
            logger.info("Link extraction: found %d new URLs from %d docs", added, total_docs)
        return added

    async def _discover_from_gaps(
        self,
        max_urls: int,
        exclusions: set[str],
        directives: list[EngineDirective],
    ) -> int:
        """Find coverage gaps and search for content to fill them."""
        entity_counts = await self.db.execute(
            select(
                KnowledgeLink.entity_type,
                KnowledgeLink.entity_name,
                func.count().label("doc_count"),
            )
            .group_by(KnowledgeLink.entity_type, KnowledgeLink.entity_name)
            .having(func.count() < 3)
            .limit(20)
        )

        steering = _extract_steering_topics(directives)
        search_queries = []

        for row in entity_counts.all():
            entity_name = row.entity_name or ""
            if len(entity_name) < 3:
                continue
            template = GAP_SEARCH_TEMPLATES[len(search_queries) % len(GAP_SEARCH_TEMPLATES)]
            query = template.format(
                entity=entity_name,
                field=entity_name,
                year=datetime.now(UTC).year,
            )
            search_queries.append(query)

        for topic in steering[:5]:
            search_queries.append(f"{topic} graduate admissions latest")

        if len(search_queries) < 4:
            for q in COLD_START_GAP_QUERIES:
                if q not in search_queries:
                    search_queries.append(q)
                if len(search_queries) >= 10:
                    break

        added = 0
        search = SearchAdapter()
        search_failures = 0
        for query in search_queries[:10]:
            if added >= max_urls:
                break
            try:
                results = await search.ingest("", query=query)
                for result in results:
                    for url in result.raw_text.split("\n"):
                        url = url.strip()
                        if not url.startswith("http"):
                            continue
                        if added >= max_urls:
                            break
                        domain = urlparse(url).netloc.lower()
                        if domain in exclusions:
                            continue
                        item = await self.add_to_frontier(
                            url,
                            priority=60,
                            discovery_method="gap_search",
                        )
                        if item:
                            added += 1
            except Exception as exc:
                search_failures += 1
                logger.warning("Gap search failed for '%s': %s", query, exc)

        if search_failures > 0 and added == 0:
            logger.info(
                "Gap search: all %d queries failed; using fallback seed URLs",
                search_failures,
            )
            added += await self._fallback_seed_urls(max_urls, exclusions)

        return added

    async def _fallback_seed_urls(
        self, max_urls: int, exclusions: set[str]
    ) -> int:
        """When search-based discovery fails, seed from a curated list."""
        fallback = [
            "https://www.harvard.edu/programs/",
            "https://www.stanford.edu/list/academic/",
            "https://catalog.mit.edu/",
            "https://www.yale.edu/academics/departments-programs",
            "https://bulletin.columbia.edu/",
            "https://www.caltech.edu/academics/departments",
            "https://registrar.princeton.edu/course-offerings",
            "https://www.brown.edu/academics/programs",
            "https://catalog.upenn.edu/",
            "https://www.cornell.edu/academics/fields.cfm",
            "https://www.cmu.edu/academics/index.html",
            "https://www.northwestern.edu/academics/",
            "https://gradschool.duke.edu/academics/programs",
            "https://graduate.rice.edu/programs",
            "https://gsas.nyu.edu/admissions.html",
            "https://www.gradadmissions.gatech.edu/programs",
            "https://www.grad.uiuc.edu/programs",
            "https://rackham.umich.edu/programs-of-study/",
            "https://www.grad.ucla.edu/programs/",
            "https://grad.berkeley.edu/programs/list/",
            "https://www.gradschool.washington.edu/programs",
            "https://grad.wisc.edu/programs/",
            "https://gradschool.unc.edu/academics/degreeprograms/",
            "https://www.grad.ubc.ca/prospective-students/graduate-degree-programs",
            "https://www.ox.ac.uk/admissions/graduate/courses/courses-a-z-listing/",
            "https://www.graduate-admissions.cam.ac.uk/courses",
            "https://www.imperial.ac.uk/study/courses/",
            "https://www.ucl.ac.uk/prospective-students/graduate/",
            "https://www.ethz.ch/en/studies/master.html",
            "https://www.topuniversities.com/university-rankings/university-subject-rankings",
            "https://www.niche.com/graduate-schools/search/best-graduate-schools/",
            "https://www.usnews.com/best-graduate-schools",
            "https://www.prepscholar.com/gre/blog/best-graduate-schools/",
            "https://www.princetonreview.com/grad-school-rankings",
            "https://www.insidehighered.com/news",
            "https://www.chronicle.com/section/Facts-Figures",
        ]
        added = 0
        for url in fallback:
            if added >= max_urls:
                break
            domain = urlparse(url).netloc.lower()
            if domain in exclusions:
                continue
            item = await self.add_to_frontier(
                url,
                priority=55,
                discovery_method="fallback_seed",
            )
            if item:
                added += 1
        if added:
            logger.info("Fallback seeds: added %d URLs", added)
        return added

    async def _discover_from_domains(
        self,
        max_urls: int,
        exclusions: set[str],
    ) -> int:
        """Find new pages on known good domains."""
        good_domains = await self.db.execute(
            select(KnowledgeDocument.source_domain, func.avg(KnowledgeDocument.quality_score))
            .where(
                KnowledgeDocument.quality_score > 0.3,
                KnowledgeDocument.source_domain.isnot(None),
            )
            .group_by(KnowledgeDocument.source_domain)
            .having(func.count() >= 1)
            .order_by(func.avg(KnowledgeDocument.quality_score).desc())
            .limit(20)
        )

        added = 0
        for row in good_domains.all():
            if added >= max_urls:
                break
            domain = row[0]
            if domain in exclusions:
                continue

            sitemap_urls = [
                f"https://{domain}/sitemap.xml",
                f"https://{domain}/graduate/sitemap.xml",
                f"https://{domain}/admissions/sitemap.xml",
            ]
            for sitemap_url in sitemap_urls:
                try:
                    import aiohttp

                    async with aiohttp.ClientSession() as session:
                        async with session.get(
                            sitemap_url,
                            timeout=aiohttp.ClientTimeout(total=10),
                        ) as resp:
                            if resp.status != 200:
                                continue
                            sitemap_text = await resp.text()

                    urls = re.findall(r"<loc>(https?://[^<]+)</loc>", sitemap_text)
                    for url in urls[:20]:
                        if added >= max_urls:
                            break
                        if _is_education_relevant(url):
                            item = await self.add_to_frontier(
                                url,
                                priority=45,
                                discovery_method="domain_expansion",
                            )
                            if item:
                                added += 1
                except Exception:
                    continue

        return added

    async def _get_active_directives(self) -> list[EngineDirective]:
        result = await self.db.execute(
            select(EngineDirective).where(EngineDirective.is_active.is_(True))
        )
        return list(result.scalars().all())


def _extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s<>\"')\]]+", text)


def _is_education_relevant(url: str) -> bool:
    url_lower = url.lower()
    return any(signal in url_lower for signal in EDUCATION_DOMAIN_SIGNALS)


def _is_plausible_content_url(url: str) -> bool:
    """Broader filter for cold-start: accept any URL that looks like real content."""
    url_lower = url.lower()
    parsed = urlparse(url_lower)

    if not parsed.scheme.startswith("http"):
        return False
    if len(parsed.path) < 2:
        return False

    skip_extensions = {".css", ".js", ".png", ".jpg", ".gif", ".svg", ".ico", ".woff", ".pdf"}
    if any(parsed.path.endswith(ext) for ext in skip_extensions):
        return False

    skip_patterns = {"login", "logout", "cart", "checkout", "privacy", "terms", "cookie"}
    if any(p in url_lower for p in skip_patterns):
        return False

    if _is_education_relevant(url):
        return True

    domain = parsed.netloc
    if domain.endswith(".edu") or domain.endswith(".ac.uk"):
        return True

    return False


def _extract_exclusions(directives: list[EngineDirective]) -> set[str]:
    exclusions: set[str] = set(EXCLUDED_DOMAINS)
    for d in directives:
        if d.directive_type == "exclusion":
            val = d.directive_value
            if isinstance(val, dict):
                exclusions.update(val.get("domains", []))
    return exclusions


def _extract_steering_topics(directives: list[EngineDirective]) -> list[str]:
    topics: list[str] = []
    for d in directives:
        if d.directive_type == "steering":
            val = d.directive_value
            if isinstance(val, dict):
                topics.extend(val.get("topics", []))
    return topics
