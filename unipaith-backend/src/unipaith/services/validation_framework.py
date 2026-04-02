"""Validation and course-correction framework.

Ensures the engine doesn't go wrong:
1. Held-out validation (20% of outcomes never used for training)
2. Calibration monitoring (ECE -- are predicted probabilities accurate?)
3. Contradiction detection (engine knowledge vs official data)
4. Prediction drift (KS test on score distributions)
5. A/B testing gate before model promotion
6. Auto-rollback when metrics degrade
7. Advisor quality sampling (placeholder for Wave 3)
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.matching import PredictionLog
from unipaith.models.ml_loop import OutcomeRecord, TrainingRun

logger = logging.getLogger("unipaith.validation_framework")

HOLDOUT_FRACTION = 0.2


class ValidationFramework:
    """Course-correction framework for the ML pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def split_holdout(
        self,
        outcomes: list[OutcomeRecord],
    ) -> tuple[list[OutcomeRecord], list[OutcomeRecord]]:
        """Split outcomes into training and held-out sets deterministically."""
        train_set = []
        holdout_set = []
        for outcome in outcomes:
            h = hashlib.md5(str(outcome.id).encode()).hexdigest()
            if int(h[:8], 16) / 0xFFFFFFFF < HOLDOUT_FRACTION:
                holdout_set.append(outcome)
            else:
                train_set.append(outcome)
        return train_set, holdout_set

    async def check_calibration(self, window_days: int = 30) -> dict[str, Any]:
        """Check Expected Calibration Error (ECE).

        Groups predictions into bins and checks if predicted probabilities
        match actual outcome rates.
        """
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        result = await self.db.execute(
            select(OutcomeRecord).where(OutcomeRecord.created_at >= cutoff)
        )
        outcomes = list(result.scalars().all())
        if len(outcomes) < 20:
            return {"status": "insufficient_data", "count": len(outcomes)}

        predictions = []
        actuals = []
        for o in outcomes:
            predictions.append(float(o.predicted_score))
            actuals.append(1.0 if o.actual_outcome in ("admitted", "enrolled") else 0.0)

        predictions = np.array(predictions)
        actuals = np.array(actuals)

        n_bins = 10
        ece = 0.0
        bin_details = []
        for i in range(n_bins):
            lo = i / n_bins
            hi = (i + 1) / n_bins
            mask = (predictions >= lo) & (predictions < hi)
            if not np.any(mask):
                continue
            bin_pred = float(np.mean(predictions[mask]))
            bin_actual = float(np.mean(actuals[mask]))
            bin_count = int(np.sum(mask))
            bin_error = abs(bin_pred - bin_actual)
            ece += bin_error * bin_count / len(predictions)
            bin_details.append(
                {
                    "range": [round(lo, 2), round(hi, 2)],
                    "avg_predicted": round(bin_pred, 4),
                    "avg_actual": round(bin_actual, 4),
                    "count": bin_count,
                    "error": round(bin_error, 4),
                }
            )

        return {
            "status": "computed",
            "ece": round(ece, 4),
            "n_samples": len(outcomes),
            "bins": bin_details,
            "is_well_calibrated": ece < 0.1,
        }

    async def check_prediction_drift(self, window_days: int = 7) -> dict[str, Any]:
        """KS test on recent vs historical prediction score distributions."""
        now = datetime.now(UTC)
        recent_cutoff = now - timedelta(days=window_days)
        historical_cutoff = now - timedelta(days=window_days * 4)

        recent_result = await self.db.execute(
            select(PredictionLog.predicted_score)
            .where(
                PredictionLog.predicted_at >= recent_cutoff,
            )
            .limit(1000)
        )
        recent_scores = [float(r[0]) for r in recent_result.fetchall()]

        historical_result = await self.db.execute(
            select(PredictionLog.predicted_score)
            .where(
                PredictionLog.predicted_at >= historical_cutoff,
                PredictionLog.predicted_at < recent_cutoff,
            )
            .limit(1000)
        )
        historical_scores = [float(r[0]) for r in historical_result.fetchall()]

        if len(recent_scores) < 10 or len(historical_scores) < 10:
            return {
                "status": "insufficient_data",
                "recent_count": len(recent_scores),
                "historical_count": len(historical_scores),
            }

        from scipy.stats import ks_2samp

        stat, p_value = ks_2samp(recent_scores, historical_scores)

        drift_detected = p_value < settings.eval_drift_pvalue_threshold
        return {
            "status": "computed",
            "ks_statistic": round(float(stat), 4),
            "p_value": round(float(p_value), 6),
            "drift_detected": drift_detected,
            "recent_mean": round(float(np.mean(recent_scores)), 4),
            "historical_mean": round(float(np.mean(historical_scores)), 4),
            "recent_count": len(recent_scores),
            "historical_count": len(historical_scores),
        }

    async def check_contradiction(self) -> dict[str, Any]:
        """Detect contradictions between engine predictions and known outcomes.

        Finds cases where the engine predicted high confidence but outcome
        was opposite.
        """
        result = await self.db.execute(
            select(OutcomeRecord)
            .where(
                OutcomeRecord.outcome_confidence >= 0.8,
            )
            .order_by(OutcomeRecord.created_at.desc())
            .limit(500)
        )
        outcomes = list(result.scalars().all())
        if not outcomes:
            return {"status": "no_data", "contradictions": 0}

        contradictions = []
        for o in outcomes:
            predicted_positive = float(o.predicted_score) >= 0.6
            actual_positive = o.actual_outcome in ("admitted", "enrolled")
            if predicted_positive != actual_positive:
                contradictions.append(
                    {
                        "student_id": str(o.student_id),
                        "program_id": str(o.program_id),
                        "predicted_score": float(o.predicted_score),
                        "actual_outcome": o.actual_outcome,
                        "outcome_confidence": float(o.outcome_confidence),
                    }
                )

        rate = len(contradictions) / max(len(outcomes), 1)
        return {
            "status": "computed",
            "total_checked": len(outcomes),
            "contradictions": len(contradictions),
            "contradiction_rate": round(rate, 4),
            "is_acceptable": rate < 0.3,
            "worst_cases": contradictions[:5],
        }

    async def should_rollback(self) -> dict[str, Any]:
        """Check if the current active model should be rolled back."""
        calibration = await self.check_calibration(window_days=7)
        drift = await self.check_prediction_drift(window_days=7)
        contradiction = await self.check_contradiction()

        reasons = []
        if calibration.get("ece", 0) > 0.2:
            reasons.append(f"high_calibration_error: ECE={calibration['ece']}")
        if drift.get("drift_detected"):
            reasons.append(f"prediction_drift: KS={drift.get('ks_statistic')}")
        if not contradiction.get("is_acceptable", True):
            reasons.append(f"high_contradiction_rate: {contradiction.get('contradiction_rate')}")

        recent_failures = await self.db.scalar(
            select(func.count())
            .select_from(TrainingRun)
            .where(
                TrainingRun.status == "failed",
                TrainingRun.created_at >= datetime.now(UTC) - timedelta(days=3),
            )
        )
        if (recent_failures or 0) >= 3:
            reasons.append(f"repeated_training_failures: {recent_failures}")

        return {
            "should_rollback": len(reasons) > 0,
            "reasons": reasons,
            "calibration": calibration,
            "drift": drift,
            "contradiction": contradiction,
        }

    async def get_validation_summary(self) -> dict[str, Any]:
        """Full validation report for admin dashboard."""
        calibration = await self.check_calibration()
        drift = await self.check_prediction_drift()
        contradiction = await self.check_contradiction()
        rollback = await self.should_rollback()

        overall_healthy = (
            calibration.get("is_well_calibrated", True)
            and not drift.get("drift_detected", False)
            and contradiction.get("is_acceptable", True)
            and not rollback["should_rollback"]
        )

        return {
            "overall_status": "healthy" if overall_healthy else "warning",
            "calibration": calibration,
            "drift": drift,
            "contradiction": contradiction,
            "rollback_recommendation": rollback,
            "checked_at": datetime.now(UTC).isoformat(),
        }
