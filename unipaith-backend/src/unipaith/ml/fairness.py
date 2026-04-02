"""
Fairness Checker — evaluates model fairness across protected demographic
attributes using demographic parity, equal opportunity, and equalized odds
metrics with a configurable fairness dial.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.ml_loop import FairnessReport
from unipaith.models.student import StudentProfile

logger = logging.getLogger(__name__)

# Outcomes considered "positive" for fairness analysis
_POSITIVE_OUTCOMES = {"admitted", "enrolled"}
_NEGATIVE_OUTCOMES = {"rejected", "declined", "withdrawn"}

# Minimum samples per group to include in fairness analysis
_MIN_GROUP_SIZE = 5


class FairnessChecker:
    """Evaluates model fairness across protected attributes."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def run_fairness_check(
        self,
        model_version: str,
        outcomes: list[dict],
        evaluation_run_id: UUID | None = None,
        training_run_id: UUID | None = None,
    ) -> list[FairnessReport]:
        """Run fairness checks across all configured protected attributes.

        Args:
            model_version: The model version being evaluated.
            outcomes: List of outcome dicts (from ModelEvaluator._collect_labeled_outcomes)
                with keys: predicted_score, predicted_tier, actual_outcome,
                outcome_confidence, student_id, program_id.
            evaluation_run_id: Optional link to the EvaluationRun.
            training_run_id: Optional link to the TrainingRun.

        Returns:
            List of persisted FairnessReport records (one per attribute
            that had sufficient data).
        """
        if not outcomes:
            logger.debug("No outcomes provided for fairness check, skipping")
            return []

        # Collect all student IDs and load demographics once
        student_ids = list({UUID(o["student_id"]) for o in outcomes})
        demographics = await self._load_demographics(student_ids)

        reports: list[FairnessReport] = []
        for attribute in settings.fairness_protected_attributes:
            report = self._check_attribute(
                model_version=model_version,
                attribute=attribute,
                outcomes=outcomes,
                demographics=demographics,
                evaluation_run_id=evaluation_run_id,
                training_run_id=training_run_id,
            )
            if report is not None:
                self.db.add(report)
                reports.append(report)

        if reports:
            await self.db.flush()

        passed_count = sum(1 for r in reports if r.passed)
        logger.info(
            "Fairness check for %s: %d attributes checked, %d passed, %d failed",
            model_version,
            len(reports),
            passed_count,
            len(reports) - passed_count,
        )
        return reports

    # ------------------------------------------------------------------
    # Core fairness computation
    # ------------------------------------------------------------------

    def _check_attribute(
        self,
        model_version: str,
        attribute: str,
        outcomes: list[dict],
        demographics: dict[str, dict],
        evaluation_run_id: UUID | None = None,
        training_run_id: UUID | None = None,
    ) -> FairnessReport | None:
        """Check fairness for a single protected attribute.

        Groups outcomes by the demographic attribute value and computes
        demographic parity, equal opportunity, and equalized odds differences.

        Returns None if fewer than 2 groups have at least _MIN_GROUP_SIZE
        members.
        """
        # Group outcomes by demographic attribute value
        groups: dict[str, list[dict]] = {}
        for o in outcomes:
            student_id = o["student_id"]
            demo = demographics.get(student_id, {})
            group_value = demo.get(attribute)
            if group_value is None:
                continue  # Skip students without this attribute
            group_value = str(group_value)
            if group_value not in groups:
                groups[group_value] = []
            groups[group_value].append(o)

        # Filter groups below minimum size
        groups = {k: v for k, v in groups.items() if len(v) >= _MIN_GROUP_SIZE}

        if len(groups) < 2:
            logger.debug(
                "Fewer than 2 groups with >=%d samples for attribute '%s', skipping fairness check",
                _MIN_GROUP_SIZE,
                attribute,
            )
            return None

        # Compute per-group metrics
        group_metrics: dict[str, dict] = {}
        positive_rates: list[float] = []
        tpr_values: list[float] = []
        fpr_values: list[float] = []

        for group_name, group_outcomes in groups.items():
            total = len(group_outcomes)
            positives = [o for o in group_outcomes if o["actual_outcome"] in _POSITIVE_OUTCOMES]
            negatives = [o for o in group_outcomes if o["actual_outcome"] in _NEGATIVE_OUTCOMES]

            positive_count = len(positives)
            negative_count = len(negatives)
            classified_count = positive_count + negative_count

            # Positive rate (demographic parity)
            pos_rate = positive_count / classified_count if classified_count > 0 else 0.0
            positive_rates.append(pos_rate)

            # True Positive Rate (equal opportunity)
            # Among actually-positive cases, what fraction did the model
            # predict as positive (tier 1)?
            if positive_count > 0:
                true_positives = sum(1 for o in positives if o["predicted_tier"] <= 1)
                tpr = true_positives / positive_count
            else:
                tpr = 0.0
            tpr_values.append(tpr)

            # False Positive Rate
            # Among actually-negative cases, what fraction did the model
            # predict as positive (tier 1)?
            if negative_count > 0:
                false_positives = sum(1 for o in negatives if o["predicted_tier"] <= 1)
                fpr = false_positives / negative_count
            else:
                fpr = 0.0
            fpr_values.append(fpr)

            avg_score = (
                sum(o["predicted_score"] for o in group_outcomes) / total if total > 0 else 0.0
            )

            group_metrics[group_name] = {
                "count": total,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "positive_rate": round(pos_rate, 4),
                "tpr": round(tpr, 4),
                "fpr": round(fpr, 4),
                "avg_predicted_score": round(avg_score, 4),
            }

        # Compute fairness differences
        demographic_parity_diff = max(positive_rates) - min(positive_rates)
        equal_opportunity_diff = max(tpr_values) - min(tpr_values)
        tpr_diff = max(tpr_values) - min(tpr_values)
        fpr_diff = max(fpr_values) - min(fpr_values)
        equalized_odds_diff = max(tpr_diff, fpr_diff)

        # Apply fairness dial
        # max_allowed = 1.0 - dial * (1.0 - max_disparity)
        # dial=0.0 -> max_allowed=1.0 (most lenient)
        # dial=1.0 -> max_allowed=max_disparity (most strict)
        dial = settings.fairness_dial
        max_disparity = settings.fairness_max_disparity
        max_allowed = 1.0 - dial * (1.0 - max_disparity)

        passed = demographic_parity_diff <= max_allowed

        violation_details = None
        if not passed:
            violation_details = {
                "demographic_parity_diff": round(demographic_parity_diff, 4),
                "max_allowed": round(max_allowed, 4),
                "dial_setting": dial,
                "group_positive_rates": {k: v["positive_rate"] for k, v in group_metrics.items()},
            }

        report = FairnessReport(
            model_version=model_version,
            evaluation_run_id=evaluation_run_id,
            training_run_id=training_run_id,
            protected_attribute=attribute,
            group_metrics=group_metrics,
            demographic_parity_diff=Decimal(str(round(demographic_parity_diff, 4))),
            equal_opportunity_diff=Decimal(str(round(equal_opportunity_diff, 4))),
            equalized_odds_diff=Decimal(str(round(equalized_odds_diff, 4))),
            fairness_dial_setting=Decimal(str(dial)),
            passed=passed,
            violation_details=violation_details,
        )

        if not passed:
            logger.warning(
                "Fairness violation for %s on attribute '%s': "
                "demographic_parity_diff=%.4f > max_allowed=%.4f",
                model_version,
                attribute,
                demographic_parity_diff,
                max_allowed,
            )
        return report

    # ------------------------------------------------------------------
    # Demographics loading
    # ------------------------------------------------------------------

    async def _load_demographics(self, student_ids: list[UUID]) -> dict[str, dict]:
        """Load demographic data for a set of students.

        Returns a dict mapping str(student_id) to a dict with keys:
        nationality, gender, ethnicity, first_generation.

        Note: gender, ethnicity, and first_generation are not in the current
        StudentProfile schema. They return None for MVP; nationality is the
        only real attribute available.
        """
        if not student_ids:
            return {}

        stmt = select(
            StudentProfile.id,
            StudentProfile.nationality,
        ).where(StudentProfile.id.in_(student_ids))

        result = await self.db.execute(stmt)
        rows = result.all()

        demographics: dict[str, dict] = {}
        for row in rows:
            demographics[str(row.id)] = {
                "nationality": row.nationality,
                # Not in current schema -- return None for MVP
                "gender": None,
                "ethnicity": None,
                "first_generation": None,
            }
        return demographics
