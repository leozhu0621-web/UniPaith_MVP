"""Spec 55 §3 — the version-keyed read cache primitive."""

from __future__ import annotations

import pytest

from unipaith.core.cache import VersionedCache, cached


@pytest.mark.asyncio
async def test_get_or_set_caches_and_counts():
    c = VersionedCache()
    calls = {"n": 0}

    def factory():
        calls["n"] += 1
        return {"v": calls["n"]}

    first = await c.get_or_set("k", factory, ttl=60)
    second = await c.get_or_set("k", factory, ttl=60)
    assert first == second == {"v": 1}  # factory ran once
    assert calls["n"] == 1
    stats = c.stats()
    assert stats["hits"] == 1 and stats["misses"] == 1
    assert stats["hit_rate"] == 0.5
    assert stats["backend"] == "memory"


@pytest.mark.asyncio
async def test_async_factory_is_awaited():
    c = VersionedCache()

    async def factory():
        return 42

    assert await c.get_or_set("k", factory) == 42


@pytest.mark.asyncio
async def test_version_bump_busts_the_key():
    """A version bump (profile_version / program_version, 51 §7) must miss."""
    c = VersionedCache()
    seen = []

    async def make(tag):
        seen.append(tag)
        return tag

    k1 = VersionedCache.make_key("program", "p1", version=1)
    k2 = VersionedCache.make_key("program", "p1", version=2)
    assert k1 != k2
    await c.get_or_set(k1, lambda: make("v1"))
    await c.get_or_set(k1, lambda: make("v1"))  # hit
    out = await c.get_or_set(k2, lambda: make("v2"))  # new version → miss
    assert out == "v2"
    assert seen == ["v1", "v2"]


@pytest.mark.asyncio
async def test_caches_none_without_thrashing():
    """A legitimately-cached None is a hit, not a perpetual miss (sentinel)."""
    c = VersionedCache()
    calls = {"n": 0}

    def factory():
        calls["n"] += 1
        return None

    await c.get_or_set("k", factory, ttl=60)
    await c.get_or_set("k", factory, ttl=60)
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_disabled_cache_bypasses(monkeypatch):
    from unipaith.config import settings

    monkeypatch.setattr(settings, "cache_enabled", False)
    c = VersionedCache()
    calls = {"n": 0}

    def factory():
        calls["n"] += 1
        return 1

    await c.get_or_set("k", factory)
    await c.get_or_set("k", factory)
    assert calls["n"] == 2  # no caching while disabled


@pytest.mark.asyncio
async def test_cached_helper_uses_namespace_and_version():
    out = await cached("test-ns", "key", lambda: "ok", ttl=5, version=1)
    assert out == "ok"
