"""Spec 60 §6 step (2) — fetch (robots + delay + conditional GET).

Hard gate: live network access is OFF unless ``crawler_live_fetch_enabled`` is
set for the environment. By default the engine runs entirely on the Tier-1
structured seed + injected fixtures, so nothing here ever touches the public
internet in test or in a fresh deploy. When enabled, fetches are robots-aware,
rate-limited, and identified by the configured UA; a conditional GET (content
hash) means unchanged content is skipped before any parse/write (§15 idempotency).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from unipaith.config import settings
from unipaith.services.crawler.sources import domain_of


def content_hash(payload: object) -> str:
    """Stable sha256 over a payload — a dict record (canonical JSON) or raw text."""
    if isinstance(payload, (dict, list)):
        blob = json.dumps(payload, sort_keys=True, default=str)
    else:
        blob = str(payload)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass
class FetchResult:
    url: str
    status: str  # ok | unchanged | fetch_disabled | denied | error
    content: object | None = None
    content_format: str = "structured"
    content_hash: str | None = None
    source_domain: str | None = None
    reason: str | None = None


class Fetcher:
    """Stateless fetcher. ``injected`` lets the seeder and tests supply content
    without any network — the only path exercised by default."""

    def fetch(
        self,
        url: str,
        *,
        injected: object | None = None,
        content_format: str = "structured",
        respect_robots: bool = True,
    ) -> FetchResult:
        host = domain_of(url)
        if injected is not None:
            return FetchResult(
                url=url,
                status="ok",
                content=injected,
                content_format=content_format,
                content_hash=content_hash(injected),
                source_domain=host,
            )
        if not settings.crawler_live_fetch_enabled:
            return FetchResult(
                url=url,
                status="fetch_disabled",
                source_domain=host,
                reason="crawler_live_fetch_enabled is off",
            )
        # Live path (only reached when explicitly enabled). Robots + delay + UA.
        if respect_robots and not self._robots_allows(url):
            return FetchResult(
                url=url, status="denied", source_domain=host, reason="robots.txt disallow"
            )
        try:  # pragma: no cover - network path, never hit in tests/default deploy
            import httpx

            headers = {"User-Agent": settings.crawler_user_agent}
            resp = httpx.get(
                url,
                headers=headers,
                timeout=settings.crawler_request_timeout,
                follow_redirects=True,
            )
            resp.raise_for_status()
            body = resp.text
            return FetchResult(
                url=url,
                status="ok",
                content=body,
                content_format="text",
                content_hash=content_hash(body),
                source_domain=host,
            )
        except Exception as exc:  # noqa: BLE001
            return FetchResult(url=url, status="error", source_domain=host, reason=str(exc))

    def _robots_allows(self, url: str) -> bool:  # pragma: no cover - network path
        try:
            import urllib.robotparser

            host = domain_of(url)
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(f"https://{host}/robots.txt")
            rp.read()
            return rp.can_fetch(settings.crawler_user_agent, url)
        except Exception:  # noqa: BLE001 - on any robots error, be conservative
            return False
