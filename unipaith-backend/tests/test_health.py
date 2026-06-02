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
