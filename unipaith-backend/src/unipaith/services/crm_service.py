"""
CRM touchpoint service — automatic logging of every meaningful interaction.
Touchpoints are logged by event hooks, never manually by users.
Provides timeline views for institutions to see student engagement history.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.workflow import Touchpoint


class CRMService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_touchpoint(
        self,
        student_id: UUID,
        touchpoint_type: str,
        institution_id: UUID | None = None,
        program_id: UUID | None = None,
        application_id: UUID | None = None,
        description: str | None = None,
        metadata: dict | None = None,
    ) -> Touchpoint:
        """
        Log a CRM touchpoint for a student-institution interaction.

        Touchpoint types include:
        - program_saved, program_unsaved, program_compared
        - application_started, application_submitted
        - checklist_completed, essay_submitted, resume_submitted
        - message_sent, message_received
        - event_rsvp, event_attended
        - interview_scheduled, interview_completed
        - decision_made, offer_sent, offer_accepted, offer_declined
        - campaign_opened, campaign_clicked
        """
        touchpoint = Touchpoint(
            student_id=student_id,
            institution_id=institution_id,
            program_id=program_id,
            application_id=application_id,
            touchpoint_type=touchpoint_type,
            description=description,
            metadata_=metadata,
        )
        self.db.add(touchpoint)
        await self.db.flush()
        return touchpoint

    async def get_student_timeline(
        self,
        student_id: UUID,
        institution_id: UUID | None = None,
        limit: int = 100,
    ) -> list[Touchpoint]:
        """
        Get timeline of all touchpoints for a student,
        optionally filtered to a specific institution.
        Returns newest first.
        """
        query = select(Touchpoint).where(Touchpoint.student_id == student_id)
        if institution_id:
            query = query.where(Touchpoint.institution_id == institution_id)
        query = query.order_by(Touchpoint.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_institution_touchpoints(
        self,
        institution_id: UUID,
        touchpoint_type: str | None = None,
        program_id: UUID | None = None,
        limit: int = 200,
    ) -> list[Touchpoint]:
        """
        Get touchpoints for an institution, with optional filters.
        Used by institution dashboards for engagement analytics.
        """
        query = select(Touchpoint).where(
            Touchpoint.institution_id == institution_id
        )
        if touchpoint_type:
            query = query.where(Touchpoint.touchpoint_type == touchpoint_type)
        if program_id:
            query = query.where(Touchpoint.program_id == program_id)
        query = query.order_by(Touchpoint.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_type(
        self,
        institution_id: UUID,
        program_id: UUID | None = None,
    ) -> dict[str, int]:
        """Count touchpoints grouped by type for analytics."""
        from sqlalchemy import func

        query = (
            select(Touchpoint.touchpoint_type, func.count())
            .where(Touchpoint.institution_id == institution_id)
            .group_by(Touchpoint.touchpoint_type)
        )
        if program_id:
            query = query.where(Touchpoint.program_id == program_id)
        result = await self.db.execute(query)
        return {row[0]: row[1] for row in result.all()}
