"""
Outcome Collector — records ground-truth outcomes from application decisions,
offer responses, and enrollments, linking them back to prediction logs for
model evaluation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import NotFoundException
from unipaith.models.application import Application, EnrollmentRecord, OfferLetter
from unipaith.models.matching import PredictionLog
from unipaith.models.ml_loop import OutcomeRecord

logger = logging.getLogger(__name__)


class OutcomeCollector:
    """Collects ground-truth outcomes and pairs them with prior predictions."""

    OUTCOME_CONFIDENCE: dict[str, Decimal] = {
        "application_decision": Decimal("0.70"),
        "offer_response": Decimal("0.85"),
        "enrollment": Decimal("1.00"),
    }

    DECISION_TO_OUTCOME: dict[str, str] = {
        "admitted": "admitted",
        "rejected": "rejected",
        "waitlisted": "waitlisted",
    }

    OFFER_RESPONSE_TO_OUTCOME: dict[str, str] = {
        "accepted": "enrolled",
        "declined": "declined",
    }

    ENROLLMENT_STATUS_TO_OUTCOME: dict[str, str] = {
        "enrolled": "enrolled",
        "deferred": "deferred",
        "withdrawn": "withdrawn",
    }

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def record_application_decision(self, application_id: UUID) -> OutcomeRecord | None:
        """Record an outcome from an application decision.

        Returns the created OutcomeRecord, or None if no matching prediction
        exists for this student+program pair.

        Raises:
            NotFoundException: if the application does not exist.
            BadRequestException: (not raised here but callers may check)
        """
        application = await self._load_or_raise(Application, application_id)
        if application.decision is None:
            logger.debug("Application %s has no decision yet, skipping", application_id)
            return None

        outcome_value = self.DECISION_TO_OUTCOME.get(application.decision)
        if outcome_value is None:
            logger.warning(
                "Unknown decision value '%s' for application %s",
                application.decision,
                application_id,
            )
            return None

        prediction = await self._find_prediction(application.student_id, application.program_id)
        if prediction is None:
            logger.debug(
                "No prediction found for student=%s program=%s",
                application.student_id,
                application.program_id,
            )
            return None

        existing = await self._find_existing_outcome(prediction.id, "application_decision")
        if existing is not None:
            logger.debug(
                "Outcome already recorded for prediction %s source=application_decision",
                prediction.id,
            )
            return existing

        record = OutcomeRecord(
            prediction_log_id=prediction.id,
            student_id=application.student_id,
            program_id=application.program_id,
            predicted_score=prediction.predicted_score,
            predicted_tier=prediction.predicted_tier,
            actual_outcome=outcome_value,
            outcome_source="application_decision",
            outcome_confidence=self.OUTCOME_CONFIDENCE["application_decision"],
            features_snapshot=prediction.features_used,
            outcome_recorded_at=datetime.now(UTC),
        )
        self.db.add(record)

        # Update the prediction log with the actual outcome
        prediction.actual_outcome = outcome_value
        prediction.outcome_recorded_at = datetime.now(UTC)

        await self.db.flush()
        logger.info(
            "Recorded application_decision outcome for prediction %s: %s",
            prediction.id,
            outcome_value,
        )
        return record

    async def record_offer_response(self, offer_id: UUID) -> OutcomeRecord | None:
        """Record an outcome from an offer letter response.

        Returns the created OutcomeRecord, or None if no matching prediction
        exists.

        Raises:
            NotFoundException: if the offer letter does not exist.
        """
        offer = await self._load_or_raise(OfferLetter, offer_id)
        if offer.student_response is None:
            logger.debug("Offer %s has no student response yet, skipping", offer_id)
            return None

        outcome_value = self.OFFER_RESPONSE_TO_OUTCOME.get(offer.student_response)
        if outcome_value is None:
            logger.warning(
                "Unknown student_response '%s' for offer %s",
                offer.student_response,
                offer_id,
            )
            return None

        # Load the parent application to get student_id and program_id
        application = await self._load_or_raise(Application, offer.application_id)

        prediction = await self._find_prediction(application.student_id, application.program_id)
        if prediction is None:
            return None

        existing = await self._find_existing_outcome(prediction.id, "offer_response")
        if existing is not None:
            return existing

        record = OutcomeRecord(
            prediction_log_id=prediction.id,
            student_id=application.student_id,
            program_id=application.program_id,
            predicted_score=prediction.predicted_score,
            predicted_tier=prediction.predicted_tier,
            actual_outcome=outcome_value,
            outcome_source="offer_response",
            outcome_confidence=self.OUTCOME_CONFIDENCE["offer_response"],
            features_snapshot=prediction.features_used,
            outcome_recorded_at=datetime.now(UTC),
        )
        self.db.add(record)

        prediction.actual_outcome = outcome_value
        prediction.outcome_recorded_at = datetime.now(UTC)

        await self.db.flush()
        logger.info(
            "Recorded offer_response outcome for prediction %s: %s",
            prediction.id,
            outcome_value,
        )
        return record

    async def record_enrollment(self, enrollment_id: UUID) -> OutcomeRecord | None:
        """Record an outcome from an enrollment record.

        Returns the created OutcomeRecord, or None if no matching prediction
        exists.

        Raises:
            NotFoundException: if the enrollment record does not exist.
        """
        enrollment = await self._load_or_raise(EnrollmentRecord, enrollment_id)
        if enrollment.enrollment_status is None:
            logger.debug("Enrollment %s has no status yet, skipping", enrollment_id)
            return None

        outcome_value = self.ENROLLMENT_STATUS_TO_OUTCOME.get(enrollment.enrollment_status)
        if outcome_value is None:
            logger.warning(
                "Unknown enrollment_status '%s' for enrollment %s",
                enrollment.enrollment_status,
                enrollment_id,
            )
            return None

        prediction = await self._find_prediction(enrollment.student_id, enrollment.program_id)
        if prediction is None:
            return None

        existing = await self._find_existing_outcome(prediction.id, "enrollment")
        if existing is not None:
            return existing

        record = OutcomeRecord(
            prediction_log_id=prediction.id,
            student_id=enrollment.student_id,
            program_id=enrollment.program_id,
            predicted_score=prediction.predicted_score,
            predicted_tier=prediction.predicted_tier,
            actual_outcome=outcome_value,
            outcome_source="enrollment",
            outcome_confidence=self.OUTCOME_CONFIDENCE["enrollment"],
            features_snapshot=prediction.features_used,
            outcome_recorded_at=datetime.now(UTC),
        )
        self.db.add(record)

        prediction.actual_outcome = outcome_value
        prediction.outcome_recorded_at = datetime.now(UTC)

        await self.db.flush()
        logger.info(
            "Recorded enrollment outcome for prediction %s: %s",
            prediction.id,
            outcome_value,
        )
        return record

    async def backfill_outcomes(self) -> dict:
        """Backfill outcome records for all existing decisions, offers, and
        enrollments that do not yet have corresponding OutcomeRecords.

        Returns:
            dict with keys decisions_processed, offers_processed,
            enrollments_processed.
        """
        decisions_processed = 0
        offers_processed = 0
        enrollments_processed = 0

        # 1) Application decisions without outcome records
        (
            select(Application)
            .where(Application.decision.isnot(None))
            .where(
                ~Application.id.in_(
                    select(OutcomeRecord.program_id).where(
                        OutcomeRecord.outcome_source == "application_decision"
                    )
                    # Use a correlated subquery on the prediction_log instead
                )
            )
        )
        # Simpler approach: load all applications with decisions
        apps_stmt = select(Application).where(Application.decision.isnot(None))
        result = await self.db.execute(apps_stmt)
        applications = result.scalars().all()

        for app in applications:
            record = await self.record_application_decision(app.id)
            if record is not None:
                decisions_processed += 1

        # 2) Offer responses
        offers_stmt = select(OfferLetter).where(OfferLetter.student_response.isnot(None))
        result = await self.db.execute(offers_stmt)
        offers = result.scalars().all()

        for offer in offers:
            record = await self.record_offer_response(offer.id)
            if record is not None:
                offers_processed += 1

        # 3) Enrollments
        enrollments_stmt = select(EnrollmentRecord).where(
            EnrollmentRecord.enrollment_status.isnot(None)
        )
        result = await self.db.execute(enrollments_stmt)
        enrollments = result.scalars().all()

        for enrollment in enrollments:
            record = await self.record_enrollment(enrollment.id)
            if record is not None:
                enrollments_processed += 1

        logger.info(
            "Backfill complete: decisions=%d offers=%d enrollments=%d",
            decisions_processed,
            offers_processed,
            enrollments_processed,
        )
        return {
            "decisions_processed": decisions_processed,
            "offers_processed": offers_processed,
            "enrollments_processed": enrollments_processed,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _find_prediction(self, student_id: UUID, program_id: UUID) -> PredictionLog | None:
        """Find the most recent PredictionLog for a student+program pair."""
        stmt = (
            select(PredictionLog)
            .where(
                and_(
                    PredictionLog.student_id == student_id,
                    PredictionLog.program_id == program_id,
                )
            )
            .order_by(PredictionLog.predicted_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_existing_outcome(
        self, prediction_log_id: UUID, outcome_source: str
    ) -> OutcomeRecord | None:
        """Check for a duplicate OutcomeRecord for this prediction+source."""
        stmt = select(OutcomeRecord).where(
            and_(
                OutcomeRecord.prediction_log_id == prediction_log_id,
                OutcomeRecord.outcome_source == outcome_source,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _load_or_raise(self, model_class: type, entity_id: UUID):
        """Load an entity by primary key or raise NotFoundException."""
        entity = await self.db.get(model_class, entity_id)
        if entity is None:
            raise NotFoundException(f"{model_class.__name__} {entity_id} not found")
        return entity
