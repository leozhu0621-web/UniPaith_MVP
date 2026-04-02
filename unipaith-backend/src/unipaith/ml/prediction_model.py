"""Unified prediction model via stacked generalization.

Combines 6 signal sources into calibrated probability predictions:
  1. Embedding similarity (cosine)
  2. Collaborative filtering (ALS affinity)
  3. Pattern recognition (cluster-program affinity)
  4. Interaction learning (bandit score)
  5. XGBoost features (structured ML)
  6. Knowledge signals (relevance from knowledge base)

Uses logistic regression as the meta-learner over signal outputs,
with Platt scaling for probability calibration.

Outputs: P(admitted), P(success), confidence interval, tier.
"""

from __future__ import annotations

import logging

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.matching import ModelRegistry

logger = logging.getLogger("unipaith.ml.prediction_model")

SIGNAL_NAMES = [
    "embedding_similarity",
    "collaborative_filtering",
    "pattern_affinity",
    "interaction_score",
    "xgboost_score",
    "knowledge_relevance",
]


class PredictionModel:
    """Stacked generalization ensemble with Platt scaling."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._weights: np.ndarray | None = None
        self._bias: float = 0.0
        self._calibration_a: float = -1.0
        self._calibration_b: float = 0.0
        self._model_version: str = "v1.0-mvp"
        self._is_loaded: bool = False

    async def load_active_model(self) -> bool:
        """Load the active model weights from the registry."""
        result = await self.db.execute(
            select(ModelRegistry).where(ModelRegistry.is_active.is_(True)).limit(1)
        )
        active = result.scalar_one_or_none()
        if active is None:
            return False

        try:
            params = active.hyperparameters or {}
            ensemble_config = params.get("ensemble", {})

            weights = ensemble_config.get("weights")
            if weights and len(weights) == len(SIGNAL_NAMES):
                self._weights = np.array(weights, dtype=float)
            else:
                self._weights = np.ones(len(SIGNAL_NAMES)) / len(SIGNAL_NAMES)

            self._bias = float(ensemble_config.get("bias", 0.0))
            self._calibration_a = float(ensemble_config.get("calibration_a", -1.0))
            self._calibration_b = float(ensemble_config.get("calibration_b", 0.0))
            self._model_version = active.model_version
            self._is_loaded = True

            logger.info("Loaded active model: %s", self._model_version)
            return True
        except Exception:
            logger.exception("Failed to load model params from registry")
            return False

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def predict(self, signals: dict[str, float]) -> dict:
        """Produce calibrated prediction from 6 signal sources.

        Returns:
            dict with p_admitted, p_success, confidence, tier, breakdown
        """
        signal_vec = np.array([signals.get(name, 0.5) for name in SIGNAL_NAMES])

        if self._weights is not None:
            raw_score = float(np.dot(self._weights, signal_vec) + self._bias)
        else:
            raw_score = float(np.mean(signal_vec))

        p_admitted = self._platt_calibrate(raw_score)
        p_success = self._estimate_success(p_admitted, signals)

        ci_half = self._confidence_interval_half(signal_vec, p_admitted)
        ci_lower = max(0.0, p_admitted - ci_half)
        ci_upper = min(1.0, p_admitted + ci_half)

        if p_admitted >= settings.matching_tier1_threshold:
            tier = 1
        elif p_admitted >= settings.matching_tier2_threshold:
            tier = 2
        else:
            tier = 3

        return {
            "p_admitted": round(p_admitted, 4),
            "p_success": round(p_success, 4),
            "confidence_interval": [round(ci_lower, 4), round(ci_upper, 4)],
            "tier": tier,
            "raw_score": round(raw_score, 4),
            "model_version": self._model_version,
            "signal_contributions": {
                name: round(
                    float(self._weights[i] * signal_vec[i])
                    if self._weights is not None
                    else float(signal_vec[i] / len(SIGNAL_NAMES)),
                    4,
                )
                for i, name in enumerate(SIGNAL_NAMES)
            },
        }

    def predict_heuristic(self, signals: dict[str, float]) -> dict:
        """Fallback heuristic scorer when no trained model exists."""
        default_weights = {
            "embedding_similarity": 0.30,
            "collaborative_filtering": 0.15,
            "pattern_affinity": 0.10,
            "interaction_score": 0.10,
            "xgboost_score": 0.25,
            "knowledge_relevance": 0.10,
        }

        score = sum(
            default_weights.get(name, 0.1) * signals.get(name, 0.5) for name in SIGNAL_NAMES
        )
        score = max(0.0, min(1.0, score))

        if score >= settings.matching_tier1_threshold:
            tier = 1
        elif score >= settings.matching_tier2_threshold:
            tier = 2
        else:
            tier = 3

        return {
            "p_admitted": round(score, 4),
            "p_success": round(score * 0.85, 4),
            "confidence_interval": [round(max(0, score - 0.15), 4), round(min(1, score + 0.15), 4)],
            "tier": tier,
            "raw_score": round(score, 4),
            "model_version": "heuristic",
            "signal_contributions": {
                name: round(default_weights.get(name, 0.1) * signals.get(name, 0.5), 4)
                for name in SIGNAL_NAMES
            },
        }

    def _platt_calibrate(self, raw_score: float) -> float:
        """Platt scaling: sigmoid(a * raw + b) for calibrated probabilities."""
        logit = self._calibration_a * raw_score + self._calibration_b
        logit = max(-20.0, min(20.0, logit))
        return 1.0 / (1.0 + np.exp(-logit))

    def _estimate_success(self, p_admitted: float, signals: dict[str, float]) -> float:
        """Estimate probability of thriving if admitted (not just getting in)."""
        base = p_admitted * 0.8
        cf_boost = signals.get("collaborative_filtering", 0.5) * 0.1
        pattern_boost = signals.get("pattern_affinity", 0.5) * 0.1
        return max(0.0, min(1.0, base + cf_boost + pattern_boost))

    def _confidence_interval_half(
        self,
        signal_vec: np.ndarray,
        p: float,
    ) -> float:
        """Estimate half-width of confidence interval based on signal agreement."""
        if len(signal_vec) < 2:
            return 0.2
        std = float(np.std(signal_vec))
        base_ci = 0.05 + std * 0.3
        uncertainty = p * (1 - p)
        return min(0.25, base_ci + uncertainty * 0.1)

    @staticmethod
    def train_ensemble(
        signal_matrix: np.ndarray,
        labels: np.ndarray,
    ) -> dict:
        """Train the meta-learner weights and calibration parameters.

        Args:
            signal_matrix: (n_samples, 6) array of signal values
            labels: (n_samples,) binary outcome labels

        Returns:
            dict with weights, bias, calibration_a, calibration_b
        """
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_predict

        lr = LogisticRegression(max_iter=1000, C=1.0)
        lr.fit(signal_matrix, labels)

        weights = lr.coef_[0].tolist()
        bias = float(lr.intercept_[0])

        probs = cross_val_predict(
            LogisticRegression(max_iter=1000, C=1.0),
            signal_matrix,
            labels,
            cv=min(5, max(2, len(labels) // 10)),
            method="predict_proba",
        )[:, 1]

        a, b = _fit_platt(probs, labels)

        return {
            "weights": weights,
            "bias": bias,
            "calibration_a": a,
            "calibration_b": b,
            "signal_names": SIGNAL_NAMES,
        }


def _fit_platt(probs: np.ndarray, labels: np.ndarray) -> tuple[float, float]:
    """Fit Platt scaling parameters a, b for sigmoid(a*x + b)."""
    from scipy.optimize import minimize

    def neg_log_likelihood(params):
        a, b = params
        logits = a * probs + b
        logits = np.clip(logits, -20, 20)
        p = 1.0 / (1.0 + np.exp(-logits))
        p = np.clip(p, 1e-7, 1 - 1e-7)
        return -np.mean(labels * np.log(p) + (1 - labels) * np.log(1 - p))

    result = minimize(neg_log_likelihood, x0=[1.0, 0.0], method="Nelder-Mead")
    return float(result.x[0]), float(result.x[1])
