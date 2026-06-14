"""UniPaith MCP data API — JSON-RPC over /mcp, single bearer key, all-data."""

import json

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.config import settings

_KEY = "test-mcp-key-123"
_AUTH = {"Authorization": f"Bearer {_KEY}"}


def _rpc(method, params=None, mid=1):
    msg = {"jsonrpc": "2.0", "method": method}
    if mid is not None:
        msg["id"] = mid
    if params is not None:
        msg["params"] = params
    return msg


def _tool_payload(resp):
    """Pull the JSON the tool returned out of the MCP content envelope."""
    body = resp.json()
    return json.loads(body["result"]["content"][0]["text"])


@pytest.mark.asyncio
async def test_mcp_requires_bearer_key(client, monkeypatch):
    monkeypatch.setattr(settings, "unipaith_mcp_api_key", _KEY)
    resp = await client.post("/mcp", json=_rpc("initialize"))
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_mcp_initialize_and_tools_list(client, monkeypatch):
    monkeypatch.setattr(settings, "unipaith_mcp_api_key", _KEY)
    init = await client.post(
        "/mcp", json=_rpc("initialize", {"protocolVersion": "2025-06-18"}), headers=_AUTH
    )
    assert init.status_code == 200
    r = init.json()["result"]
    assert r["protocolVersion"] == "2025-06-18"
    assert "tools" in r["capabilities"]
    assert r["serverInfo"]["name"] == "unipaith"

    listed = await client.post("/mcp", json=_rpc("tools/list", mid=2), headers=_AUTH)
    names = {t["name"] for t in listed.json()["result"]["tools"]}
    assert names == {
        "get_profile",
        "create_profile",
        "save_signals",
        "get_matches",
        "search_programs",
        "generate_strategy",
    }


@pytest.mark.asyncio
async def test_mcp_notification_returns_202(client, monkeypatch):
    monkeypatch.setattr(settings, "unipaith_mcp_api_key", _KEY)
    resp = await client.post(
        "/mcp", json=_rpc("notifications/initialized", mid=None), headers=_AUTH
    )
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_mcp_get_profile_by_student_id(client, db_session, mock_student_user, monkeypatch):
    monkeypatch.setattr(settings, "unipaith_mcp_api_key", _KEY)
    profile = await ensure_profile(db_session, mock_student_user)
    resp = await client.post(
        "/mcp",
        json=_rpc(
            "tools/call", {"name": "get_profile", "arguments": {"student_id": str(profile.id)}}
        ),
        headers=_AUTH,
    )
    assert resp.status_code == 200
    out = _tool_payload(resp)
    assert "completion" in out  # snapshot shape — all-data read by student id


@pytest.mark.asyncio
async def test_mcp_search_programs_no_student(client, monkeypatch):
    monkeypatch.setattr(settings, "unipaith_mcp_api_key", _KEY)
    resp = await client.post(
        "/mcp",
        json=_rpc(
            "tools/call", {"name": "search_programs", "arguments": {"query": "data science"}}
        ),
        headers=_AUTH,
    )
    out = _tool_payload(resp)
    assert "programs" in out and "total" in out


@pytest.mark.asyncio
async def test_mcp_unknown_student_id(client, monkeypatch):
    monkeypatch.setattr(settings, "unipaith_mcp_api_key", _KEY)
    resp = await client.post(
        "/mcp",
        json=_rpc("tools/call", {"name": "get_profile", "arguments": {"student_id": "not-a-uuid"}}),
        headers=_AUTH,
    )
    out = _tool_payload(resp)
    assert "student_not_found" in out["error"]
