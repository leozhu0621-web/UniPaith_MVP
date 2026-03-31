"""
Model Evaluator — compares predictions against actual outcomes to produce
accuracy, precision, recall, F1, AUC-ROC, confusion matrices, per-tier
metrics, and determines whether retraining should be triggered.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException
from unipaith.models.matching import ModelRegistry, PredictionLog
from unipaith.models.ml_loop import EvaluationRun, OutcomeRecord

logger = logging.getLogger(__name__)

# Outcomes considered "positive" for binary classification
_POSITIVE_OUTCOMES = {"admitted", "enrolled"}
_NEGATIVE_OUTCOMES = {"rejected", "declined", "withdrawn"}


class ModelEvaluator:
    """Evaluates model performance against collected ground-truth outcomes."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def run_evaluation(
        self,
        model_version: str | None = None,
        evaluation_type: str = "scheduled",
    ) -> EvaluationRun:
        """Run a full model evaluation.

        Args:
            model_version: Specific version to evaluate, or None for the
                currently active model.
            evaluation_type: One of 'scheduled', 'manual', 'promotion'.

        Returns:
            The persisted EvaluationRun record.

        Raises:
            BadRequestException: if insufficient labeled outcomes exist.
            NotFoundException: if the specified model version does not exist.
        """
        started_at = datetime.now(UTC)

        if model_version is None:
            model_version = await self._get_active_model_version()

        outcomes = await self._collect_labeled_outcomes(model_version)

        if len(outcomes) < settings.eval_min_predictions_for_eval:
            raise BadRequestException(
                f"Insufficient labeled outcomes for evaluation: "
                f"{len(outcomes)} < {settings.eval_min_predictions_for_eval} required"
            )

        metrics = self._compute_metrics(outcomes)
        confusion = self._compute_confusion_matrix(outcomes)
        per_tier = self._compute_per_tier_metrics(outcomes)
        should_retrain = self._should_retrain(metrics)

        evaluation = EvaluationRun(
            model_version=model_version,
            evaluation_type=evaluation_type,
            dataset_size=len(outcomes),
            metrics=metrics,
            confusion_matrix=confusion,
            per_tier_metrics=per_tier,
            drift_detected=False,
            retraining_triggered=should_retrain,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )
        self.db.add(evaluation)
        await self.db.flush()

        logger.info(
            "Evaluation complete for %s: accuracy=%.4f, retrain=%s, n=%d",
            model_version,
            metrics.get("accuracy", 0),
            should_retrain,
            len(outcomes),
        )
        return evaluation

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    async def _collect_labeled_outcomes(self, model_version: str) -> list[dict]:
        """Collect outcomes joined with predictions for a model version.

        Returns list of dicts with: predicted_score, predicted_tier,
        actual_outcome, outcome_confidence, student_id, program_id.
        """
        stmt = (
            select(
                OutcomeRecord.predicted_score,
                OutcomeRecord.predicted_tier,
                OutcomeRecord.actual_outcome,
                OutcomeRecord.outcome_confidence,
                OutcomeRecord.student_id,
                OutcomeRecord.program_id,
            )
            .join(
                PredictionLog,
                OutcomeRecord.prediction_log_id == PredictionLog.id,
            )
            .where(PredictionLog.model_version == model_version)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "predicted_score": float(row.predicted_score),
                "predicted_tier": row.predicted_tier,
                "actual_outcome": row.actual_outcome,
                "outcome_confidence": float(row.outcome_confidence),
                "student_id": str(row.student_id),
                "program_id": str(row.program_id),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Metric computation (pure, no DB access)
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_metrics(outcomes: list[dict]) -> dict:
        """Compute binary classification metrics.

        Positive class: admitted, enrolled
        Negative class: rejected, declined, withdrawn

        Returns dict with accuracy, precision, recall, f1, auc_roc.
        """
        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )

        y_true: list[int] = []
        y_pred: list[int] = []
        y_scores: list[float] = []

        for o in outcomes:
            actual = o["actual_outcome"]
            # Skip outcomes we cannot classify (e.g. waitlisted, deferred)
            if actual not in _POSITIVE_OUTCOMES and actual not in _NEGATIVE_OUTCOMES:
                continue

            true_label = 1 if actual in _POSITIVE_OUTCOMES else 0
            # Predicted tier 1 = strongest match -> predict positive
            pred_label = 1 if o["predicted_tier"] <= 1 else 0

            y_true.append(true_label)
            y_pred.append(pred_label)
            y_scores.append(o["predicted_score"])

        if len(y_true) == 0:
            return {
                "accuracy": 0.0,
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0,
                "auc_roc": 0.5,
                "n_classified": 0,
            }

        accuracy = float(accuracy_score(y_true, y_pred))
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))

        # AUC-ROC: handle edge case where all labels are the same class
        unique_labels = set(y_true)
        if len(unique_labels) < 2:
            auc = 0.5
        else:
            try:
                auc = float(roc_auc_score(y_true, y_scores))
            except ValueError:
                auc = 0.5

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "auc_roc": auc,
            "n_classified": len(y_true),
        }

    @staticmethod
    def _compute_confusion_matrix(outcomes: list[dict]) -> dict:
        """Build a confusion matrix of predicted_tier vs actual_outcome.

        Returns a nested dict: {predicted_tier: {actual_outcome: count}}.
        """
        matrix: dict[int, dict[str, int]] = {}
        for o in outcomes:
            tier = o["predicted_tier"]
            actual = o["actual_outcome"]
            if tier not in matrix:
                matrix[tier] = {}
            matrix[tier][actual] = matrix[tier].get(actual, 0) + 1

        # Convert keys to strings for JSON serialization
        return {str(tier): counts for tier, counts in sorted(matrix.items())}

    @staticmethod
    def _compute_per_tier_metrics(outcomes: list[dict]) -> dict:
        """Compute accuracy within each predicted tier (1, 2, 3).

        For each tier, accuracy is defined as the fraction of outcomes in
        that tier that are considered "correct" for the tier level:
        - Tier 1: positive outcomes (admitted/enrolled)
        - Tier 2: any outcome is acceptable (we measure positive rate)
        - Tier 3: negative outcomes (rejected/declined/withdrawn)
        """
        tier_groups: dict[int, list[dict]] = {}
        for o in outcomes:
            tier = o["predicted_tier"]
            if tier not in tier_groups:
                tier_groups[tier] = []
            tier_groups[tier].append(o)

        per_tier: dict[str, dict] = {}
        for tier in sorted(tier_groups.keys()):
            group = tier_groups[tier]
            total = len(group)
            positive_count = sum(1 for o in group if o["actual_outcome"] in _POSITIVE_OUTCOMES)
            negative_count = sum(1 for o in group if o["actual_outcome"] in _NEGATIVE_OUTCOMES)

            if tier == 1:
                correct = positive_count
            elif tier == 3:
                correct = negative_count
            else:
                # For tier 2 (middle), measure balanced rate
                correct = total  # all outcomes are "expected" for middle tier

            accuracy = correct / total if total > 0 else 0.0

            per_tier[str(tier)] = {
                "total": total,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "accuracy": round(accuracy, 4),
            }

        return per_tier

    @staticmethod
    def _should_retrain(metrics: dict) -> bool:
        """Determine if retraining should be triggered based on accuracy."""
        accuracy = metrics.get("accuracy", 0.0)
        return accuracy < settings.eval_accuracy_threshold

    # ------------------------------------------------------------------
    # Model registry helpers
    # ------------------------------------------------------------------

    async def _get_active_model_version(self) -> str:
        """Get the currently active model version from the registry.

        Returns 'v1.0-mvp' as fallback if no active model is registered.
        """
        stmt = select(ModelRegistry.model_version).where(ModelRegistry.is_active.is_(True))
        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        if version is None:
            logger.warning("No active model found in registry, using default 'v1.0-mvp'")
            return "v1.0-mvp"
        return version
