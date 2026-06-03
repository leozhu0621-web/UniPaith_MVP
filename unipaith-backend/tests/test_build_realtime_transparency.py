"""Spec 57 — the /build/realtime transparency surface.

Asserts the payload shape, that capability statuses are internally consistent,
that the transport routes (SSE /me/stream + WS /ws/messages) are resolved live
from the running route table, that the catalog event-type count + broker backend
are read from the running registry/broker, and that the public endpoint serves it
unauthenticated and is wired into the overview hub.
"""

from __future__ import annotations

from httpx import AsyncClient

from unipaith.main import app
from unipaith.transparency.realtime import build_realtime


def test_build_realtime_payload_shape_is_consistent():
    payload = build_realtime(app.routes)
    for key in (
        "the_bar",
        "summary",
        "capabilities",
        "build_tasks",
        "acceptance",
        "config_knobs",
        "routes",
        "catalog",
        "broker",
        "open_questions",
    ):
        assert key in payload, f"missing {key}"

    s = payload["summary"]
    caps = payload["capabilities"]
    assert s["capability_count"] == len(caps)
    assert (
        s["capabilities_live"] + s["capabilities_partial"] + s["capabilities_planned"]
        == s["capability_count"]
    )
    assert s["build_task_count"] == len(payload["build_tasks"])
    assert s["acceptance_count"] == len(payload["acceptance"])
    for c in caps:
        assert c["status"] in {"live", "partial", "planned"}
        assert isinstance(c["built"], list)
        assert isinstance(c["planned"], list)


def test_transport_routes_resolved_live_from_route_table():
    payload = build_realtime(app.routes)
    routes = payload["routes"]
    # The SSE bell stream and the WS messaging endpoint are actually served.
    assert any(p.endswith("/me/stream") for p in routes["sse"])
    assert any("/ws/messages" in p for p in routes["ws"])
    # The notification center endpoints back the panel.
    assert any("/notifications" in p for p in routes["notifications"])
    assert payload["summary"]["sse_route_count"] == len(routes["sse"])
    assert payload["summary"]["ws_route_count"] == len(routes["ws"])


def test_catalog_and_broker_read_live():
    payload = build_realtime(app.routes)
    s = payload["summary"]
    # Catalog count matches the running registry.
    from unipaith.services import notification_catalog as catalog

    assert s["event_type_count"] == catalog.event_type_count()
    assert len(payload["catalog"]) == s["event_type_count"]
    # Broker backend is the live posture (memory without Redis configured in CI).
    assert s["broker_backend"] in {"memory", "redis"}
    assert payload["broker"]["backend"] == s["broker_backend"]
    # Idempotency column is wired (model has event_id).
    assert s["idempotency_wired"] is True


def test_config_knobs_read_off_settings():
    payload = build_realtime(app.routes)
    names = {k["name"] for k in payload["config_knobs"]}
    assert "realtime_enabled" in names
    assert "notification_digest_enabled" in names
    assert "web_push_enabled" in names
    for k in payload["config_knobs"]:
        assert "section" in k


def test_sse_and_ws_capabilities_live():
    payload = build_realtime(app.routes)
    by_key = {c["key"]: c for c in payload["capabilities"]}
    assert by_key["sse"]["status"] == "live"
    assert by_key["ws"]["status"] == "live"
    assert by_key["catalog"]["status"] == "live"
    assert by_key["center"]["status"] == "live"


async def test_build_realtime_endpoint_is_public(client: AsyncClient):
    r = await client.get("/api/v1/build/realtime")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["summary"]["capability_count"] >= 6
    assert body["summary"]["event_type_count"] >= 10


async def test_overview_includes_realtime_surface(client: AsyncClient):
    r = await client.get("/api/v1/build/overview")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "realtime" in body
    keys = {s["key"] for s in body["surfaces"]}
    assert "realtime" in keys
    surface = next(s for s in body["surfaces"] if s["key"] == "realtime")
    assert surface["path"] == "/goal/realtime"
    assert surface["spec"] == "57"
