"""
ABTestManager — Deterministic A/B test assignment and experiment evaluation.

Provides sticky, hash-based variant assignment so each student always sees
the same model version within an experiment.  Evaluation computes conversion
rates and lift to decide whether a challenger model should be promoted.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.matching import ModelRegistry
from unipaith.models.ml_loop import ABTestAssignment, OutcomeRecord

logger = logging.getLogger(__name__)

# Outcomes treated as conversions in experiment evaluation
_POSITIVE_OUTCOMES = {"admitted", "enrolled"}
_NEGATIVE_OUTCOMES = {"rejected", "declined"}


class ABTestManager:
    """Hash-based, sticky A/B test manager for model experiments."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Model selection
    # ------------------------------------------------------------------

    async def get_model_for_student(
        self,
        student_id: UUID,
        experiment_name: str | None = None,
    ) -> str:
        """
        Determine which model version a student should use.

        If an active experiment exists the student is assigned a sticky
        variant (control or challenger).  Otherwise the active production
        model version is returned.
        """
        # Resolve experiment name
        if experiment_name is None:
            experiment_name = await self._get_active_experiment()

        if experiment_name is None:
            return await self._get_active_version()

        # Check for existing assignment
        result = await self.db.execute(
            select(ABTestAssignment).where(
                ABTestAssignment.student_id == student_id,
                ABTestAssignment.experiment_name == experiment_name,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            return existing.model_version

        # Assign a new variant
        traffic_pct = settings.model_ab_test_traffic_pct
        variant = self._assign_variant(student_id, experiment_name, traffic_pct)

        if variant == "challenger":
            model_version = await self._get_challenger_version(experiment_name)
        else:
            model_version = await self._get_active_version()

        assignment = ABTestAssignment(
            student_id=student_id,
            experiment_name=experiment_name,
            variant=variant,
            model_version=model_version,
        )
        self.db.add(assignment)
        await self.db.flush()

        logger.info(
            "Student %s assigned to variant '%s' (model %s) in experiment '%s'",
            student_id,
            variant,
            model_version,
            experiment_name,
        )

        return model_version

    # ------------------------------------------------------------------
    # Experiment management
    # ------------------------------------------------------------------

    async def create_experiment(
        self,
        experiment_name: str,
        challenger_version: str,
        traffic_pct: float | None = None,
    ) -> dict:
        """
        Define a new A/B experiment between the active model and a challenger.

        Does not persist a separate experiment record — the experiment is
        implied by ABTestAssignment rows sharing the same experiment_name.
        """
        # Verify challenger exists
        result = await self.db.execute(
            select(ModelRegistry).where(ModelRegistry.model_version == challenger_version)
        )
        challenger = result.scalar_one_or_none()
        if challenger is None:
            raise NotFoundException(f"Challenger model version '{challenger_version}' not found")

        active_version = await self._get_active_version()
        pct = traffic_pct if traffic_pct is not None else settings.model_ab_test_traffic_pct

        logger.info(
            "Experiment '%s' created — control=%s, challenger=%s, traffic=%.0f%%",
            experiment_name,
            active_version,
            challenger_version,
            pct * 100,
        )

        return {
            "experiment_name": experiment_name,
            "control": active_version,
            "challenger": challenger_version,
            "traffic_pct": pct,
        }

    # ------------------------------------------------------------------
    # Experiment evaluation
    # ------------------------------------------------------------------

    async def evaluate_experiment(self, experiment_name: str) -> dict:
        """
        Evaluate an experiment by comparing conversion rates between
        control and challenger groups.
        """
        # Load all assignments for this experiment
        result = await self.db.execute(
            select(ABTestAssignment).where(ABTestAssignment.experiment_name == experiment_name)
        )
        assignments = result.scalars().all()

        if not assignments:
            raise NotFoundException(f"No assignments found for experiment '{experiment_name}'")

        # Group student IDs by variant
        control_student_ids: list[UUID] = []
        challenger_student_ids: list[UUID] = []

        for a in assignments:
            if a.variant == "control":
                control_student_ids.append(a.student_id)
            else:
                challenger_student_ids.append(a.student_id)

        # Compute conversion stats for each group
        control_stats = await self._compute_group_stats(control_student_ids)
        challenger_stats = await self._compute_group_stats(challenger_student_ids)

        # Check minimum sample size
        min_samples = settings.model_ab_test_min_samples
        if control_stats["total"] < min_samples or challenger_stats["total"] < min_samples:
            return {
                "status": "insufficient_data",
                "control": control_stats,
                "challenger": challenger_stats,
                "min_samples_required": min_samples,
            }

        # Compute lift
        control_rate = control_stats["conversion_rate"]
        challenger_rate = challenger_stats["conversion_rate"]

        if control_rate > 0:
            lift = (challenger_rate - control_rate) / control_rate
        else:
            lift = 1.0 if challenger_rate > 0 else 0.0

        recommendation = "promote_challenger" if lift > 0 else "keep_control"

        logger.info(
            "Experiment '%s' evaluated — lift=%.4f, recommendation=%s",
            experiment_name,
            lift,
            recommendation,
        )

        return {
            "status": "evaluated",
            "control": control_stats,
            "challenger": challenger_stats,
            "lift": lift,
            "recommendation": recommendation,
        }

    # ------------------------------------------------------------------
    # Variant assignment (deterministic)
    # ------------------------------------------------------------------

    @staticmethod
    def _assign_variant(
        student_id: UUID,
        experiment_name: str,
        traffic_pct: float,
    ) -> str:
        """
        Deterministic hash-based variant assignment.

        Uses SHA-256 of ``student_id:experiment_name`` so the same student
        always lands in the same bucket for a given experiment.
        """
        hash_input = f"{student_id}:{experiment_name}".encode()
        hash_hex = hashlib.sha256(hash_input).hexdigest()
        bucket = int(hash_hex[:8], 16) % 100

        if bucket < int(traffic_pct * 100):
            return "challenger"
        return "control"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_active_experiment(self) -> str | None:
        """
        Return the name of any experiment with assignments in the last 7 days,
        or None if no active experiment exists.
        """
        cutoff = datetime.now(UTC) - timedelta(days=7)
        result = await self.db.execute(
            select(ABTestAssignment.experiment_name)
            .where(ABTestAssignment.assigned_at >= cutoff)
            .order_by(ABTestAssignment.assigned_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row

    async def _get_active_version(self) -> str:
        """Return the active model version, falling back to 'v1.0-mvp'."""
        result = await self.db.execute(
            select(ModelRegistry).where(ModelRegistry.is_active.is_(True)).limit(1)
        )
        model = result.scalar_one_or_none()
        return model.model_version if model is not None else "v1.0-mvp"

    async def _get_challenger_version(self, experiment_name: str) -> str:
        """
        Find the challenger model version for an experiment by looking up an
        existing challenger assignment, or falling back to the latest
        non-active model.
        """
        result = await self.db.execute(
            select(ABTestAssignment.model_version)
            .where(
                ABTestAssignment.experiment_name == experiment_name,
                ABTestAssignment.variant == "challenger",
            )
            .limit(1)
        )
        version = result.scalar_one_or_none()
        if version is not None:
            return version

        # Fallback: latest non-active, non-retired model
        model_result = await self.db.execute(
            select(ModelRegistry)
            .where(
                ModelRegistry.is_active.is_(False),
                ModelRegistry.retired_at.is_(None),
            )
            .order_by(ModelRegistry.created_at.desc())
            .limit(1)
        )
        model = model_result.scalar_one_or_none()
        if model is not None:
            return model.model_version

        raise BadRequestException(f"No challenger model found for experiment '{experiment_name}'")

    async def _compute_group_stats(self, student_ids: list[UUID]) -> dict:
        """Compute conversion rate for a set of student IDs based on OutcomeRecord."""
        if not student_ids:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "conversion_rate": 0.0,
            }

        result = await self.db.execute(
            select(OutcomeRecord).where(
                OutcomeRecord.student_id.in_(student_ids),
                OutcomeRecord.actual_outcome.in_(list(_POSITIVE_OUTCOMES | _NEGATIVE_OUTCOMES)),
            )
        )
        records = result.scalars().all()

        positive = sum(1 for r in records if r.actual_outcome in _POSITIVE_OUTCOMES)
        negative = sum(1 for r in records if r.actual_outcome in _NEGATIVE_OUTCOMES)
        total = positive + negative

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "conversion_rate": positive / total if total > 0 else 0.0,
        }
