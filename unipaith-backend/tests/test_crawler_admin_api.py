"""Tests for Phase 5 – Crawler Admin API endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_admin_required(client: AsyncClient):
    """Unauthenticated request to admin endpoint should be rejected."""
    resp = await client.get("/api/v1/admin/crawler/dashboard")
    # Without auth the dependency fails: 401, 403, or 422 (validation error)
    assert resp.status_code in (401, 403, 422)


async def test_list_sources(admin_client: AsyncClient):
    resp = await admin_client.get("/api/v1/admin/crawler/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert "sources" in data
    assert "total" in data


async def test_review_stats(admin_client: AsyncClient):
    resp = await admin_client.get("/api/v1/admin/crawler/review/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
