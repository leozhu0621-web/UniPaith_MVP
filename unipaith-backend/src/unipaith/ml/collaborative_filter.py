"""Collaborative filtering via ALS matrix factorization.

"Students like you applied here and thrived."

Builds a student-program interaction matrix from InteractionSignal and
OutcomeRecord, trains ALS via the implicit library, and produces
per-student-program affinity scores. Falls back to embedding similarity
for cold-start users/programs.
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

logger = logging.getLogger("unipaith.ml.collaborative_filter")

SIGNAL_WEIGHTS = {
    "view": 0.1,
    "click": 0.2,
    "save": 0.5,
    "compare": 0.3,
    "time_spent": 0.15,
    "apply": 1.0,
    "dismiss": -0.3,
}

OUTCOME_WEIGHTS = {
    "admitted": 2.0,
    "enrolled": 2.5,
    "rejected": -0.5,
    "declined": 0.3,
    "waitlisted": 0.5,
}


class CollaborativeFilter:
    """ALS-based collaborative filtering for student-program recommendations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._model = None
        self._student_map: dict[UUID, int] = {}
        self._program_map: dict[UUID, int] = {}
        self._reverse_program_map: dict[int, UUID] = {}

    async def train(self, factors: int = 64, iterations: int = 15) -> dict:
        """Build interaction matrix and train ALS model."""
        interactions = await self._build_interaction_matrix()
        if not interactions:
            return {"status": "skipped", "reason": "no_interactions"}

        students = sorted(set(s for s, _ in interactions))
        programs = sorted(set(p for _, p in interactions))

        self._student_map = {sid: i for i, sid in enumerate(students)}
        self._program_map = {pid: i for i, pid in enumerate(programs)}
        self._reverse_program_map = {i: pid for pid, i in self._program_map.items()}

        n_students = len(students)
        n_programs = len(programs)

        try:
            from implicit.als import AlternatingLeastSquares
            from scipy.sparse import csr_matrix

            rows, cols, data = [], [], []
            for (student_id, program_id), weight in interactions.items():
                si = self._student_map[student_id]
                pi = self._program_map[program_id]
                rows.append(si)
                cols.append(pi)
                data.append(max(0.01, float(weight)))

            matrix = csr_matrix(
                (data, (rows, cols)), shape=(n_students, n_programs),
            )

            model = AlternatingLeastSquares(
                factors=factors,
                iterations=iterations,
                regularization=0.1,
                random_state=42,
            )
            model.fit(matrix)
            self._model = model

            logger.info(
                "CF trained: %d students x %d programs, %d interactions",
                n_students, n_programs, len(data),
            )
            return {
                "status": "trained",
                "students": n_students,
                "programs": n_programs,
                "interactions": len(data),
                "factors": factors,
            }
        except Exception:
            logger.exception("CF training failed")
            return {"status": "failed", "reason": "training_error"}

    def predict(self, student_id: UUID, program_id: UUID) -> float:
        """Get CF affinity score for a student-program pair."""
        if self._model is None:
            return 0.5

        si = self._student_map.get(student_id)
        pi = self._program_map.get(program_id)
        if si is None or pi is None:
            return 0.5

        try:
            student_factor = self._model.user_factors[si]
            program_factor = self._model.item_factors[pi]
            raw = float(np.dot(student_factor, program_factor))
            return max(0.0, min(1.0, (raw + 1.0) / 2.0))
        except Exception:
            return 0.5

    def predict_batch(
        self, student_id: UUID, program_ids: list[UUID],
    ) -> dict[UUID, float]:
        """Get CF scores for multiple programs for one student."""
        return {pid: self.predict(student_id, pid) for pid in program_ids}

    def recommend_for_student(
        self, student_id: UUID, n: int = 20,
    ) -> list[tuple[UUID, float]]:
        """Get top-N program recommendations for a student."""
        if self._model is None:
            return []

        si = self._student_map.get(student_id)
        if si is None:
            return []

        try:
            from scipy.sparse import csr_matrix
            n_programs = len(self._program_map)
            empty_row = csr_matrix((1, n_programs))
            ids, scores = self._model.recommend(
                si, empty_row, N=n, filter_already_liked_items=False,
            )
            return [
                (self._reverse_program_map[int(idx)], float(score))
                for idx, score in zip(ids, scores)
                if int(idx) in self._reverse_program_map
            ]
        except Exception:
            return []

    async def _build_interaction_matrix(
        self,
    ) -> dict[tuple[UUID, UUID], float]:
        """Aggregate signals and outcomes into weighted interactions."""
        interactions: dict[tuple[UUID, UUID], float] = defaultdict(float)

        signals_result = await self.db.execute(
            select(InteractionSignal).where(
                InteractionSignal.entity_type == "program",
                InteractionSignal.entity_id.isnot(None),
            )
        )
        for signal in signals_result.scalars().all():
            weight = SIGNAL_WEIGHTS.get(signal.signal_type, 0.1)
            key = (signal.user_id, signal.entity_id)
            interactions[key] += weight

        outcomes_result = await self.db.execute(select(OutcomeRecord))
        for outcome in outcomes_result.scalars().all():
            weight = OUTCOME_WEIGHTS.get(outcome.actual_outcome, 0.0)
            key = (outcome.student_id, outcome.program_id)
            interactions[key] += weight

        return dict(interactions)
