"""/messages/stream routes through UniAgentHost when the flag is on, and falls
back to the in-app orchestrator when host setup fails."""

import pytest

import unipaith.api.discovery as disc_api
from tests._uni_helpers import ensure_profile
from tests.test_uni_agent_host import _FakeAgentClient
from unipaith.config import settings


async def _make_session(student_client) -> str:
    s = await student_client.post("/api/v1/students/me/discovery/sessions/unified")
    assert s.status_code in (200, 201), s.text
    return s.json()["id"]


@pytest.mark.asyncio
async def test_stream_endpoint_uses_host_when_flag_on(
    student_client, db_session, mock_student_user, monkeypatch
):
    await ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_uni_managed_agent_v1", True)

    real_host = disc_api.UniAgentHost

    def _host_with_fake(db, client=None):
        return real_host(db, client=_FakeAgentClient())

    monkeypatch.setattr(disc_api, "UniAgentHost", _host_with_fake)

    sid = await _make_session(student_client)
    resp = await student_client.post(
        f"/api/v1/students/me/discovery/sessions/{sid}/messages/stream",
        json={"role": "student", "content": "hello"},
    )
    assert resp.status_code == 200
    assert "assistant_message" in resp.text
    assert "Where are you headed" in resp.text  # streamed from the fake agent


@pytest.mark.asyncio
async def test_opener_serves_static_greeting_when_flag_off(
    student_client, db_session, mock_student_user, monkeypatch
):
    await ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_uni_managed_agent_v1", False)
    resp = await student_client.post("/api/v1/students/me/discovery/opener/stream")
    assert resp.status_code == 200
    assert "assistant_message" in resp.text
    assert "I'm Uni" in resp.text
    assert "student_message" not in resp.text  # Uni speaks first — no student turn


@pytest.mark.asyncio
async def test_opener_uses_host_when_flag_on(
    student_client, db_session, mock_student_user, monkeypatch
):
    await ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_uni_managed_agent_v1", True)
    real_host = disc_api.UniAgentHost

    def _host_with_fake(db, client=None):
        return real_host(db, client=_FakeAgentClient())

    monkeypatch.setattr(disc_api, "UniAgentHost", _host_with_fake)
    resp = await student_client.post("/api/v1/students/me/discovery/opener/stream")
    assert resp.status_code == 200
    assert "assistant_message" in resp.text
    assert "Where are you headed" in resp.text  # streamed from the fake agent
    assert "student_message" not in resp.text


@pytest.mark.asyncio
async def test_stream_endpoint_falls_back_to_orchestrator_on_setup_failure(
    student_client, db_session, mock_student_user, monkeypatch
):
    await ensure_profile(db_session, mock_student_user)
    monkeypatch.setattr(settings, "ai_uni_managed_agent_v1", True)

    real_host = disc_api.UniAgentHost

    def _host_that_fails(db, client=None):
        return real_host(db, client=_FakeAgentClient(raise_on_create=True))

    monkeypatch.setattr(disc_api, "UniAgentHost", _host_that_fails)

    sid = await _make_session(student_client)
    resp = await student_client.post(
        f"/api/v1/students/me/discovery/sessions/{sid}/messages/stream",
        json={"role": "student", "content": "hello"},
    )
    # Never a 5xx — the orchestrator served the turn instead.
    assert resp.status_code == 200
    assert "assistant_message" in resp.text
