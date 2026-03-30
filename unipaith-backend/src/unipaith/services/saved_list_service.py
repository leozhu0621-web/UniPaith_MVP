"""
Saved-list service — manage a student's saved/bookmarked programs and
provide AI-powered program comparison.
"""
from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.llm_client import get_llm_client
from unipaith.core.exceptions import BadRequestException, ConflictException, NotFoundException
from unipaith.models.engagement import SavedList, SavedListItem
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult

logger = logging.getLogger(__name__)


class SavedListService:
    """CRUD for saved-program lists plus AI comparison."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_or_create_default_list(self, student_id: UUID) -> SavedList:
        """Return the student's default saved list, creating one if needed."""
        result = await self.db.execute(
            select(SavedList)
            .where(SavedList.student_id == student_id)
            .options(selectinload(SavedList.items))
        )
        saved_list = result.scalar_one_or_none()
        if saved_list is None:
            saved_list = SavedList(student_id=student_id, list_name="My List")
            self.db.add(saved_list)
            await self.db.flush()
        return saved_list

    async def _get_item(
        self, saved_list: SavedList, program_id: UUID
    ) -> SavedListItem:
        """Fetch a single item from the list or raise 404."""
        result = await self.db.execute(
            select(SavedListItem).where(
                SavedListItem.list_id == saved_list.id,
                SavedListItem.program_id == program_id,
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise NotFoundException("Program is not in the saved list")
        return item

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_saved(self, student_id: UUID) -> list[SavedListItem]:
        """Return all saved programs with eagerly-loaded program + institution."""
        saved_list = await self._get_or_create_default_list(student_id)
        result = await self.db.execute(
            select(SavedListItem)
            .where(SavedListItem.list_id == saved_list.id)
            .join(Program, SavedListItem.program_id == Program.id)
            .options(
                selectinload(SavedListItem.saved_list),
            )
            .order_by(SavedListItem.added_at.desc())
        )
        return list(result.scalars().all())

    async def save_program(
        self,
        student_id: UUID,
        program_id: UUID,
        notes: str | None = None,
    ) -> SavedListItem:
        """Add a program to the student's saved list."""
        # Ensure the program exists.
        prog = await self.db.execute(
            select(Program).where(Program.id == program_id)
        )
        if prog.scalar_one_or_none() is None:
            raise NotFoundException("Program not found")

        saved_list = await self._get_or_create_default_list(student_id)

        # Check for duplicates.
        existing = await self.db.execute(
            select(SavedListItem).where(
                SavedListItem.list_id == saved_list.id,
                SavedListItem.program_id == program_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictException("Program is already saved")

        item = SavedListItem(
            list_id=saved_list.id,
            program_id=program_id,
            notes=notes,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def unsave_program(self, student_id: UUID, program_id: UUID) -> None:
        """Remove a program from the saved list."""
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        await self.db.delete(item)
        await self.db.flush()

    async def update_notes(
        self, student_id: UUID, program_id: UUID, notes: str
    ) -> SavedListItem:
        """Update the notes attached to a saved program."""
        saved_list = await self._get_or_create_default_list(student_id)
        item = await self._get_item(saved_list, program_id)
        item.notes = notes
        await self.db.flush()
        return item

    async def compare_programs(
        self, student_id: UUID, program_ids: list[UUID]
    ) -> dict:
        """
        Build a comparison matrix for 2-5 saved programs and generate an
        AI narrative analysis.

        Returns ``{"comparison_data": [...], "ai_analysis": str}``.
        """
        if len(program_ids) < 2 or len(program_ids) > 5:
            raise BadRequestException("Provide between 2 and 5 programs for comparison")

        # Load programs with their institutions.
        result = await self.db.execute(
            select(Program)
            .where(Program.id.in_(program_ids))
            .options(selectinload(Program.institution))
        )
        programs = list(result.scalars().all())
        if len(programs) != len(program_ids):
            raise NotFoundException("One or more programs not found")

        # Load match results for the student + each program.
        match_result = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id == student_id,
                MatchResult.program_id.in_(program_ids),
            )
        )
        match_map: dict[UUID, MatchResult] = {
            m.program_id: m for m in match_result.scalars().all()
        }

        # Build structured comparison data.
        comparison_data: list[dict] = []
        for prog in programs:
            inst: Institution = prog.institution
            match = match_map.get(prog.id)
            comparison_data.append({
                "program_id": str(prog.id),
                "program_name": prog.program_name,
                "institution_name": inst.name if inst else None,
                "country": inst.country if inst else None,
                "degree_type": prog.degree_type,
                "duration_months": prog.duration_months,
                "tuition": prog.tuition,
                "acceptance_rate": float(prog.acceptance_rate) if prog.acceptance_rate else None,
                "application_deadline": str(prog.application_deadline) if prog.application_deadline else None,
                "requirements": prog.requirements,
                "match_score": float(match.match_score) if match and match.match_score else None,
                "match_tier": match.match_tier if match else None,
                "match_reasoning": match.reasoning_text if match else None,
            })

        # Generate AI analysis.
        llm = get_llm_client()
        system_prompt = (
            "You are an expert graduate-school advisor. The user is comparing "
            "multiple programs. Provide a concise narrative analysis covering: "
            "key differences, which program best fits the student, trade-offs in "
            "cost, location, and career outcomes. Be specific and reference the "
            "data provided."
        )
        user_content = json.dumps(comparison_data, indent=2, default=str)
        ai_analysis = await llm.generate_reasoning(system_prompt, user_content)

        return {
            "comparison_data": comparison_data,
            "ai_analysis": ai_analysis,
        }
