"""
ModelManager — Model promotion, rollback, and registry management.

Handles the lifecycle of trained models: listing, promoting candidates
that pass fairness checks and improvement thresholds, rolling back to a
previous version, and auto-promoting after a successful training run.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import NotFoundException
from unipaith.models.matching import ModelRegistry
from unipaith.models.ml_loop import FairnessReport, TrainingRun

logger = logging.getLogger(__name__)


class ModelManager:
    """Registry-backed model lifecycle management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def get_active_model(self) -> ModelRegistry | None:
        """Return the currently active model, or None if no model is active."""
        result = await self.db.execute(
            select(ModelRegistry).where(ModelRegistry.is_active.is_(True)).limit(1)
        )
        return result.scalar_one_or_none()

    async def list_models(
        self,
        limit: int = 20,
        include_retired: bool = False,
    ) -> list[ModelRegistry]:
        """List models ordered by creation date, optionally including retired ones."""
        stmt = select(ModelRegistry).order_by(ModelRegistry.created_at.desc())

        if not include_retired:
            stmt = stmt.where(ModelRegistry.retired_at.is_(None))

        stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Promotion
    # ------------------------------------------------------------------

    async def promote_model(
        self,
        model_version: str,
        force: bool = False,
    ) -> dict:
        """
        Promote a candidate model to active.

        Non-force promotions require:
        1. All fairness reports to pass (if fairness_check_on_promotion is enabled)
        2. Test accuracy to beat the current active model by at least
           model_promotion_min_improvement

        Returns a dict describing the outcome.
        """
        # Load candidate
        result = await self.db.execute(
            select(ModelRegistry).where(ModelRegistry.model_version == model_version)
        )
        candidate = result.scalar_one_or_none()
        if candidate is None:
            raise NotFoundException(f"Model version '{model_version}' not found")

        # Fairness gate
        if not force and settings.fairness_check_on_promotion:
            fairness_ok = await self._check_fairness_passed(model_version)
            if not fairness_ok:
                logger.info("Promotion blocked for %s — fairness check failed", model_version)
                return {"success": False, "reason": "fairness_check_failed"}

        # Balanced improvement gate
        active_model = await self.get_active_model()
        if not force and active_model is not None:
            active_metrics = active_model.performance_metrics or {}
            candidate_metrics = candidate.performance_metrics or {}
            active_accuracy = float(active_metrics.get("accuracy", 0.0) or 0.0)
            candidate_accuracy = float(candidate_metrics.get("accuracy", 0.0) or 0.0)
            accuracy_improvement = candidate_accuracy - active_accuracy
            composite_improvement = self._composite_metric(
                candidate_metrics
            ) - self._composite_metric(active_metrics)

            # Safety: never allow a large accuracy degradation.
            if accuracy_improvement < -abs(settings.model_rollback_degradation_threshold):
                logger.info(
                    "Promotion blocked for %s — candidate degrades accuracy too much (%.4f)",
                    model_version,
                    accuracy_improvement,
                )
                return {
                    "success": False,
                    "reason": "safety_accuracy_degradation",
                    "active_accuracy": active_accuracy,
                    "candidate_accuracy": candidate_accuracy,
                    "accuracy_improvement": accuracy_improvement,
                    "max_degradation": -abs(settings.model_rollback_degradation_threshold),
                }

            passes_accuracy_gate = accuracy_improvement >= settings.model_promotion_min_improvement
            passes_composite_gate = (
                composite_improvement >= settings.model_promotion_min_composite_improvement
            )
            if not (passes_accuracy_gate or passes_composite_gate):
                logger.info(
                    "Promotion blocked for %s — balanced gates not met (acc=%.4f, composite=%.4f)",
                    model_version,
                    accuracy_improvement,
                    composite_improvement,
                )
                return {
                    "success": False,
                    "reason": "insufficient_balanced_improvement",
                    "active_accuracy": active_accuracy,
                    "candidate_accuracy": candidate_accuracy,
                    "accuracy_improvement": accuracy_improvement,
                    "composite_improvement": composite_improvement,
                    "required_accuracy": settings.model_promotion_min_improvement,
                    "required_composite": settings.model_promotion_min_composite_improvement,
                }

        # Deactivate current active model
        previous_version: str | None = None
        if active_model is not None:
            active_model.is_active = False
            previous_version = active_model.model_version

        # Activate candidate
        now = datetime.now(UTC)
        candidate.is_active = True
        candidate.promoted_at = now

        # Copy test_metrics into performance_metrics (ensure they're in sync)
        # performance_metrics was already set during training; this is a no-op
        # if already populated, but ensures consistency for manually registered models.
        if candidate.performance_metrics is None:
            candidate.performance_metrics = {}

        await self.db.flush()

        logger.info("Model %s promoted (previous: %s)", model_version, previous_version)

        return {
            "success": True,
            "promoted": model_version,
            "previous": previous_version,
        }

    # ------------------------------------------------------------------
    # Rollback
    # ------------------------------------------------------------------

    async def rollback_model(self) -> dict:
        """
        Roll back to the most recently promoted model before the current one.
        Retires the current active model.
        """
        active_model = await self.get_active_model()
        if active_model is None:
            raise NotFoundException("No active model to roll back from")

        # Find most recently promoted model before the current one
        result = await self.db.execute(
            select(ModelRegistry)
            .where(
                ModelRegistry.promoted_at.is_not(None),
                ModelRegistry.id != active_model.id,
                ModelRegistry.retired_at.is_(None),
            )
            .order_by(ModelRegistry.promoted_at.desc())
            .limit(1)
        )
        previous_model = result.scalar_one_or_none()

        if previous_model is None:
            raise NotFoundException("No previous model available for rollback")

        now = datetime.now(UTC)

        # Retire current
        active_model.is_active = False
        active_model.retired_at = now

        # Reactivate previous
        previous_model.is_active = True

        await self.db.flush()

        logger.info(
            "Rolled back from %s to %s",
            active_model.model_version,
            previous_model.model_version,
        )

        return {
            "success": True,
            "rolled_back_to": previous_model.model_version,
            "retired": active_model.model_version,
        }

    # ------------------------------------------------------------------
    # Auto-promotion
    # ------------------------------------------------------------------

    async def auto_promote_if_better(self, training_run_id) -> dict:
        """
        Load a completed TrainingRun and attempt non-force promotion of
        its resulting model.
        """
        result = await self.db.execute(select(TrainingRun).where(TrainingRun.id == training_run_id))
        run = result.scalar_one_or_none()
        if run is None:
            raise NotFoundException(f"Training run '{training_run_id}' not found")

        if not run.resulting_model_version:
            return {
                "success": False,
                "reason": "training_run_has_no_model",
            }

        return await self.promote_model(run.resulting_model_version)

    # ------------------------------------------------------------------
    # Fairness check
    # ------------------------------------------------------------------

    async def _check_fairness_passed(self, model_version: str) -> bool:
        """
        Return True if all FairnessReport records for this model version
        have passed=True. If no reports exist, return True (optimistic).
        """
        result = await self.db.execute(
            select(FairnessReport).where(FairnessReport.model_version == model_version)
        )
        reports = result.scalars().all()

        if not reports:
            return True

        return all(report.passed for report in reports)

    @staticmethod
    def _composite_metric(metrics: dict) -> float:
        """Weighted quality score used for balanced promotions."""
        accuracy = float(metrics.get("accuracy", 0.0) or 0.0)
        f1_score = float(metrics.get("f1", 0.0) or 0.0)
        roc_auc = float(metrics.get("roc_auc", metrics.get("auc", 0.0)) or 0.0)
        return (0.5 * accuracy) + (0.3 * f1_score) + (0.2 * roc_auc)
