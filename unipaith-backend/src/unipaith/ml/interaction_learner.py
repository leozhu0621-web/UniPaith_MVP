"""Contextual bandit for interaction learning.

Learns what each student responds to from their behavior signals.
Some students want safety schools, some want reaches, some want exploration.
Uses Thompson sampling for explore/exploit balance.

Signal rewards:
  view=+0.1, click=+0.2, save=+0.5, compare=+0.3,
  apply=+1.0, admit=+2.0, dismiss=-0.3
"""

from __future__ import annotations

import logging
from collections import defaultdict
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.knowledge import InteractionSignal
from unipaith.models.ml_loop import OutcomeRecord

logger = logging.getLogger("unipaith.ml.interaction_learner")

REWARD_MAP = {
    "view": 0.1,
    "click": 0.2,
    "save": 0.5,
    "compare": 0.3,
    "time_spent": 0.15,
    "apply": 1.0,
    "dismiss": -0.3,
    "admitted": 2.0,
    "enrolled": 2.5,
    "rejected": -0.5,
}


class InteractionLearner:
    """Thompson-sampling contextual bandit over student-program interactions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._alpha: dict[tuple[UUID, UUID], float] = defaultdict(lambda: 1.0)
        self._beta: dict[tuple[UUID, UUID], float] = defaultdict(lambda: 1.0)
        self._student_profile: dict[UUID, dict] = {}

    async def train(self) -> dict:
        """Learn from historical interactions and outcomes."""
        n_signals = 0
        n_outcomes = 0

        signals_result = await self.db.execute(
            select(InteractionSignal).where(
                InteractionSignal.entity_type == "program",
                InteractionSignal.entity_id.isnot(None),
            )
        )
        for signal in signals_result.scalars().all():
            if signal.entity_id is None:
                continue
            reward = REWARD_MAP.get(signal.signal_type, 0.0)
            key = (signal.user_id, signal.entity_id)
            if reward > 0:
                self._alpha[key] += reward
            elif reward < 0:
                self._beta[key] += abs(reward)
            n_signals += 1

            profile = self._student_profile.setdefault(
                signal.user_id,
                {
                    "total_views": 0,
                    "total_saves": 0,
                    "total_applies": 0,
                    "total_dismisses": 0,
                    "explore_tendency": 0.5,
                },
            )
            if signal.signal_type == "view":
                profile["total_views"] += 1
            elif signal.signal_type == "save":
                profile["total_saves"] += 1
            elif signal.signal_type == "apply":
                profile["total_applies"] += 1
            elif signal.signal_type == "dismiss":
                profile["total_dismisses"] += 1

        outcomes_result = await self.db.execute(select(OutcomeRecord))
        for outcome in outcomes_result.scalars().all():
            reward = REWARD_MAP.get(outcome.actual_outcome, 0.0)
            key = (outcome.student_id, outcome.program_id)
            if reward > 0:
                self._alpha[key] += reward
            elif reward < 0:
                self._beta[key] += abs(reward)
            n_outcomes += 1

        for uid, profile in self._student_profile.items():
            total = max(profile["total_views"], 1)
            save_rate = profile["total_saves"] / total
            dismiss_rate = profile["total_dismisses"] / total
            profile["explore_tendency"] = max(0.1, min(0.9, 0.5 + save_rate - dismiss_rate))

        logger.info("Bandit trained: %d signals, %d outcomes", n_signals, n_outcomes)
        return {"status": "trained", "signals": n_signals, "outcomes": n_outcomes}

    def predict(self, student_id: UUID, program_id: UUID) -> float:
        """Thompson sampling prediction for a student-program pair."""
        key = (student_id, program_id)
        alpha = self._alpha[key]
        beta = self._beta[key]

        try:
            sample = np.random.beta(alpha, beta)
        except Exception:
            sample = 0.5

        explore = self._get_explore_tendency(student_id)
        if np.random.random() < explore * 0.1:
            sample = 0.5 + np.random.uniform(-0.2, 0.2)

        return float(max(0.0, min(1.0, sample)))

    def predict_batch(
        self,
        student_id: UUID,
        program_ids: list[UUID],
    ) -> dict[UUID, float]:
        """Get bandit scores for multiple programs."""
        return {pid: self.predict(student_id, pid) for pid in program_ids}

    def update(
        self,
        student_id: UUID,
        program_id: UUID,
        signal_type: str,
    ) -> None:
        """Online update from a new interaction signal."""
        reward = REWARD_MAP.get(signal_type, 0.0)
        key = (student_id, program_id)
        if reward > 0:
            self._alpha[key] += reward
        elif reward < 0:
            self._beta[key] += abs(reward)

    def _get_explore_tendency(self, student_id: UUID) -> float:
        profile = self._student_profile.get(student_id)
        if profile is None:
            return 0.5
        return profile.get("explore_tendency", 0.5)

    def get_student_behavior_profile(self, student_id: UUID) -> dict:
        """Get the learned behavior profile for a student."""
        return self._student_profile.get(
            student_id,
            {
                "total_views": 0,
                "total_saves": 0,
                "total_applies": 0,
                "total_dismisses": 0,
                "explore_tendency": 0.5,
            },
        )
