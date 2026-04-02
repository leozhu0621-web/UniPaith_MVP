"""
ModelTrainer — Optuna-tuned XGBoost retraining on accumulated outcome data.

Collects labeled outcomes, builds a feature matrix, runs SMOTE for class
imbalance, performs Bayesian hyperparameter search via Optuna with
StratifiedKFold cross-validation, and persists the best model to the
ModelRegistry.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.ai_runtime_metrics import record_ml_training, start_timer
from unipaith.core.exceptions import BadRequestException
from unipaith.models.matching import ModelRegistry
from unipaith.models.ml_loop import OutcomeRecord, TrainingRun

logger = logging.getLogger(__name__)

# ---- Graceful imports for heavy ML dependencies ----
try:
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.model_selection import StratifiedKFold, train_test_split
except ImportError as exc:
    raise ImportError(
        "scikit-learn is required for ModelTrainer. Install it with: pip install scikit-learn"
    ) from exc

try:
    from xgboost import XGBClassifier
except ImportError as exc:
    raise ImportError(
        "xgboost is required for ModelTrainer. Install it with: pip install xgboost"
    ) from exc

try:
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
except ImportError as exc:
    raise ImportError(
        "optuna is required for ModelTrainer. Install it with: pip install optuna"
    ) from exc

try:
    from imblearn.over_sampling import SMOTE
except ImportError as exc:
    raise ImportError(
        "imbalanced-learn is required for ModelTrainer. "
        "Install it with: pip install imbalanced-learn"
    ) from exc

# Feature columns used for training
FEATURE_COLUMNS: list[str] = [
    "normalized_gpa",
    "work_experience_years",
    "research_count",
    "leadership_count",
    "publication_count",
    "total_activities",
    "test_score_avg",
    "embedding_similarity",
    "historical_fit",
    "institution_pref_fit",
    "student_pref_fit",
    "budget_fit",
]

# Outcomes treated as positive labels
_POSITIVE_OUTCOMES = {"admitted", "enrolled"}
_NEGATIVE_OUTCOMES = {"rejected", "declined"}


class ModelTrainer:
    """Orchestrates end-to-end model retraining with Optuna hyperparameter search."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_training(
        self,
        triggered_by: str = "scheduled",
        evaluation_run_id: Any | None = None,
        mode: str = "full",
        trigger_reason: str | None = None,
        new_outcomes_count: int | None = None,
    ) -> TrainingRun:
        """
        Execute a full training pipeline:
        1. Collect labeled data
        2. Build feature matrix
        3. SMOTE resampling
        4. Optuna hyperparameter search with StratifiedKFold CV
        5. Final model training + test-set evaluation
        6. Persist to ModelRegistry
        """
        now = datetime.now(UTC)
        training_mode = mode.lower()
        if training_mode not in {"fast", "full"}:
            raise BadRequestException("training mode must be 'fast' or 'full'")
        timer = start_timer()

        training_run = TrainingRun(
            triggered_by=triggered_by,
            evaluation_run_id=evaluation_run_id,
            training_data_size=0,
            test_data_size=0,
            feature_columns=FEATURE_COLUMNS,
            algorithm="XGBClassifier",
            mode=training_mode,
            trigger_reason=trigger_reason,
            new_outcomes_count=new_outcomes_count,
            hyperparameters={},
            cv_metrics={
                "mode": training_mode,
                "trigger_reason": trigger_reason,
                "new_outcomes_count": new_outcomes_count,
            },
            status="running",
            started_at=now,
        )
        self.db.add(training_run)
        await self.db.flush()

        try:
            result = await self._execute_pipeline(training_run, training_mode)
            record_ml_training(timer, ok=result.status == "completed")
            return result
        except Exception:
            training_run.status = "failed"
            training_run.failure_reason = "unexpected_error"
            training_run.completed_at = datetime.now(UTC)
            await self.db.flush()
            logger.exception("Training run %s failed unexpectedly", training_run.id)
            record_ml_training(timer, ok=False)
            raise

    # ------------------------------------------------------------------
    # Internal pipeline
    # ------------------------------------------------------------------

    async def _execute_pipeline(
        self,
        training_run: TrainingRun,
        mode: str,
    ) -> TrainingRun:
        # Step 1 — collect labelled data
        data, data_metadata = await self._collect_training_data()
        if data_metadata.get("window_start"):
            training_run.data_window_start = datetime.fromisoformat(data_metadata["window_start"])
        training_run.data_window_end = datetime.now(UTC)
        mode_params = self._mode_settings(mode)

        if len(data) < settings.outcome_min_decisions_for_training:
            training_run.status = "failed"
            training_run.failure_reason = (
                f"Insufficient training data: {len(data)} samples "
                f"(minimum {settings.outcome_min_decisions_for_training})"
            )
            training_run.completed_at = datetime.now(UTC)
            training_run.cv_metrics = {
                **(training_run.cv_metrics or {}),
                **data_metadata,
                "mode_params": mode_params,
            }
            await self.db.flush()
            logger.warning("Training aborted — only %d labelled samples available", len(data))
            return training_run

        # Step 2 — build feature matrix
        X, y = self._build_feature_matrix(data)  # noqa: N806

        # Step 3 — train/test split (stratified)
        X_train, X_test, y_train, y_test = train_test_split(  # noqa: N806
            X,
            y,
            test_size=settings.training_test_split,
            stratify=y,
            random_state=42,
        )

        training_run.training_data_size = len(X_train)
        training_run.test_data_size = len(X_test)

        # Step 4 — SMOTE on training set only
        smote = SMOTE(random_state=42)
        X_train_res, y_train_res = smote.fit_resample(X_train, y_train)  # noqa: N806

        # Step 5 — Optuna hyperparameter search
        study_name = f"training-{training_run.id}"
        study = optuna.create_study(
            study_name=study_name,
            direction="maximize",
        )

        def objective(trial: optuna.Trial) -> float:
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 50, 300),
                "max_depth": trial.suggest_int("max_depth", 3, 10),
                "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                "subsample": trial.suggest_float("subsample", 0.6, 1.0),
                "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
                "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
                "gamma": trial.suggest_float("gamma", 0.0, 5.0),
                "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
                "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            }

            clf = XGBClassifier(
                **params,
                use_label_encoder=False,
                eval_metric="logloss",
                random_state=42,
                verbosity=0,
            )

            skf = StratifiedKFold(n_splits=mode_params["cv_folds"], shuffle=True, random_state=42)

            fold_scores: list[float] = []
            for train_idx, val_idx in skf.split(X_train_res, y_train_res):
                clf.fit(X_train_res[train_idx], y_train_res[train_idx])
                preds = clf.predict(X_train_res[val_idx])
                fold_scores.append(accuracy_score(y_train_res[val_idx], preds))

            return float(np.mean(fold_scores))

        study.optimize(
            objective,
            n_trials=mode_params["optuna_trials"],
            timeout=mode_params["max_duration_minutes"] * 60,
        )

        best_params = study.best_params
        cv_metrics = {
            "best_cv_accuracy": study.best_value,
            "n_trials": len(study.trials),
            "best_trial_number": study.best_trial.number,
            "mode": mode,
            "mode_params": mode_params,
            **data_metadata,
        }

        # Step 6 — train final model with best params on full training set
        final_model = XGBClassifier(
            **best_params,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
            verbosity=0,
        )
        final_model.fit(X_train_res, y_train_res)

        # Step 7 — evaluate on held-out test set
        y_pred = final_model.predict(X_test)
        y_proba = final_model.predict_proba(X_test)

        test_metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "roc_auc": float(
                roc_auc_score(y_test, y_proba[:, 1]) if y_proba.shape[1] == 2 else 0.0
            ),
        }

        # Step 8 — generate model version
        model_version = await self._generate_version_string()

        # Step 9 — persist to ModelRegistry (MVP: store params + metrics, not pickle)
        artifact_path = f"models/{model_version}/metadata.json"

        registry_entry = ModelRegistry(
            model_version=model_version,
            architecture="XGBClassifier",
            hyperparameters=best_params,
            performance_metrics=test_metrics,
            is_active=False,
            trained_at=datetime.now(UTC),
        )
        self.db.add(registry_entry)

        # Step 10 — finalise TrainingRun
        training_run.status = "completed"
        training_run.hyperparameters = best_params
        training_run.cv_metrics = cv_metrics
        training_run.test_metrics = test_metrics
        training_run.optuna_study_name = study_name
        training_run.resulting_model_version = model_version
        training_run.model_artifact_path = artifact_path
        training_run.completed_at = datetime.now(UTC)

        await self.db.flush()

        logger.info(
            "Training run %s completed (%s mode) — model %s | accuracy %.4f | roc_auc %.4f",
            training_run.id,
            mode,
            model_version,
            test_metrics["accuracy"],
            test_metrics["roc_auc"],
        )

        return training_run

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    async def _collect_training_data(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Join OutcomeRecord rows with their features_snapshot.
        Returns a list of dicts, each containing feature values and a binary label.
        """
        result = await self.db.execute(
            select(OutcomeRecord).where(
                OutcomeRecord.actual_outcome.in_(list(_POSITIVE_OUTCOMES | _NEGATIVE_OUTCOMES))
            )
        )
        records = list(result.scalars().all())
        total_records = len(records)
        window_start = datetime.now(UTC) - timedelta(
            days=settings.training_recent_outcome_window_days
        )
        records = [r for r in records if r.outcome_recorded_at >= window_start]

        data: list[dict[str, Any]] = []
        for rec in records:
            snapshot = rec.features_snapshot or {}
            row: dict[str, Any] = {}

            for col in FEATURE_COLUMNS:
                row[col] = snapshot.get(col)

            row["label"] = 1 if rec.actual_outcome in _POSITIVE_OUTCOMES else 0
            data.append(row)

        metadata = {
            "records_total": total_records,
            "records_in_window": len(records),
            "window_start": window_start.isoformat(),
            "window_end": datetime.now(UTC).isoformat(),
        }
        return data, metadata

    # ------------------------------------------------------------------
    # Feature matrix
    # ------------------------------------------------------------------

    @staticmethod
    def _build_feature_matrix(
        data: list[dict[str, Any]],
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert list-of-dicts into (X, y) numpy arrays.
        Missing values are imputed with per-column median.
        """
        n = len(data)
        m = len(FEATURE_COLUMNS)

        X = np.full((n, m), np.nan, dtype=np.float64)  # noqa: N806
        y = np.zeros(n, dtype=np.int32)

        for i, row in enumerate(data):
            for j, col in enumerate(FEATURE_COLUMNS):
                val = row.get(col)
                if val is not None:
                    X[i, j] = float(val)
            y[i] = int(row["label"])

        # Impute missing with column medians
        for j in range(m):
            col_vals = X[:, j]
            mask = ~np.isnan(col_vals)
            if mask.any():
                median_val = float(np.median(col_vals[mask]))
                X[~mask, j] = median_val
            else:
                X[:, j] = 0.0  # fallback when entire column is missing

        return X, y

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _generate_version_string(self) -> str:
        """Generate a sequential model version string like 'v3.0-trained-2026-03-29'."""
        result = await self.db.execute(select(func.count()).select_from(ModelRegistry))
        count = result.scalar() or 0
        today = date.today().isoformat()
        return f"v{count + 1}.0-trained-{today}"

    @staticmethod
    def _mode_settings(mode: str) -> dict[str, int]:
        if mode == "fast":
            return {
                "cv_folds": settings.training_fast_cv_folds,
                "optuna_trials": settings.training_fast_optuna_trials,
                "max_duration_minutes": settings.training_fast_max_duration_minutes,
            }
        return {
            "cv_folds": settings.training_cv_folds,
            "optuna_trials": settings.training_optuna_trials,
            "max_duration_minutes": settings.training_max_duration_minutes,
        }
