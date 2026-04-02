"""
Phase 4: Self-Improving ML Loop modules.

- outcome_collector: Records ground-truth outcomes from decisions/offers/enrollments
- evaluator: Computes accuracy, confusion matrix, per-tier metrics
- drift_detector: KS-test based drift detection for predictions and features
- fairness: Demographic parity, equal opportunity, equalized odds checks
- trainer: Optuna-tuned XGBoost retraining on accumulated outcome data
- model_manager: Model promotion, rollback, and registry management
- ab_testing: Deterministic A/B test assignment and experiment evaluation
"""

from unipaith.ml.drift_detector import DriftDetector
from unipaith.ml.evaluator import ModelEvaluator
from unipaith.ml.fairness import FairnessChecker
from unipaith.ml.outcome_collector import OutcomeCollector

__all__ = [
    "DriftDetector",
    "FairnessChecker",
    "ModelEvaluator",
    "OutcomeCollector",
]
