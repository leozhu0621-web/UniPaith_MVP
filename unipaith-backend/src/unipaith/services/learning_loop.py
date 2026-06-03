"""Spec 67 §2/§6 — outcome ingestion (activates the dormant ml_loop substrate).

Records the labeled outcomes the learning loop trains on — real
(student, program, predicted-confidence, realized-outcome) pairs from
matches / applications / enrollment — instead of the `random.uniform`
fabrications (`seed_ml_outcomes:42`, smell #6). The actual training / isotonic
calibration is `67`'s later work; this is the **consent-gated ingestion** that
feeds it: a student whose `consent.training` is false contributes to NO training
set (46 §9 hard gate) — recording is simply skipped. Confidence flows
uncalibrated, and honestly says so, until enough real pairs exist (`65` §5).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.confidence_outcome import ConfidenceOutcomePair

# The isotonic calibrator (`confidence_calibrator`) can fit only above this many
# real pairs (67 §6); below it, Confidence flows uncalibrated.
MIN_PAIRS_FOR_CALIBRATION = 1000

# Realized outcomes that count as a "positive" label (the prediction held up).
POSITIVE_KINDS = frozenset({"applied", "admitted", "enrolled", "accepted_offer"})


class LearningLoopService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_confidence_outcome(
        self,
        *,
        student_id: UUID,
        program_id: UUID,
        predicted_confidence: float,
        outcome: int,
        outcome_kind: str,
        training_consent: bool,
        event_at: datetime | None = None,
    ) -> ConfidenceOutcomePair | None:
        """Record a predicted-confidence vs realized-outcome pair (the
        calibrator's training data). Returns None — recording **nothing** — when
        `training_consent` is false (46 §9: consent.training=false never trains).
        """
        if not training_consent:
            return None
        if outcome not in (0, 1):
            raise ValueError("outcome must be 0 or 1")
        pair = ConfidenceOutcomePair(
            student_id=student_id,
            program_id=program_id,
            predicted_confidence=predicted_confidence,
            outcome=outcome,
            outcome_kind=outcome_kind,
            event_at=event_at or datetime.now(UTC),
        )
        self.db.add(pair)
        await self.db.flush()
        return pair

    async def confidence_pair_count(self) -> int:
        res = await self.db.execute(select(func.count()).select_from(ConfidenceOutcomePair))
        return int(res.scalar_one())

    async def calibrator_ready(self) -> bool:
        """True once enough real pairs exist to fit the calibrator (67 §6).
        Until then the matcher's Confidence is honest-uncalibrated, not faked."""
        return await self.confidence_pair_count() >= MIN_PAIRS_FOR_CALIBRATION
