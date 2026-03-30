"""Tests for ModelManager — Phase 4 ML loop."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ml.model_manager import ModelManager
from unipaith.models.matching import ModelRegistry


async def _create_model(
    db: AsyncSession,
    version: str,
    is_active: bool = False,
    accuracy: float = 0.80,
    promoted_at: datetime | None = None,
) -> ModelRegistry:
    entry = ModelRegistry(
        model_version=version,
        architecture="XGBClassifier",
        hyperparameters={"n_estimators": 100},
        performance_metrics={"accuracy": accuracy},
        is_active=is_active,
        trained_at=datetime.now(timezone.utc),
        promoted_at=promoted_at,
    )
    db.add(entry)
    await db.flush()
    return entry


@pytest.mark.asyncio
async def test_promote_model(db_session: AsyncSession):
    """Create a ModelRegistry entry, promote, verify is_active=True."""
    entry = await _create_model(db_session, "v2.0-test", is_active=False, accuracy=0.90)
    await db_session.commit()

    manager = ModelManager(db_session)
    result = await manager.promote_model("v2.0-test", force=True)
    await db_session.commit()

    assert result["success"] is True
    assert result["promoted"] == "v2.0-test"

    # Reload
    refreshed = await db_session.get(ModelRegistry, entry.id)
    assert refreshed.is_active is True


@pytest.mark.asyncio
async def test_rollback(db_session: AsyncSession):
    """Promote, then rollback, verify previous model reactivated."""
    # Create two models; promote both in sequence
    prev = await _create_model(
        db_session, "v1.0-prev", is_active=False, accuracy=0.75,
        promoted_at=datetime.now(timezone.utc),
    )
    current = await _create_model(
        db_session, "v2.0-current", is_active=True, accuracy=0.85,
        promoted_at=datetime.now(timezone.utc),
    )
    await db_session.commit()

    manager = ModelManager(db_session)
    result = await manager.rollback_model()
    await db_session.commit()

    assert result["success"] is True
    assert result["rolled_back_to"] == "v1.0-prev"
    assert result["retired"] == "v2.0-current"

    # Verify states
    prev_refreshed = await db_session.get(ModelRegistry, prev.id)
    current_refreshed = await db_session.get(ModelRegistry, current.id)
    assert prev_refreshed.is_active is True
    assert current_refreshed.is_active is False
    assert current_refreshed.retired_at is not None


@pytest.mark.asyncio
async def test_list_models(db_session: AsyncSession):
    """Create 2 entries, verify list returns them."""
    await _create_model(db_session, "v1.0-a", is_active=False)
    await _create_model(db_session, "v2.0-b", is_active=True)
    await db_session.commit()

    manager = ModelManager(db_session)
    models = await manager.list_models()

    assert len(models) >= 2
    versions = {m.model_version for m in models}
    assert "v1.0-a" in versions
    assert "v2.0-b" in versions
