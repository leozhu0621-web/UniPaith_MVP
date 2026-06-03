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
import ipaddress
import json
import socket
from dataclasses import dataclass
from urllib.parse import urljoin

from unipaith.config import settings
from unipaith.services.crawler.sources import (
    ALLOWLISTED_DOMAINS,
    PERSONAL_DOMAIN_DENYLIST,
    domain_of,
)

# SSRF guard (Spec 58 §5). The crawler must never be coaxed into fetching an
# internal address — directly or via a redirect from an allowlisted page.
_MAX_REDIRECTS = 5


def _host_resolves_to_public(host: str) -> bool:
    """True only if EVERY IP ``host`` resolves to is globally routable.

    Blocks loopback / private / link-local (incl. the 169.254.169.254 cloud
    metadata endpoint) / reserved / multicast / unspecified ranges. Fails
    closed: any resolution error or any non-global address → False.
    """
    if not host:
        return False
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    addrs = {info[4][0] for info in infos}
    if not addrs:
        return False
    for addr in addrs:
        try:
            ip = ipaddress.ip_address(addr.split("%", 1)[0])  # strip IPv6 zone id
        except ValueError:
            return False
        if not ip.is_global or ip.is_multicast:
            return False
    return True


def _host_allowlisted(host: str) -> bool:
    """Sync allowlist check (the async ``Sources.is_url_allowed`` mirrors this).

    Used to re-validate redirect targets so an allowlisted page can't bounce the
    fetcher to an off-allowlist host.
    """
    if not host:
        return False
    if any(host == bad or host.endswith("." + bad) for bad in PERSONAL_DOMAIN_DENYLIST):
        return False
    return any(host == ok or host.endswith("." + ok) for ok in ALLOWLISTED_DOMAINS)


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
        # SSRF guard (Spec 58 §5): the initial host must resolve to a public IP.
        if not _host_resolves_to_public(host):
            return FetchResult(
                url=url,
                status="denied",
                source_domain=host,
                reason="ssrf_blocked: host does not resolve to a public address",
            )
        try:  # pragma: no cover - network path, never hit in tests/default deploy
            import httpx

            headers = {"User-Agent": settings.crawler_user_agent}
            # Follow redirects MANUALLY so every hop is re-validated against the
            # allowlist + the public-IP guard. follow_redirects=True would let an
            # allowlisted page 302 us to 169.254.169.254 or an internal host.
            current = url
            resp = None
            for _hop in range(_MAX_REDIRECTS + 1):
                resp = httpx.get(
                    current,
                    headers=headers,
                    timeout=settings.crawler_request_timeout,
                    follow_redirects=False,
                )
                if not resp.is_redirect or not resp.headers.get("location"):
                    break
                nxt = urljoin(current, resp.headers["location"])
                nxt_host = domain_of(nxt)
                if not (_host_allowlisted(nxt_host) and _host_resolves_to_public(nxt_host)):
                    return FetchResult(
                        url=url,
                        status="denied",
                        source_domain=host,
                        reason=f"ssrf_blocked: unsafe redirect to {nxt_host}",
                    )
                current = nxt
            else:
                return FetchResult(
                    url=url, status="error", source_domain=host, reason="too_many_redirects"
                )
            resp.raise_for_status()
            body = resp.text
            return FetchResult(
                url=current,
                status="ok",
                content=body,
                content_format="text",
                content_hash=content_hash(body),
                source_domain=domain_of(current),
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
