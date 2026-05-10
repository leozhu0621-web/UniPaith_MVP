"""Phase D — ML model-state registry loader.

Tiny accessor over `model_registry` for the calibrator (D2) and the
learned reranker (D3). Both kinds of state persist as JSONB on the
`hyperparameters` column of a row keyed on a fixed `model_version`
string.

Cold-start contract: when no row exists, return an unfitted state.
The matcher falls through to identity behavior — raw confidence
shown as-is, IdentityReranker preserves order. The first time a
trainer (D2 fit / D3 train) writes a state, this loader picks it up
on the next request.

Why this lives in its own module
--------------------------------
- Both `MatchService` and the offline trainers want to read the same
  active state. Keeping the keys + lookups in one place prevents
  drift.
- Re-using `model_registry` instead of new tables matches the existing
  ML loop architecture and avoids alembic churn.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.matching import ModelRegistry
from unipaith.services.confidence_calibrator import CalibratorState
from unipaith.services.reranker import RerankerState

logger = logging.getLogger(__name__)

# Fixed registry keys. One row per kind; trainers update in place. The
# row's `is_active` flag gates whether the state is considered "live."
CALIBRATOR_KEY = "confidence_calibrator"
RERANKER_KEY = "reranker"


# ── Read paths ──────────────────────────────────────────────────────────────


async def load_calibrator_state(db: AsyncSession) -> CalibratorState:
    """Read the active calibrator state from `model_registry`.

    Cold start (no row, inactive row, or empty hyperparameters): returns
    an unfitted CalibratorState. `apply_calibrator` is the identity in
    that case, so raw confidence flows through unchanged.
    """
    row = await db.scalar(
        select(ModelRegistry).where(
            ModelRegistry.model_version == CALIBRATOR_KEY,
            ModelRegistry.is_active.is_(True),
        )
    )
    if row is None:
        return CalibratorState()
    return CalibratorState.from_dict(row.hyperparameters or None)


async def load_reranker_state(db: AsyncSession) -> RerankerState:
    """Read the active learned-reranker state from `model_registry`.

    Cold start: returns an unfitted RerankerState. `get_reranker` then
    returns IdentityReranker, which preserves matcher order.
    """
    row = await db.scalar(
        select(ModelRegistry).where(
            ModelRegistry.model_version == RERANKER_KEY,
            ModelRegistry.is_active.is_(True),
        )
    )
    if row is None:
        return RerankerState()
    return RerankerState.from_dict(row.hyperparameters or None)


# ── Write paths (used by D2/D3 trainers) ───────────────────────────────────


async def save_calibrator_state(db: AsyncSession, state: CalibratorState) -> ModelRegistry:
    """Upsert the active calibrator state. Used by the D2 fit job and
    by tests that want to flip state in-flight.
    """
    return await _upsert_state(db, CALIBRATOR_KEY, state.to_dict())


async def save_reranker_state(db: AsyncSession, state: RerankerState) -> ModelRegistry:
    """Upsert the active reranker state."""
    return await _upsert_state(db, RERANKER_KEY, state.to_dict())


async def _upsert_state(
    db: AsyncSession, key: str, hyperparameters: dict[str, Any]
) -> ModelRegistry:
    row = await db.scalar(select(ModelRegistry).where(ModelRegistry.model_version == key))
    if row is None:
        row = ModelRegistry(
            model_version=key,
            architecture=key,
            hyperparameters=hyperparameters,
            is_active=True,
        )
        db.add(row)
    else:
        row.hyperparameters = hyperparameters
        row.is_active = True
    await db.flush()
    return row
