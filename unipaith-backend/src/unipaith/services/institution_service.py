from __future__ import annotations

import math
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program, TargetSegment
from unipaith.schemas.institution import (
    CreateInstitutionRequest,
    CreateProgramRequest,
    CreateSegmentRequest,
    PaginatedResponse,
    ProgramSummaryResponse,
    UpdateInstitutionRequest,
    UpdateProgramRequest,
    UpdateSegmentRequest,
)


class InstitutionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Institution Profile ---

    async def get_institution(self, user_id: UUID) -> Institution:
        return await self._get_institution_for_user(user_id)

    async def create_institution(
        self, user_id: UUID, data: CreateInstitutionRequest
    ) -> Institution:
        existing = await self.db.execute(
            select(Institution).where(Institution.admin_user_id == user_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Institution already exists for this user")

        institution = Institution(admin_user_id=user_id, **data.model_dump())
        self.db.add(institution)
        await self.db.flush()
        return institution

    async def update_institution(
        self, user_id: UUID, data: UpdateInstitutionRequest
    ) -> Institution:
        institution = await self._get_institution_for_user(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(institution, key, value)
        await self.db.flush()
        return institution

    # --- Programs ---

    async def list_programs(self, institution_id: UUID) -> list[Program]:
        result = await self.db.execute(
            select(Program).where(Program.institution_id == institution_id)
        )
        return list(result.scalars().all())

    async def get_program(
        self, institution_id: UUID, program_id: UUID
    ) -> Program:
        return await self._verify_program_ownership(institution_id, program_id)

    async def create_program(
        self, institution_id: UUID, data: CreateProgramRequest
    ) -> Program:
        program = Program(
            institution_id=institution_id,
            is_published=False,
            **data.model_dump(),
        )
        self.db.add(program)
        await self.db.flush()
        return program

    async def update_program(
        self, institution_id: UUID, program_id: UUID, data: UpdateProgramRequest
    ) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(program, key, value)
        await self.db.flush()
        return program

    async def publish_program(
        self, institution_id: UUID, program_id: UUID
    ) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        errors = []
        if not program.program_name:
            errors.append("program_name is required")
        if not program.degree_type:
            errors.append("degree_type is required")
        if not program.description_text:
            errors.append("description_text is required")
        if not program.tuition and not program.application_deadline:
            errors.append("At least one of tuition or application_deadline is required")
        if errors:
            raise BadRequestException(f"Cannot publish: {'; '.join(errors)}")
        program.is_published = True
        await self.db.flush()
        return program

    async def unpublish_program(
        self, institution_id: UUID, program_id: UUID
    ) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        program.is_published = False
        await self.db.flush()
        return program

    async def delete_program(
        self, institution_id: UUID, program_id: UUID
    ) -> None:
        program = await self._verify_program_ownership(institution_id, program_id)
        app_count = await self.db.execute(
            select(func.count()).select_from(Application).where(
                Application.program_id == program_id
            )
        )
        if app_count.scalar_one() > 0:
            raise ConflictException(
                "Cannot delete program with existing applications"
            )
        await self.db.delete(program)
        await self.db.flush()

    # --- Target Segments ---

    async def list_segments(self, institution_id: UUID) -> list[TargetSegment]:
        result = await self.db.execute(
            select(TargetSegment).where(
                TargetSegment.institution_id == institution_id
            )
        )
        return list(result.scalars().all())

    async def create_segment(
        self, institution_id: UUID, data: CreateSegmentRequest
    ) -> TargetSegment:
        segment = TargetSegment(institution_id=institution_id, **data.model_dump())
        self.db.add(segment)
        await self.db.flush()
        return segment

    async def update_segment(
        self, institution_id: UUID, segment_id: UUID, data: UpdateSegmentRequest
    ) -> TargetSegment:
        result = await self.db.execute(
            select(TargetSegment).where(
                TargetSegment.id == segment_id,
                TargetSegment.institution_id == institution_id,
            )
        )
        segment = result.scalar_one_or_none()
        if not segment:
            raise NotFoundException("Segment not found")
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(segment, key, value)
        await self.db.flush()
        return segment

    async def delete_segment(
        self, institution_id: UUID, segment_id: UUID
    ) -> None:
        result = await self.db.execute(
            select(TargetSegment).where(
                TargetSegment.id == segment_id,
                TargetSegment.institution_id == institution_id,
            )
        )
        segment = result.scalar_one_or_none()
        if not segment:
            raise NotFoundException("Segment not found")
        await self.db.delete(segment)
        await self.db.flush()

    # --- Public Program Browsing ---

    async def search_programs(
        self,
        query: str | None = None,
        country: str | None = None,
        degree_type: str | None = None,
        min_tuition: int | None = None,
        max_tuition: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ProgramSummaryResponse]:
        stmt = (
            select(Program, Institution)
            .join(Institution, Program.institution_id == Institution.id)
            .where(Program.is_published.is_(True))
        )

        if query:
            # TODO: upgrade to PostgreSQL full-text search (to_tsvector/to_tsquery)
            like_q = f"%{query}%"
            stmt = stmt.where(
                Program.program_name.ilike(like_q)
                | Program.description_text.ilike(like_q)
                | Program.department.ilike(like_q)
            )
        if country:
            stmt = stmt.where(Institution.country.ilike(f"%{country}%"))
        if degree_type:
            stmt = stmt.where(Program.degree_type == degree_type)
        if min_tuition is not None:
            stmt = stmt.where(Program.tuition >= min_tuition)
        if max_tuition is not None:
            stmt = stmt.where(Program.tuition <= max_tuition)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        offset = (page - 1) * page_size
        results = await self.db.execute(
            stmt.offset(offset).limit(page_size)
        )
        rows = results.all()

        items = [
            ProgramSummaryResponse(
                id=prog.id,
                program_name=prog.program_name,
                degree_type=prog.degree_type,
                department=prog.department,
                tuition=prog.tuition,
                application_deadline=prog.application_deadline,
                institution_name=inst.name,
                institution_country=inst.country,
            )
            for prog, inst in rows
        ]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(1, math.ceil(total / page_size)),
        )

    async def get_public_program(self, program_id: UUID) -> Program:
        result = await self.db.execute(
            select(Program).where(
                Program.id == program_id, Program.is_published.is_(True)
            )
        )
        program = result.scalar_one_or_none()
        if not program:
            raise NotFoundException("Program not found")
        return program

    # --- Helpers ---

    async def _get_institution_for_user(self, user_id: UUID) -> Institution:
        result = await self.db.execute(
            select(Institution).where(Institution.admin_user_id == user_id)
        )
        institution = result.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution not found")
        return institution

    async def _verify_program_ownership(
        self, institution_id: UUID, program_id: UUID
    ) -> Program:
        result = await self.db.execute(
            select(Program).where(
                Program.id == program_id,
                Program.institution_id == institution_id,
            )
        )
        program = result.scalar_one_or_none()
        if not program:
            raise NotFoundException("Program not found")
        return program

    async def get_program_count(self, institution_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Program).where(
                Program.institution_id == institution_id,
                Program.is_published.is_(True),
            )
        )
        return result.scalar_one()
