import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    # Spec 55 §8 — liveness is enriched but the pinned contract is preserved.
    assert "environment" in data
    assert "uptime_s" in data


@pytest.mark.asyncio
async def test_readiness_checks_database(client: AsyncClient):
    """Spec 55 §8 — /ready runs a real SELECT 1 and reports each dependency.

    The test engine binds the same DATABASE_URL as the app's async_session, so the
    DB is up during tests → ready (200). The DB check is the only readiness gate;
    scheduler + cache are reported, not gated.
    """
    resp = await client.get("/api/v1/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    checks = data["checks"]
    assert checks["database"]["ok"] is True
    assert "latency_ms" in checks["database"]
    assert checks["database"]["pool_size"] >= 1
    # Scheduler + cache are reported but never gate readiness.
    assert checks["scheduler"]["ok"] is True
    assert checks["cache"]["ok"] is True
    assert checks["cache"]["backend"] == "memory"
    # todo 4.1 — the AI provider is reported (never gated). Tests run AI_MOCK_MODE,
    # so it's "ok" without a real key.
    assert checks["ai"]["ok"] is True
    assert checks["ai"]["provider"] == "anthropic"
    assert checks["ai"]["mock_mode"] is True


def test_ai_provider_configured_logic(monkeypatch):
    """todo 4.1 — the AI-key presence predicate behind the boot alarm + /ready."""
    from unipaith.config import settings
    from unipaith.core.security import ai_provider_configured

    # Mock mode: always considered configured (the deterministic stub needs no key).
    monkeypatch.setattr(settings, "ai_mock_mode", True)
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    assert ai_provider_configured() is True

    # Real mode + empty/whitespace key: the alarm condition.
    monkeypatch.setattr(settings, "ai_mock_mode", False)
    monkeypatch.setattr(settings, "anthropic_api_key", "   ")
    assert ai_provider_configured() is False

    # Real mode + a present key: configured.
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-ant-xxx")
    assert ai_provider_configured() is True


def test_ai_alarm_logs_when_key_missing(monkeypatch, caplog):
    """A missing key (outside mock mode) must raise a loud, greppable error — but
    NOT an exception (graceful degradation, never a boot failure)."""
    import logging

    from unipaith.config import settings
    from unipaith.core.security import warn_if_ai_provider_unconfigured

    monkeypatch.setattr(settings, "ai_mock_mode", False)
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    with caplog.at_level(logging.ERROR):
        warn_if_ai_provider_unconfigured()  # must not raise
    assert "ANTHROPIC_API_KEY is empty" in caplog.text

    # Configured (mock mode) → silent.
    caplog.clear()
    monkeypatch.setattr(settings, "ai_mock_mode", True)
    with caplog.at_level(logging.ERROR):
        warn_if_ai_provider_unconfigured()
    assert "ANTHROPIC_API_KEY is empty" not in caplog.text


@pytest.mark.asyncio
async def test_cors_headers(client: AsyncClient):
    resp = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" in resp.headers
