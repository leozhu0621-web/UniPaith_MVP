"""
MLOrchestrator — Coordinates the full self-improving ML cycle.

Runs evaluation, drift detection, retraining, fairness checking, and
model promotion in sequence.  Designed to be called by the admin API
or a scheduled job.  Never raises — always returns partial results.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ml.drift_detector import DriftDetector
from unipaith.ml.evaluator import ModelEvaluator
from unipaith.ml.fairness import FairnessChecker
from unipaith.ml.model_manager import ModelManager
from unipaith.ml.outcome_collector import OutcomeCollector
from unipaith.ml.trainer import ModelTrainer

logger = logging.getLogger(__name__)


class MLOrchestrator:
    """End-to-end ML loop coordinator."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.evaluator = ModelEvaluator(db)
        self.drift_detector = DriftDetector(db)
        self.fairness_checker = FairnessChecker(db)
        self.trainer = ModelTrainer(db)
        self.model_manager = ModelManager(db)

    # ------------------------------------------------------------------
    # Full cycle
    # ------------------------------------------------------------------

    async def run_full_cycle(self, triggered_by: str = "scheduled") -> dict[str, Any]:
        """Run the complete ML improvement cycle.

        Steps:
        1. Evaluate current model
        2. Check for data / prediction drift
        3. Retrain if evaluation or drift warrants it
        4. Run fairness checks on the new model
        5. Auto-promote if the new model is better

        Never raises — partial results are returned on failure.
        """
        started_at = datetime.now(UTC)
        result: dict[str, Any] = {
            "started_at": started_at.isoformat(),
            "completed_at": None,
            "evaluation": None,
            "drift": None,
            "training": None,
            "fairness": None,
            "promotion": None,
        }

        # --- Step 1: Evaluation ---
        try:
            eval_run = await self.evaluator.run_evaluation(
                evaluation_type="triggered",
            )
            result["evaluation"] = {
                "id": str(eval_run.id),
                "model_version": eval_run.model_version,
                "dataset_size": eval_run.dataset_size,
                "metrics": eval_run.metrics,
                "retraining_triggered": eval_run.retraining_triggered,
                "drift_detected": eval_run.drift_detected,
            }
        except Exception:
            logger.exception("Full cycle: evaluation step failed")
            result["completed_at"] = datetime.now(UTC).isoformat()
            return result

        # --- Step 2: Drift detection ---
        try:
            drift_snapshots = await self.drift_detector.check_all_drift()
            any_drift = any(s.drift_detected for s in drift_snapshots)
            result["drift"] = {
                "snapshots_count": len(drift_snapshots),
                "drift_detected": any_drift,
                "details": [
                    {
                        "id": str(s.id),
                        "snapshot_type": s.snapshot_type,
                        "feature_name": s.feature_name,
                        "drift_detected": s.drift_detected,
                        "p_value": s.p_value,
                    }
                    for s in drift_snapshots
                ],
            }
        except Exception:
            logger.exception("Full cycle: drift detection step failed")
            result["completed_at"] = datetime.now(UTC).isoformat()
            return result

        # --- Step 3: Determine if retraining is needed ---
        training_needed = eval_run.retraining_triggered or any_drift
        if not training_needed:
            result["training"] = {"skipped": True, "reason": "no trigger"}
            result["completed_at"] = datetime.now(UTC).isoformat()
            return result

        # --- Step 4: Run training ---
        try:
            training_run = await self.trainer.run_training(
                triggered_by=triggered_by,
                evaluation_run_id=eval_run.id,
            )
            result["training"] = {
                "id": str(training_run.id),
                "status": training_run.status,
                "model_version": training_run.resulting_model_version,
                "test_metrics": training_run.test_metrics,
            }
        except Exception:
            logger.exception("Full cycle: training step failed")
            result["training"] = {"skipped": False, "error": "training failed"}
            result["completed_at"] = datetime.now(UTC).isoformat()
            return result

        if training_run.status != "completed" or not training_run.resulting_model_version:
            result["completed_at"] = datetime.now(UTC).isoformat()
            return result

        # --- Step 5: Fairness check on new model ---
        try:
            fairness_reports = await self.fairness_checker.run_fairness_check(
                model_version=training_run.resulting_model_version,
                outcomes=[],  # evaluated from DB by the checker
                training_run_id=training_run.id,
            )
            if isinstance(fairness_reports, list):
                passed = all(r.passed for r in fairness_reports)
                result["fairness"] = {
                    "reports_count": len(fairness_reports),
                    "all_passed": passed,
                }
            else:
                result["fairness"] = {
                    "reports_count": 1,
                    "all_passed": getattr(fairness_reports, "passed", None),
                }
        except Exception:
            logger.exception("Full cycle: fairness check step failed")
            result["fairness"] = {"error": "fairness check failed"}

        # --- Step 6: Auto-promote if better ---
        try:
            promotion = await self.model_manager.auto_promote_if_better(
                training_run.id,
            )
            result["promotion"] = promotion
        except Exception:
            logger.exception("Full cycle: promotion step failed")
            result["promotion"] = {"error": "promotion failed"}

        result["completed_at"] = datetime.now(UTC).isoformat()
        return result

    # ------------------------------------------------------------------
    # Individual operations
    # ------------------------------------------------------------------

    async def run_evaluation_only(self) -> dict[str, Any]:
        """Run model evaluation only and return a summary."""
        try:
            eval_run = await self.evaluator.run_evaluation(
                evaluation_type="manual",
            )
            return {
                "id": str(eval_run.id),
                "model_version": eval_run.model_version,
                "dataset_size": eval_run.dataset_size,
                "metrics": eval_run.metrics,
                "retraining_triggered": eval_run.retraining_triggered,
                "drift_detected": eval_run.drift_detected,
                "started_at": eval_run.started_at.isoformat() if eval_run.started_at else None,
                "completed_at": eval_run.completed_at.isoformat()
                if eval_run.completed_at
                else None,
            }
        except Exception:
            logger.exception("run_evaluation_only failed")
            return {"error": "evaluation failed"}

    async def run_drift_check_only(self) -> dict[str, Any]:
        """Run drift detection only and return a summary."""
        try:
            snapshots = await self.drift_detector.check_all_drift()
            return {
                "snapshots_count": len(snapshots),
                "drift_detected": any(s.drift_detected for s in snapshots),
                "details": [
                    {
                        "id": str(s.id),
                        "snapshot_type": s.snapshot_type,
                        "feature_name": s.feature_name,
                        "drift_detected": s.drift_detected,
                        "p_value": s.p_value,
                    }
                    for s in snapshots
                ],
            }
        except Exception:
            logger.exception("run_drift_check_only failed")
            return {"error": "drift check failed"}

    async def backfill_outcomes(self) -> dict[str, Any]:
        """Backfill outcome records from historical data."""
        try:
            collector = OutcomeCollector(self.db)
            return await collector.backfill_outcomes()
        except Exception:
            logger.exception("backfill_outcomes failed")
            return {"error": "backfill failed"}
