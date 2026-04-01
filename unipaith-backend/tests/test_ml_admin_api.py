"""Tests for ML Admin API endpoints — Phase 4 ML loop."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.matching import ModelRegistry
from unipaith.models.user import User


@pytest.mark.asyncio
async def test_admin_required(client: AsyncClient):
    """Unauthenticated GET /admin/ml/models -> 401 or 403."""
    resp = await client.get("/api/v1/admin/ml/models")
    # Without auth header -> 422 (missing header) or 403
    assert resp.status_code in (401, 403, 422)


@pytest.mark.asyncio
async def test_list_models(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    mock_admin_user: User,
):
    """admin_client GET /admin/ml/models -> 200."""
    # Persist the admin user first
    db_session.add(mock_admin_user)
    await db_session.commit()

    # Seed a model
    entry = ModelRegistry(
        model_version="v1.0-api-test",
        architecture="XGBClassifier",
        performance_metrics={"accuracy": 0.80},
        is_active=True,
        trained_at=datetime.now(timezone.utc),
    )
    db_session.add(entry)
    await db_session.commit()

    resp = await admin_client.get("/api/v1/admin/ml/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data


@pytest.mark.asyncio
async def test_outcome_stats(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    mock_admin_user: User,
):
    """admin_client GET /admin/ml/outcomes/stats -> 200."""
    db_session.add(mock_admin_user)
    await db_session.commit()

    resp = await admin_client.get("/api/v1/admin/ml/outcomes/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_outcomes" in data


@pytest.mark.asyncio
async def test_learning_kpis(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    mock_admin_user: User,
):
    """admin_client GET /admin/ml/kpis -> 200."""
    db_session.add(mock_admin_user)
    await db_session.commit()

    resp = await admin_client.get("/api/v1/admin/ml/kpis")
    assert resp.status_code == 200
    data = resp.json()
    assert "generated_at" in data
    assert "retrain_runs_24h" in data


@pytest.mark.asyncio
async def test_cycle_health(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    mock_admin_user: User,
):
    """admin_client GET /admin/ml/cycle/health -> 200."""
    db_session.add(mock_admin_user)
    await db_session.commit()

    resp = await admin_client.get("/api/v1/admin/ml/cycle/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "generated_at" in data
    assert "blocking_reasons" in data
    assert "readiness_score" in data


@pytest.mark.asyncio
async def test_learning_trends(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    mock_admin_user: User,
):
    """admin_client GET /admin/ml/trends -> 200."""
    db_session.add(mock_admin_user)
    await db_session.commit()

    resp = await admin_client.get("/api/v1/admin/ml/trends")
    assert resp.status_code == 200
    data = resp.json()
    assert "generated_at" in data
    assert "evals_per_day" in data
    assert "completed_trains_per_day" in data


@pytest.mark.asyncio
async def test_scheduler_smoke(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    mock_admin_user: User,
):
    """admin_client GET /admin/ml/scheduler/smoke -> 200."""
    db_session.add(mock_admin_user)
    await db_session.commit()

    resp = await admin_client.get("/api/v1/admin/ml/scheduler/smoke")
    assert resp.status_code == 200
    data = resp.json()
    assert "scheduler_effective_enabled" in data
    assert "expected_job_ids" in data


@pytest.mark.asyncio
async def test_architecture_trace_shape_and_stage_completeness(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    mock_admin_user: User,
):
    """admin_client GET /admin/ml/architecture-trace -> includes all expected stages."""
    db_session.add(mock_admin_user)
    await db_session.commit()

    resp = await admin_client.get("/api/v1/admin/ml/architecture-trace")
    assert resp.status_code == 200
    data = resp.json()
    assert "generated_at" in data
    assert isinstance(data.get("stages"), list)
    assert isinstance(data.get("runs"), list)

    stage_ids = {stage["stage_id"] for stage in data["stages"]}
    assert stage_ids == {
        "ingest",
        "understand",
        "match",
        "outcome",
        "evaluation",
        "training",
        "promotion",
    }
    for stage in data["stages"]:
        assert stage["source"]
        assert stage["status"] in {"ok", "warning", "error", "idle"}


@pytest.mark.asyncio
async def test_architecture_trace_include_runs_toggle(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    mock_admin_user: User,
):
    """architecture-trace should support include_runs flag and limit."""
    db_session.add(mock_admin_user)
    await db_session.commit()

    resp_no_runs = await admin_client.get(
        "/api/v1/admin/ml/architecture-trace",
        params={"include_runs": False},
    )
    assert resp_no_runs.status_code == 200
    data_no_runs = resp_no_runs.json()
    assert data_no_runs["runs"] == []

    resp_with_runs = await admin_client.get(
        "/api/v1/admin/ml/architecture-trace",
        params={"include_runs": True, "limit": 3},
    )
    assert resp_with_runs.status_code == 200
    data_with_runs = resp_with_runs.json()
    assert isinstance(data_with_runs["runs"], list)
    assert len(data_with_runs["runs"]) <= 3
