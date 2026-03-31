"""
Interview service — scheduling, confirmation, completion, and scoring
for admissions interviews.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import (
    Application,
    Interview,
    InterviewScore,
)

logger = logging.getLogger(__name__)


class InterviewService:
    """Manages interview lifecycle for the admissions pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Interview scheduling
    # ------------------------------------------------------------------

    async def propose_interview(
        self,
        application_id: UUID,
        interviewer_id: UUID,
        interview_type: str,
        proposed_times: list[str],
        duration_minutes: int = 30,
        location_or_link: str | None = None,
    ) -> Interview:
        """Create a new interview proposal for an application.

        Args:
            application_id: The application being interviewed.
            interviewer_id: The reviewer conducting the interview.
            interview_type: Type of interview (e.g. ``"phone"``, ``"video"``,
                ``"in_person"``).
            proposed_times: List of ISO 8601 datetime strings representing
                available time slots.
            duration_minutes: Expected length of the interview.
            location_or_link: Physical address or video-conferencing link.

        Returns:
            The newly created :class:`Interview` with status ``proposed``.

        Raises:
            BadRequestException: If no proposed times are provided.
        """
        if not proposed_times:
            raise BadRequestException("At least one proposed time is required")

        # Verify application exists
        app_result = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        if not app_result.scalar_one_or_none():
            raise NotFoundException("Application not found")

        interview = Interview(
            application_id=application_id,
            interviewer_id=interviewer_id,
            interview_type=interview_type,
            proposed_times=proposed_times,
            duration_minutes=duration_minutes,
            location_or_link=location_or_link,
            status="proposed",
        )
        self.db.add(interview)
        await self.db.flush()
        return interview

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    async def list_application_interviews(self, application_id: UUID) -> list[Interview]:
        """List all interviews associated with an application."""
        result = await self.db.execute(
            select(Interview).where(Interview.application_id == application_id)
        )
        return list(result.scalars().all())

    async def get_student_interviews(self, student_id: UUID) -> list[Interview]:
        """Get all interviews across all of a student's applications.

        Joins through :class:`Application` to find every interview linked to
        applications owned by the given student.
        """
        result = await self.db.execute(
            select(Interview)
            .join(Application, Interview.application_id == Application.id)
            .where(Application.student_id == student_id)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Student actions
    # ------------------------------------------------------------------

    async def confirm_time(
        self, student_id: UUID, interview_id: UUID, confirmed_time: str
    ) -> Interview:
        """Student confirms one of the proposed interview times.

        Validates that the ``confirmed_time`` is among the original proposed
        times, then sets the interview status to ``confirmed`` and updates the
        parent application status to ``interview``.

        Args:
            student_id: The student confirming.
            interview_id: The interview to confirm.
            confirmed_time: An ISO 8601 datetime string matching one of the
                proposed times.

        Returns:
            The updated :class:`Interview`.

        Raises:
            NotFoundException: If the interview does not exist or does not
                belong to one of the student's applications.
            BadRequestException: If the interview is not in ``proposed`` status
                or the chosen time is not among the proposed options.
        """
        interview = await self._get_student_interview(student_id, interview_id)

        if interview.status != "proposed":
            raise BadRequestException("Only proposed interviews can be confirmed")

        proposed: list[str] = interview.proposed_times or []
        if confirmed_time not in proposed:
            raise BadRequestException("Selected time is not among the proposed options")

        interview.status = "confirmed"
        interview.confirmed_time = datetime.fromisoformat(confirmed_time)

        # Update application status to "interview"
        app_result = await self.db.execute(
            select(Application).where(Application.id == interview.application_id)
        )
        app = app_result.scalar_one_or_none()
        if app and app.status in ("submitted", "under_review"):
            app.status = "interview"

        await self.db.flush()
        return interview

    # ------------------------------------------------------------------
    # Interviewer actions
    # ------------------------------------------------------------------

    async def complete_interview(self, interview_id: UUID) -> Interview:
        """Mark an interview as completed.

        Raises:
            NotFoundException: If the interview does not exist.
            BadRequestException: If the interview is not in ``confirmed``
                status.
        """
        interview = await self._get_interview(interview_id)

        if interview.status != "confirmed":
            raise BadRequestException("Only confirmed interviews can be marked as completed")

        interview.status = "completed"
        await self.db.flush()
        return interview

    async def score_interview(
        self,
        interview_id: UUID,
        interviewer_id: UUID,
        criterion_scores: dict,
        total_weighted_score: float | Decimal,
        interviewer_notes: str | None = None,
        recommendation: str | None = None,
        rubric_id: UUID | None = None,
    ) -> InterviewScore:
        """Record scores for a completed interview.

        Args:
            interview_id: The interview being scored.
            interviewer_id: The interviewer submitting scores.
            criterion_scores: Mapping of criterion name to numeric score.
            total_weighted_score: Pre-computed or manually entered total.
            interviewer_notes: Optional free-text notes.
            recommendation: Optional recommendation (e.g. ``"admit"``,
                ``"reject"``, ``"waitlist"``).
            rubric_id: Optional rubric used for scoring.

        Returns:
            The created :class:`InterviewScore`.

        Raises:
            NotFoundException: If the interview does not exist.
            BadRequestException: If the interview has not been completed.
        """
        interview = await self._get_interview(interview_id)

        if interview.status != "completed":
            raise BadRequestException("Interview must be completed before scoring")

        score = InterviewScore(
            interview_id=interview_id,
            interviewer_id=interviewer_id,
            rubric_id=rubric_id,
            criterion_scores=criterion_scores,
            total_weighted_score=Decimal(str(total_weighted_score)),
            interviewer_notes=interviewer_notes,
            recommendation=recommendation,
        )
        self.db.add(score)
        await self.db.flush()
        return score

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_interview(self, interview_id: UUID) -> Interview:
        """Load an interview by ID or raise 404."""
        result = await self.db.execute(select(Interview).where(Interview.id == interview_id))
        interview = result.scalar_one_or_none()
        if not interview:
            raise NotFoundException("Interview not found")
        return interview

    async def _get_student_interview(self, student_id: UUID, interview_id: UUID) -> Interview:
        """Load an interview that belongs to one of the student's applications."""
        result = await self.db.execute(
            select(Interview)
            .join(Application, Interview.application_id == Application.id)
            .where(
                Interview.id == interview_id,
                Application.student_id == student_id,
            )
        )
        interview = result.scalar_one_or_none()
        if not interview:
            raise NotFoundException("Interview not found for this student")
        return interview
