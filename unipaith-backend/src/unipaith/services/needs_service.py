"""Phase A — Needs service (Maslow-keyed needs map)."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.needs import StudentNeed
from unipaith.models.student import StudentProfile
from unipaith.schemas.needs import CreateNeedRequest, UpdateNeedRequest


class NeedsService:
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

    async def _get_need(self, need_id: UUID, student_id: UUID) -> StudentNeed:
        result = await self.db.execute(
            select(StudentNeed).where(
                StudentNeed.id == need_id,
                StudentNeed.student_id == student_id,
            )
        )
        need = result.scalar_one_or_none()
        if need is None:
            raise NotFoundException("Need not found")
        return need

    @staticmethod
    def _validate_provenance(source: str, source_session_id: UUID | None) -> None:
        """Discovery requires session_id; manual forbids it. 'inferred'
        accepts either."""
        if source == "discovery" and source_session_id is None:
            raise BadRequestException("source_session_id is required when source='discovery'")
        if source == "manual" and source_session_id is not None:
            raise BadRequestException("source_session_id must be omitted when source='manual'")

    async def list_needs(
        self, user_id: UUID, *, maslow_level: str | None = None
    ) -> list[StudentNeed]:
        student_id = await self._student_id(user_id)
        stmt = select(StudentNeed).where(StudentNeed.student_id == student_id)
        if maslow_level is not None:
            stmt = stmt.where(StudentNeed.maslow_level == maslow_level)
        stmt = stmt.order_by(StudentNeed.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_need(self, user_id: UUID, body: CreateNeedRequest) -> StudentNeed:
        self._validate_provenance(body.source, body.source_session_id)
        student_id = await self._student_id(user_id)
        need = StudentNeed(
            student_id=student_id,
            maslow_level=body.maslow_level,
            need_type=body.need_type,
            signal=body.signal,
            severity=body.severity,
            source=body.source,
            source_session_id=body.source_session_id,
            source_quote=body.source_quote,
            confidence=body.confidence,
        )
        self.db.add(need)
        await self.db.flush()
        await self.db.refresh(need)
        return need

    async def update_need(
        self, user_id: UUID, need_id: UUID, body: UpdateNeedRequest
    ) -> StudentNeed:
        student_id = await self._student_id(user_id)
        need = await self._get_need(need_id, student_id)
        data = body.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(need, key, value)
        await self.db.flush()
        await self.db.refresh(need)
        return need

    async def delete_need(self, user_id: UUID, need_id: UUID) -> None:
        student_id = await self._student_id(user_id)
        need = await self._get_need(need_id, student_id)
        await self.db.delete(need)
        await self.db.flush()
