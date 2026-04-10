"""Scientific metrics for the knowledge engine.

Computes and exposes metrics with mathematical definitions:
- Prediction quality: F1, AUC-ROC, ECE, Brier Score, NDCG@10
- Information gain: prediction entropy reduction per learning cycle
- Coverage: completeness vs IPEDS/QS reference datasets
- Understanding depth (placeholder for Wave 3 PersonInsight metrics)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.knowledge import KnowledgeDocument, KnowledgeLink
from unipaith.models.matching import Embedding, PredictionLog
from unipaith.models.ml_loop import OutcomeRecord, TrainingRun
from unipaith.services.validation_framework import ValidationFramework

logger = logging.getLogger("unipaith.engine_metrics")

IPEDS_APPROXIMATE_INSTITUTIONS = 4000
QS_APPROXIMATE_PROGRAMS = 15000


class EngineMetrics:
    """Computes scientific metrics for the engine's learning progress."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.validation = ValidationFramework(db)

    async def compute_all(self) -> dict[str, Any]:
        """Compute the full metrics dashboard."""
        prediction = await self._prediction_quality()
        info_gain = await self._information_gain()
        coverage = await self._coverage()
        operational = await self._operational_metrics()
        validation_summary = await self.validation.get_validation_summary()

        return {
            "computed_at": datetime.now(UTC).isoformat(),
            "prediction_quality": prediction,
            "information_gain": info_gain,
            "coverage": coverage,
            "operational": operational,
            "validation": validation_summary,
        }

    async def _prediction_quality(self) -> dict[str, Any]:
        """F1, AUC-ROC, ECE, Brier Score, NDCG@10 from recent outcomes."""
        result = await self.db.execute(
            select(OutcomeRecord).order_by(OutcomeRecord.created_at.desc()).limit(1000)
        )
        outcomes = [
            o for o in result.scalars().all() if o.predicted_score is not None
        ]
        if len(outcomes) < 10:
            return {"status": "insufficient_data", "count": len(outcomes)}

        y_pred = np.array([float(o.predicted_score) for o in outcomes])
        y_true = np.array(
            [1.0 if o.actual_outcome in ("admitted", "enrolled") else 0.0 for o in outcomes]
        )
        y_pred_binary = (y_pred >= 0.5).astype(float)

        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )

        metrics: dict[str, Any] = {"status": "computed", "n_samples": len(outcomes)}

        try:
            metrics["accuracy"] = round(float(accuracy_score(y_true, y_pred_binary)), 4)
        except Exception:
            metrics["accuracy"] = None

        try:
            metrics["f1"] = round(float(f1_score(y_true, y_pred_binary, zero_division=0)), 4)
        except Exception:
            metrics["f1"] = None

        try:
            metrics["precision"] = round(
                float(precision_score(y_true, y_pred_binary, zero_division=0)),
                4,
            )
        except Exception:
            metrics["precision"] = None

        try:
            metrics["recall"] = round(
                float(recall_score(y_true, y_pred_binary, zero_division=0)),
                4,
            )
        except Exception:
            metrics["recall"] = None

        try:
            if len(np.unique(y_true)) > 1:
                metrics["auc_roc"] = round(float(roc_auc_score(y_true, y_pred)), 4)
            else:
                metrics["auc_roc"] = None
        except Exception:
            metrics["auc_roc"] = None

        metrics["brier_score"] = round(float(np.mean((y_pred - y_true) ** 2)), 4)

        calibration = await self.validation.check_calibration(window_days=90)
        metrics["ece"] = calibration.get("ece")

        metrics["ndcg_10"] = self._compute_ndcg(outcomes, k=10)

        return metrics

    async def _information_gain(self) -> dict[str, Any]:
        """Measure prediction entropy reduction per learning cycle."""
        result = await self.db.execute(
            select(TrainingRun)
            .where(TrainingRun.status == "completed")
            .order_by(TrainingRun.created_at.desc())
            .limit(10)
        )
        runs = list(result.scalars().all())
        if len(runs) < 2:
            return {"status": "insufficient_runs", "count": len(runs)}

        entropies = []
        for run in runs:
            perf = run.performance_metrics or {}
            accuracy = float(perf.get("accuracy", 0.5) or 0.5)
            p = max(0.01, min(0.99, accuracy))
            entropy = -(p * np.log2(p) + (1 - p) * np.log2(1 - p))
            entropies.append(entropy)

        if len(entropies) >= 2:
            entropy_delta = entropies[0] - entropies[-1]
        else:
            entropy_delta = 0.0

        return {
            "status": "computed",
            "latest_entropy": round(float(entropies[0]), 4) if entropies else None,
            "oldest_entropy": round(float(entropies[-1]), 4) if entropies else None,
            "entropy_reduction": round(float(entropy_delta), 4),
            "improving": entropy_delta > 0,
            "runs_analyzed": len(runs),
        }

    async def _coverage(self) -> dict[str, Any]:
        """Measure knowledge coverage vs reference datasets."""
        institutions_count = (
            await self.db.scalar(select(func.count()).select_from(Institution)) or 0
        )
        programs_count = await self.db.scalar(select(func.count()).select_from(Program)) or 0
        knowledge_docs = (
            await self.db.scalar(
                select(func.count())
                .select_from(KnowledgeDocument)
                .where(
                    KnowledgeDocument.processing_status == "completed",
                )
            )
            or 0
        )
        embeddings_count = await self.db.scalar(select(func.count()).select_from(Embedding)) or 0
        unique_entities = (
            await self.db.scalar(
                select(func.count(func.distinct(KnowledgeLink.entity_name))).select_from(
                    KnowledgeLink
                )
            )
            or 0
        )

        return {
            "institutions": {
                "count": institutions_count,
                "vs_ipeds": round(institutions_count / max(IPEDS_APPROXIMATE_INSTITUTIONS, 1), 4),
            },
            "programs": {
                "count": programs_count,
                "vs_qs": round(programs_count / max(QS_APPROXIMATE_PROGRAMS, 1), 4),
            },
            "knowledge_documents": knowledge_docs,
            "embeddings": embeddings_count,
            "unique_entities_linked": unique_entities,
            "feature_completeness": await self._feature_completeness(),
        }

    async def _feature_completeness(self) -> dict[str, Any]:
        """Check what percentage of programs have complete feature data."""
        total = await self.db.scalar(select(func.count()).select_from(Program)) or 0
        with_features = (
            await self.db.scalar(
                select(func.count())
                .select_from(Embedding)
                .where(
                    Embedding.entity_type == "program",
                )
            )
            or 0
        )
        return {
            "total_programs": total,
            "with_embeddings": with_features,
            "completeness": round(with_features / max(total, 1), 4),
        }

    async def _operational_metrics(self) -> dict[str, Any]:
        """Learning velocity and cost efficiency."""
        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)

        training_runs_7d = (
            await self.db.scalar(
                select(func.count())
                .select_from(TrainingRun)
                .where(
                    TrainingRun.created_at >= week_ago,
                )
            )
            or 0
        )
        completed_7d = (
            await self.db.scalar(
                select(func.count())
                .select_from(TrainingRun)
                .where(
                    TrainingRun.status == "completed",
                    TrainingRun.created_at >= week_ago,
                )
            )
            or 0
        )
        failed_7d = (
            await self.db.scalar(
                select(func.count())
                .select_from(TrainingRun)
                .where(
                    TrainingRun.status == "failed",
                    TrainingRun.created_at >= week_ago,
                )
            )
            or 0
        )
        predictions_7d = (
            await self.db.scalar(
                select(func.count())
                .select_from(PredictionLog)
                .where(
                    PredictionLog.predicted_at >= week_ago,
                )
            )
            or 0
        )
        outcomes_7d = (
            await self.db.scalar(
                select(func.count())
                .select_from(OutcomeRecord)
                .where(
                    OutcomeRecord.created_at >= week_ago,
                )
            )
            or 0
        )

        latest_model = await self.db.execute(
            select(TrainingRun)
            .where(TrainingRun.status == "completed")
            .order_by(TrainingRun.created_at.desc())
            .limit(1)
        )
        latest = latest_model.scalar_one_or_none()
        model_age_hours = None
        if latest and latest.created_at:
            model_age_hours = round((now - latest.created_at).total_seconds() / 3600, 1)

        return {
            "training_runs_7d": training_runs_7d,
            "completed_7d": completed_7d,
            "failed_7d": failed_7d,
            "success_rate_7d": round(completed_7d / max(training_runs_7d, 1), 4),
            "predictions_7d": predictions_7d,
            "outcomes_7d": outcomes_7d,
            "model_age_hours": model_age_hours,
        }

    def _compute_ndcg(self, outcomes: list[OutcomeRecord], k: int = 10) -> float | None:
        """NDCG@K for ranking quality."""
        outcomes = [o for o in outcomes if o.predicted_score is not None]
        if len(outcomes) < k:
            return None

        sorted_outcomes = sorted(outcomes, key=lambda o: float(o.predicted_score), reverse=True)
        top_k = sorted_outcomes[:k]
        relevance = [1.0 if o.actual_outcome in ("admitted", "enrolled") else 0.0 for o in top_k]

        dcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(relevance))

        ideal_relevance = sorted(relevance, reverse=True)
        idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevance))

        if idcg == 0:
            return None
        return round(float(dcg / idcg), 4)
