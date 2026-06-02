"""Spec 56 — the /build/search transparency surface.

Asserts the payload shape, that the capability statuses are internally consistent,
that the backing-route buckets are resolved live from the running route table
(so the page can't claim a surface the app doesn't serve), that the saved-searches
table presence is read from the live metadata, and that the public endpoint serves
it unauthenticated.
"""

from __future__ import annotations

from httpx import AsyncClient

from unipaith.main import app
from unipaith.transparency.search import build_search

# asyncio_mode = "auto" (pyproject) runs the async tests without an explicit mark;
# the sync tests below run as plain functions.


def test_build_search_payload_shape_is_consistent():
    payload = build_search(app.routes)
    for key in (
        "the_bar",
        "summary",
        "capabilities",
        "build_tasks",
        "acceptance",
        "config_knobs",
        "routes",
        "open_questions",
    ):
        assert key in payload, f"missing {key}"

    s = payload["summary"]
    caps = payload["capabilities"]
    assert s["capability_count"] == len(caps)
    # The honest live/partial/planned split sums to the total.
    assert (
        s["capabilities_live"] + s["capabilities_partial"] + s["capabilities_planned"]
        == s["capability_count"]
    )
    assert s["build_task_count"] == len(payload["build_tasks"])
    assert s["acceptance_count"] == len(payload["acceptance"])
    # Every capability carries a valid status + the built/planned envelope.
    for c in caps:
        assert c["status"] in {"live", "partial", "planned"}
        assert isinstance(c["built"], list)
        assert isinstance(c["planned"], list)


def test_saved_search_capability_is_live_and_table_present():
    payload = build_search(app.routes)
    saved = next(c for c in payload["capabilities"] if c["key"] == "saved_search")
    # The net-new build ships live in this spec.
    assert saved["status"] == "live"
    assert payload["summary"]["saved_searches_table_present"] is True
    assert payload["saved_searches_table_present"] is True


def test_routes_resolved_live_from_route_table():
    payload = build_search(app.routes)
    routes = payload["routes"]
    # Saved-search endpoints are bucketed correctly (and not mis-counted as search).
    assert any("/saved-searches" in p for p in routes["saved_search"])
    assert all("/saved-searches" not in p for p in routes["search"])
    # The real program search endpoints are present.
    assert any("/search/programs" in p for p in routes["search"])
    # The Connect feed is backed.
    assert any("/connect" in p for p in routes["feed"])
    assert payload["summary"]["saved_search_route_count"] == len(routes["saved_search"])


def test_config_knobs_read_off_settings():
    payload = build_search(app.routes)
    names = {k["name"] for k in payload["config_knobs"]}
    assert "saved_search_alerts_enabled" in names
    assert "ai_discovery_query_v2_enabled" in names
    for k in payload["config_knobs"]:
        assert "section" in k


async def test_build_search_endpoint_is_public(client: AsyncClient):
    r = await client.get("/api/v1/build/search")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"]["capability_count"] >= 6


async def test_overview_includes_search_surface(client: AsyncClient):
    r = await client.get("/api/v1/build/overview")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "search" in body
    keys = {s["key"] for s in body["surfaces"]}
    assert "search" in keys
