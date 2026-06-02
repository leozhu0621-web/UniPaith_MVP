"""Spec 55 §3 — version-keyed read cache.

An in-process async TTL cache with hit/miss accounting and a ``cached()`` helper.
Correct for a single task; a shared backend (Redis / ElastiCache) makes it
cross-task — that infra is the planned half of §3 (see §11). The key carries a
**version** component so a ``profile_version`` / ``program_version`` bump
(spec 51 §7) busts the entry: we never serve stale past a bump.

The cache is dependency-free in dev/CI/prod-without-Redis (pure Python). When
``settings.redis_url`` is set *and* the ``redis`` package is importable, a
distributed backend can be wired in — ``stats()`` reports that readiness so the
``/goal/backend`` page tells the truth about which backend is actually live.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from unipaith.config import settings

# Sentinel so a legitimately-cached ``None`` is distinguishable from a miss.
_MISS: Any = object()


def redis_available() -> bool:
    """True when a distributed cache backend *could* be wired (config + lib).

    Read by ``stats()`` and the production-readiness surface. Does not import
    redis unless a URL is configured, so the soft dependency stays soft.
    """
    if not settings.redis_url:
        return False
    try:  # pragma: no cover - redis is not installed in dev/CI
        import redis.asyncio  # noqa: F401

        return True
    except Exception:
        return False


@dataclass
class _Entry:
    value: Any
    expires_at: float


class VersionedCache:
    """Async, TTL-bounded, version-keyed in-process cache.

    Thread-safe under asyncio via a single lock. Sizes itself by TTL only — hot
    read payloads (program/school detail, match results, the build surface) are
    small and short-lived, so there is no LRU cap; expired entries are reaped
    lazily on access.
    """

    def __init__(self) -> None:
        self._store: dict[str, _Entry] = {}
        self._lock = asyncio.Lock()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    @staticmethod
    def make_key(namespace: str, key: str, version: str | int = 1) -> str:
        """Compose a version-keyed cache key. A version bump busts the entry."""
        return f"{namespace}:v{version}:{key}"

    @staticmethod
    def _now() -> float:
        return time.monotonic()

    async def get(self, key: str) -> Any:
        """Return the cached value or ``_MISS``. Reaps the entry if expired."""
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.misses += 1
                return _MISS
            if entry.expires_at < self._now():
                self._store.pop(key, None)
                self.evictions += 1
                self.misses += 1
                return _MISS
            self.hits += 1
            return entry.value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        ttl = settings.cache_default_ttl if ttl is None else ttl
        async with self._lock:
            self._store[key] = _Entry(value, self._now() + max(1, ttl))

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any | Awaitable[Any]],
        ttl: int | None = None,
    ) -> Any:
        """Return the cached value, else compute it via ``factory`` and store it.

        ``factory`` may be sync or async. When caching is disabled the factory is
        always invoked and nothing is stored (so a flag flip is immediate).
        """
        if not settings.cache_enabled:
            return await _resolve(factory)
        cached = await self.get(key)
        if cached is not _MISS:
            return cached
        value = await _resolve(factory)
        await self.set(key, value, ttl)
        return value

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    def reset_stats(self) -> None:
        self.hits = self.misses = self.evictions = 0

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "backend": "memory",
            "enabled": settings.cache_enabled,
            "entries": len(self._store),
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "lookups": total,
            "hit_rate": round(self.hits / total, 4) if total else 0.0,
            "default_ttl_s": settings.cache_default_ttl,
            # Whether a shared backend could be wired right now (config + lib).
            "distributed_ready": redis_available(),
            "distributed_configured": bool(settings.redis_url),
        }


async def _resolve(factory: Callable[[], Any | Awaitable[Any]]) -> Any:
    result = factory()
    if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
        return await result
    return result


# Module-level singleton — one cache per process (per ECS task).
cache = VersionedCache()


async def cached(
    namespace: str,
    key: str,
    factory: Callable[[], Any | Awaitable[Any]],
    ttl: int | None = None,
    version: str | int = 1,
) -> Any:
    """Convenience wrapper: version-key + get-or-set against the process cache.

    Example::

        payload = await cached("build-overview", "v1", build_it, ttl=30)
    """
    full_key = VersionedCache.make_key(namespace, key, version)
    return await cache.get_or_set(full_key, factory, ttl)
