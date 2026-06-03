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

# Outcome kinds allowed by the confidence_outcome_pairs CHECK constraint.
ALLOWED_OUTCOME_KINDS = frozenset({"applied", "accepted", "enrolled", "aged_out"})
# Kinds that count as a "positive" label (the predicted match held up); aged_out
# (window passed without the positive event) is the negative.
POSITIVE_KINDS = frozenset({"applied", "accepted", "enrolled"})


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
        if outcome_kind not in ALLOWED_OUTCOME_KINDS:
            raise ValueError(f"outcome_kind must be one of {sorted(ALLOWED_OUTCOME_KINDS)}")
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

    async def record_outcome_for(
        self,
        *,
        student_id: UUID,
        program_id: UUID,
        outcome_kind: str,
        outcome: int = 1,
    ) -> ConfidenceOutcomePair | None:
        """Convenience hook for the application/enrollment paths: look up the
        prediction (``MatchResult.confidence_score``) and the student's training
        consent for this (student, program), then record the labeled pair.

        No-op (returns None) when there is no prior match prediction to label or
        the student hasn't consented to training (46 §9). Best-effort by design —
        callers wrap it so a recording failure never breaks the user action.
        """
        from unipaith.models.matching import MatchResult
        from unipaith.models.student import StudentDataConsent

        mr = await self.db.scalar(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id == program_id,
            )
        )
        if mr is None or mr.confidence_score is None:
            return None
        consent = await self.db.scalar(
            select(StudentDataConsent).where(StudentDataConsent.student_id == student_id)
        )
        return await self.record_confidence_outcome(
            student_id=student_id,
            program_id=program_id,
            predicted_confidence=float(mr.confidence_score),
            outcome=outcome,
            outcome_kind=outcome_kind,
            training_consent=bool(consent and consent.consent_training),
        )

    async def confidence_pair_count(self) -> int:
        res = await self.db.execute(select(func.count()).select_from(ConfidenceOutcomePair))
        return int(res.scalar_one())

    async def calibrator_ready(self) -> bool:
        """True once enough real pairs exist to fit the calibrator (67 §6).
        Until then the matcher's Confidence is honest-uncalibrated, not faked."""
        return await self.confidence_pair_count() >= MIN_PAIRS_FOR_CALIBRATION
