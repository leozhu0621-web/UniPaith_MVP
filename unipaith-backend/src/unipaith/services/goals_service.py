"""Phase A — Goals service (SMART goal stack)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.goals import StudentGoal
from unipaith.models.student import StudentProfile
from unipaith.schemas.goals import CreateGoalRequest, UpdateGoalRequest


class GoalsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _student_id(self, user_id: UUID) -> UUID:
        result = await self.db.execute(
            select(StudentProfile.id).where(StudentProfile.user_id == user_id)
        )
        sid = result.scalar_one_or_none()
        if sid is None:
            raise NotFoundException("Student profile not found")
        return sid

    async def _get_goal(self, goal_id: UUID, student_id: UUID) -> StudentGoal:
        result = await self.db.execute(
            select(StudentGoal).where(
                StudentGoal.id == goal_id,
                StudentGoal.student_id == student_id,
            )
        )
        goal = result.scalar_one_or_none()
        if goal is None:
            raise NotFoundException("Goal not found")
        return goal

    @staticmethod
    def _validate_provenance(source: str, source_session_id: UUID | None) -> None:
        """Discovery-sourced rows MUST carry source_session_id; manual rows
        MUST NOT. The same rule is enforced at the DB level — we surface a 400
        instead of letting the IntegrityError bubble up."""
        if source == "discovery" and source_session_id is None:
            raise BadRequestException("source_session_id is required when source='discovery'")
        if source == "manual" and source_session_id is not None:
            raise BadRequestException("source_session_id must be omitted when source='manual'")

    async def list_goals(self, user_id: UUID, *, status: str | None = None) -> list[StudentGoal]:
        student_id = await self._student_id(user_id)
        stmt = select(StudentGoal).where(StudentGoal.student_id == student_id)
        if status is not None:
            stmt = stmt.where(StudentGoal.status == status)
        stmt = stmt.order_by(StudentGoal.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_goal(self, user_id: UUID, body: CreateGoalRequest) -> StudentGoal:
        self._validate_provenance(body.source, body.source_session_id)
        student_id = await self._student_id(user_id)
        goal = StudentGoal(
            student_id=student_id,
            category=body.category,
            specific=body.specific,
            measurable=body.measurable,
            achievable_notes=body.achievable_notes,
            relevant_notes=body.relevant_notes,
            time_bound=body.time_bound,
            status=body.status,
            source=body.source,
            source_session_id=body.source_session_id,
            confidence=body.confidence,
        )
        self.db.add(goal)
        await self.db.flush()
        await self.db.refresh(goal)
        return goal

    async def update_goal(
        self, user_id: UUID, goal_id: UUID, body: UpdateGoalRequest
    ) -> StudentGoal:
        student_id = await self._student_id(user_id)
        goal = await self._get_goal(goal_id, student_id)

        # Partial update — only fields explicitly set on the request body.
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(goal, key, value)
        await self.db.flush()
        await self.db.refresh(goal)
        return goal

    async def delete_goal(self, user_id: UUID, goal_id: UUID) -> None:
        student_id = await self._student_id(user_id)
        goal = await self._get_goal(goal_id, student_id)
        await self.db.delete(goal)
        await self.db.flush()
