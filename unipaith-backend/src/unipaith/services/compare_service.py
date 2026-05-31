"""Spec 10 §8 — server-persisted compare set.

The student's global compare tray, capped at 4 programs (spec 10 §8), backed
by `student_compare_lists`. Stateless from the client's view: list / add /
remove. The side-by-side comparison matrix itself still comes from
`SavedListService.compare_programs` — this service only owns the *set*.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import ConflictException, NotFoundException
from unipaith.models.engagement import StudentCompareItem
from unipaith.models.institution import Institution, Program
from unipaith.schemas.search import CompareItem, CompareListResponse

MAX_COMPARE = 4


class CompareService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list(self, student_id: UUID) -> CompareListResponse:
        return CompareListResponse(items=await self._items(student_id), max=MAX_COMPARE)

    async def add(self, student_id: UUID, program_id: UUID) -> CompareListResponse:
        program = await self.db.scalar(
            select(Program).where(Program.id == program_id, Program.is_published.is_(True))
        )
        if program is None:
            raise NotFoundException("Program not found")

        existing = await self.db.scalar(
            select(StudentCompareItem).where(
                StudentCompareItem.student_id == student_id,
                StudentCompareItem.program_id == program_id,
            )
        )
        if existing is None:  # idempotent add
            count = await self.db.scalar(
                select(func.count())
                .select_from(StudentCompareItem)
                .where(StudentCompareItem.student_id == student_id)
            )
            if (count or 0) >= MAX_COMPARE:
                raise ConflictException(
                    f"You can compare up to {MAX_COMPARE} programs. Remove one to add another."
                )
            self.db.add(StudentCompareItem(student_id=student_id, program_id=program_id))
            await self.db.flush()
        return await self.list(student_id)

    async def remove(self, student_id: UUID, program_id: UUID) -> CompareListResponse:
        await self.db.execute(
            delete(StudentCompareItem).where(
                StudentCompareItem.student_id == student_id,
                StudentCompareItem.program_id == program_id,
            )
        )
        await self.db.flush()
        return await self.list(student_id)

    async def _items(self, student_id: UUID) -> list[CompareItem]:
        stmt = (
            select(StudentCompareItem, Program, Institution)
            .join(Program, StudentCompareItem.program_id == Program.id)
            .join(Institution, Program.institution_id == Institution.id)
            .where(StudentCompareItem.student_id == student_id)
            .order_by(StudentCompareItem.created_at.asc())
        )
        rows = (await self.db.execute(stmt)).all()
        return [
            CompareItem(
                program_id=prog.id,
                program_name=prog.program_name,
                institution_name=inst.name,
                degree_type=prog.degree_type,
            )
            for (_item, prog, inst) in rows
        ]
