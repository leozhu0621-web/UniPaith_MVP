"""
Drift Detector — monitors for distribution shifts in predictions, features,
and data quality using the Kolmogorov-Smirnov test and volume-based checks.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.matching import MatchResult, PredictionLog, StudentFeature
from unipaith.models.ml_loop import DriftSnapshot

logger = logging.getLogger(__name__)

# Key features to monitor for drift
_MONITORED_FEATURES = [
    "normalized_gpa",
    "work_experience_years",
    "test_score_normalized",
]


class DriftDetector:
    """Detects distribution drift in predictions, features, and data volume."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def check_all_drift(
        self,
        reference_days: int = 90,
        current_days: int = 7,
    ) -> list[DriftSnapshot]:
        """Run all drift checks and return a list of DriftSnapshot records.

        Args:
            reference_days: Number of days for the reference (baseline) period.
            current_days: Number of days for the current (recent) period.

        Returns:
            List of persisted DriftSnapshot records, one per check.
        """
        now = datetime.now(timezone.utc)
        ref_start = now - timedelta(days=reference_days)
        ref_end = now - timedelta(days=current_days)
        cur_start = now - timedelta(days=current_days)
        cur_end = now

        snapshots: list[DriftSnapshot] = []

        # 1) Prediction score distribution drift
        pred_snapshot = await self._check_prediction_drift(
            ref_start, ref_end, cur_start, cur_end
        )
        if pred_snapshot is not None:
            snapshots.append(pred_snapshot)

        # 2) Feature distribution drift for each monitored feature
        for feature_name in _MONITORED_FEATURES:
            feat_snapshot = await self._check_feature_drift(
                feature_name, ref_start, ref_end, cur_start, cur_end
            )
            if feat_snapshot is not None:
                snapshots.append(feat_snapshot)

        # 3) Data quality / volume drift
        quality_snapshot = await self._check_data_quality_drift(
            ref_start, ref_end, cur_start, cur_end
        )
        if quality_snapshot is not None:
            snapshots.append(quality_snapshot)

        detected_count = sum(1 for s in snapshots if s.drift_detected)
        logger.info(
            "Drift check complete: %d snapshots, %d drift detected",
            len(snapshots),
            detected_count,
        )
        return snapshots

    # ------------------------------------------------------------------
    # Prediction drift
    # ------------------------------------------------------------------

    async def _check_prediction_drift(
        self,
        ref_start: datetime,
        ref_end: datetime,
        cur_start: datetime,
        cur_end: datetime,
    ) -> DriftSnapshot | None:
        """Check for distribution drift in match scores.

        Uses the two-sample Kolmogorov-Smirnov test on MatchResult.match_score
        values between reference and current periods.
        """
        ref_scores = await self._load_match_scores(ref_start, ref_end)
        cur_scores = await self._load_match_scores(cur_start, cur_end)

        if len(ref_scores) < 5 or len(cur_scores) < 5:
            logger.debug(
                "Insufficient data for prediction drift check: ref=%d cur=%d",
                len(ref_scores),
                len(cur_scores),
            )
            return None

        from scipy.stats import ks_2samp

        statistic, p_value = ks_2samp(ref_scores, cur_scores)

        ref_stats = _compute_stats(ref_scores)
        cur_stats = _compute_stats(cur_scores)
        drift_detected = p_value < settings.eval_drift_pvalue_threshold

        snapshot = DriftSnapshot(
            snapshot_type="prediction_distribution",
            reference_period_start=ref_start,
            reference_period_end=ref_end,
            current_period_start=cur_start,
            current_period_end=cur_end,
            feature_name="match_score",
            reference_stats=ref_stats,
            current_stats=cur_stats,
            test_statistic=Decimal(str(round(statistic, 6))),
            p_value=Decimal(str(round(p_value, 8))),
            drift_detected=drift_detected,
        )
        self.db.add(snapshot)
        await self.db.flush()

        if drift_detected:
            logger.warning(
                "Prediction drift detected: KS=%.4f p=%.6f",
                statistic,
                p_value,
            )
        return snapshot

    async def _load_match_scores(
        self, start: datetime, end: datetime
    ) -> list[float]:
        """Load match scores from MatchResult within a time window."""
        stmt = (
            select(MatchResult.match_score)
            .where(
                and_(
                    MatchResult.computed_at >= start,
                    MatchResult.computed_at < end,
                    MatchResult.match_score.isnot(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        return [float(row[0]) for row in result.all()]

    # ------------------------------------------------------------------
    # Feature drift
    # ------------------------------------------------------------------

    async def _check_feature_drift(
        self,
        feature_name: str,
        ref_start: datetime,
        ref_end: datetime,
        cur_start: datetime,
        cur_end: datetime,
    ) -> DriftSnapshot | None:
        """Check for distribution drift in a specific student feature.

        Extracts the feature value from StudentFeature.feature_data
        ['structured'][feature_name].
        """
        ref_values = await self._load_feature_values(
            feature_name, ref_start, ref_end
        )
        cur_values = await self._load_feature_values(
            feature_name, cur_start, cur_end
        )

        if len(ref_values) < 5 or len(cur_values) < 5:
            logger.debug(
                "Insufficient data for feature drift (%s): ref=%d cur=%d",
                feature_name,
                len(ref_values),
                len(cur_values),
            )
            return None

        from scipy.stats import ks_2samp

        statistic, p_value = ks_2samp(ref_values, cur_values)

        ref_stats = _compute_stats(ref_values)
        cur_stats = _compute_stats(cur_values)
        drift_detected = p_value < settings.eval_drift_pvalue_threshold

        snapshot = DriftSnapshot(
            snapshot_type="feature_distribution",
            reference_period_start=ref_start,
            reference_period_end=ref_end,
            current_period_start=cur_start,
            current_period_end=cur_end,
            feature_name=feature_name,
            reference_stats=ref_stats,
            current_stats=cur_stats,
            test_statistic=Decimal(str(round(statistic, 6))),
            p_value=Decimal(str(round(p_value, 8))),
            drift_detected=drift_detected,
        )
        self.db.add(snapshot)
        await self.db.flush()

        if drift_detected:
            logger.warning(
                "Feature drift detected for %s: KS=%.4f p=%.6f",
                feature_name,
                statistic,
                p_value,
            )
        return snapshot

    async def _load_feature_values(
        self, feature_name: str, start: datetime, end: datetime
    ) -> list[float]:
        """Load values of a specific feature from StudentFeature records.

        The feature is expected at feature_data['structured'][feature_name].
        """
        stmt = (
            select(StudentFeature.feature_data)
            .where(
                and_(
                    StudentFeature.updated_at >= start,
                    StudentFeature.updated_at < end,
                    StudentFeature.feature_data.isnot(None),
                )
            )
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()

        values: list[float] = []
        for feature_data in rows:
            structured = feature_data.get("structured") if feature_data else None
            if structured is None:
                continue
            val = structured.get(feature_name)
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    continue
        return values

    # ------------------------------------------------------------------
    # Data quality / volume drift
    # ------------------------------------------------------------------

    async def _check_data_quality_drift(
        self,
        ref_start: datetime,
        ref_end: datetime,
        cur_start: datetime,
        cur_end: datetime,
    ) -> DriftSnapshot | None:
        """Check for data quality drift based on prediction volume.

        Drift is detected if the current period volume drops by more than
        50% compared to the reference period (adjusted for period length).
        """
        ref_count = await self._count_predictions(ref_start, ref_end)
        cur_count = await self._count_predictions(cur_start, cur_end)

        # Normalize counts to a daily rate for fair comparison
        ref_days = max((ref_end - ref_start).days, 1)
        cur_days = max((cur_end - cur_start).days, 1)
        ref_daily_rate = ref_count / ref_days
        cur_daily_rate = cur_count / cur_days

        # Volume drop threshold: 50%
        if ref_daily_rate > 0:
            volume_ratio = cur_daily_rate / ref_daily_rate
        else:
            volume_ratio = 1.0  # No reference data, no drift

        drift_detected = volume_ratio < 0.5

        ref_stats = {
            "count": ref_count,
            "days": ref_days,
            "daily_rate": round(ref_daily_rate, 2),
        }
        cur_stats = {
            "count": cur_count,
            "days": cur_days,
            "daily_rate": round(cur_daily_rate, 2),
        }

        snapshot = DriftSnapshot(
            snapshot_type="data_quality",
            reference_period_start=ref_start,
            reference_period_end=ref_end,
            current_period_start=cur_start,
            current_period_end=cur_end,
            feature_name="prediction_volume",
            reference_stats=ref_stats,
            current_stats=cur_stats,
            test_statistic=Decimal(str(round(volume_ratio, 6))),
            p_value=None,  # Not a statistical test
            drift_detected=drift_detected,
        )
        self.db.add(snapshot)
        await self.db.flush()

        if drift_detected:
            logger.warning(
                "Data quality drift detected: volume ratio=%.2f "
                "(ref_daily=%.1f, cur_daily=%.1f)",
                volume_ratio,
                ref_daily_rate,
                cur_daily_rate,
            )
        return snapshot

    async def _count_predictions(
        self, start: datetime, end: datetime
    ) -> int:
        """Count PredictionLog entries within a time window."""
        stmt = (
            select(func.count())
            .select_from(PredictionLog)
            .where(
                and_(
                    PredictionLog.predicted_at >= start,
                    PredictionLog.predicted_at < end,
                )
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _compute_stats(values: list[float]) -> dict:
    """Compute descriptive statistics for a list of numeric values."""
    import statistics

    n = len(values)
    if n == 0:
        return {"count": 0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

    mean_val = statistics.mean(values)
    std_val = statistics.stdev(values) if n > 1 else 0.0

    return {
        "count": n,
        "mean": round(mean_val, 6),
        "std": round(std_val, 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
    }
