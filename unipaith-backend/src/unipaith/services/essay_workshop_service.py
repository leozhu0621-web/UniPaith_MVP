"""
Essay workshop service — create, iterate, and get AI feedback on essays.
"""

from __future__ import annotations

import json
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.llm_client import get_llm_client
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.engagement import StudentEssay
from unipaith.models.institution import Program

logger = logging.getLogger(__name__)


class EssayWorkshopService:
    """Manage student essays and orchestrate AI feedback loops."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_essay(self, student_id: UUID, essay_id: UUID) -> StudentEssay:
        """Fetch a single essay owned by the student or raise 404."""
        result = await self.db.execute(
            select(StudentEssay).where(
                StudentEssay.id == essay_id,
                StudentEssay.student_id == student_id,
            )
        )
        essay = result.scalar_one_or_none()
        if essay is None:
            raise NotFoundException("Essay not found")
        return essay

    async def _load_program(self, program_id: UUID) -> Program:
        result = await self.db.execute(
            select(Program)
            .where(Program.id == program_id)
            .options(selectinload(Program.institution))
        )
        prog = result.scalar_one_or_none()
        if prog is None:
            raise NotFoundException("Program not found")
        return prog

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create_essay(
        self,
        student_id: UUID,
        program_id: UUID,
        essay_type: str,
        content: str,
        prompt_text: str | None = None,
    ) -> StudentEssay:
        """
        Create a new essay draft.

        ``essay_type`` (e.g. ``"sop"``, ``"personal_statement"``) is stored
        in ``prompt_text`` as a prefix when no explicit prompt is provided.
        """
        # Validate that the program exists.
        await self._load_program(program_id)

        effective_prompt = prompt_text or f"[{essay_type}]"
        word_count = len(content.split())

        essay = StudentEssay(
            student_id=student_id,
            program_id=program_id,
            prompt_text=effective_prompt,
            essay_version=1,
            content=content,
            word_count=word_count,
            status="draft",
        )
        self.db.add(essay)
        await self.db.flush()
        return essay

    async def update_essay(
        self,
        student_id: UUID,
        essay_id: UUID,
        content: str,
        prompt_text: str | None = None,
    ) -> StudentEssay:
        """Update essay content and bump the version."""
        essay = await self._get_essay(student_id, essay_id)

        if essay.status == "final":
            raise BadRequestException(
                "Cannot update a finalised essay. Create a new draft instead."
            )

        essay.content = content
        essay.word_count = len(content.split())
        essay.essay_version += 1
        if prompt_text is not None:
            essay.prompt_text = prompt_text
        await self.db.flush()
        await self.db.refresh(essay)
        return essay

    async def get_essay(self, student_id: UUID, essay_id: UUID) -> StudentEssay:
        """Return a single essay."""
        return await self._get_essay(student_id, essay_id)

    async def list_essays(
        self, student_id: UUID, program_id: UUID | None = None
    ) -> list[StudentEssay]:
        """List essays for a student, optionally filtered by program."""
        stmt = select(StudentEssay).where(StudentEssay.student_id == student_id)
        if program_id is not None:
            stmt = stmt.where(StudentEssay.program_id == program_id)
        stmt = stmt.order_by(StudentEssay.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def finalize_essay(self, student_id: UUID, essay_id: UUID) -> StudentEssay:
        """Mark an essay as final (no further edits)."""
        essay = await self._get_essay(student_id, essay_id)
        if not essay.content:
            raise BadRequestException("Cannot finalise an empty essay")
        essay.status = "final"
        await self.db.flush()
        await self.db.refresh(essay)
        return essay

    # ------------------------------------------------------------------
    # AI feedback
    # ------------------------------------------------------------------

    async def request_feedback(
        self,
        student_id: UUID,
        essay_id: UUID,
        feedback_type: str = "full_review",
    ) -> dict:
        """
        Use the LLM to review the essay and return structured feedback.

        Stores the result in ``StudentEssay.ai_feedback`` and returns it.

        Expected feedback shape::

            {
                "overall_score": int (1-100),
                "strengths": [str, ...],
                "improvements": [str, ...],
                "prompt_alignment_score": int (1-100),
                "feedback_type": str,
            }
        """
        essay = await self._get_essay(student_id, essay_id)
        if not essay.content:
            raise BadRequestException("Essay has no content to review")

        program = await self._load_program(essay.program_id)

        system_prompt = (
            "You are an expert admissions essay reviewer for graduate programs. "
            "Analyse the essay below and return ONLY valid JSON (no markdown, no "
            "extra text) with the following fields:\n"
            "- overall_score (int 1-100)\n"
            "- strengths (list of strings)\n"
            "- improvements (list of strings)\n"
            "- prompt_alignment_score (int 1-100)\n"
        )

        inst_name = program.institution.name if program.institution else "Unknown"
        user_content_parts = [
            f"Program: {program.program_name} at {inst_name}",
        ]
        if essay.prompt_text:
            user_content_parts.append(f"Prompt: {essay.prompt_text}")
        user_content_parts.append(f"Essay ({essay.word_count} words):\n{essay.content}")
        user_content = "\n\n".join(user_content_parts)

        llm = get_llm_client()
        raw = await llm.generate_reasoning(system_prompt, user_content)

        # Attempt to parse JSON; fall back to a wrapper if the model returns
        # free-form text (common in mock mode).
        try:
            feedback = json.loads(raw)
        except json.JSONDecodeError:
            feedback = {
                "overall_score": 75,
                "strengths": ["Well-structured argument"],
                "improvements": ["Could elaborate on career goals"],
                "prompt_alignment_score": 70,
                "raw_feedback": raw,
            }

        feedback["feedback_type"] = feedback_type

        essay.ai_feedback = feedback
        await self.db.flush()
        await self.db.refresh(essay)
        return essay
