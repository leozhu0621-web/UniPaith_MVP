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
