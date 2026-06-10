"""
Essay workshop service — create, iterate, and get AI feedback on essays.

Phase C1: `request_feedback` calls the A6 Workshop Coach + Haiku-as-judge
post-classifier when `ai_discovery_v2_enabled` is True. Falls back to the
placeholder feedback when the flag is off so existing test contracts and
non-AI environments still work.
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.config import settings
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


        if settings.ai_workshops_v2_enabled:
            feedback = await self._llm_feedback(essay, program, feedback_type)
        else:
            feedback = {
                "overall_score": None,
                "strengths": [],
                "improvements": [
                    "AI essay feedback is currently disabled. Enable "
                    "AI_WORKSHOPS_V2_ENABLED to receive structured coach feedback.",
                ],
                "prompt_alignment_score": None,
                "raw_feedback": None,
                "feedback_type": feedback_type,
            }

        essay.ai_feedback = feedback
        await self.db.flush()
        await self.db.refresh(essay)
        return essay

    async def _llm_feedback(
        self, essay: StudentEssay, program: Program, feedback_type: str
    ) -> dict:
        """Phase C1 — call the A6 Workshop Coach + Haiku judge.

        On any failure (LLM error, malformed feedback, judge fails the
        guardrail), we return a refusal-shaped placeholder rather than
        partial / unsafe content. Safety-incident details are logged via
        `ai_safety_incidents` (added by the client wrapper) and exposed in
        `raw_feedback` for admin review.
        """
        from unipaith.ai.coach import EssayDraft, get_workshop_coach

        institution_name = (
            program.institution.name if program.institution else ""
        )
        draft = EssayDraft(
            draft_text=essay.content or "",
            prompt_text=essay.prompt_text or "",
            program_name=program.program_name or "",
            institution_name=institution_name,
            target_word_count=getattr(essay, "target_word_count", None),
            word_count=essay.word_count,
        )

        try:
            result = await get_workshop_coach().coach_essay(
                draft=draft, db=self.db
            )
        except Exception as exc:  # pragma: no cover — degraded path
            logger.exception("Workshop coach failed for essay=%s: %s", essay.id, exc)
            return {
                "overall_score": None,
                "strengths": [],
                "improvements": [
                    "Coach call failed — please try again. Our team has been notified."
                ],
                "prompt_alignment_score": None,
                "raw_feedback": {"error": str(exc)[:240]},
                "feedback_type": feedback_type,
            }

        if not result.passed:
            # The judge caught something. Don't surface unsafe content;
            # ask the student to reword their request, log the incident.
            logger.warning(
                "Workshop guardrail blocked essay=%s judge_score=%d evidence=%s",
                essay.id,
                result.verdict.score,
                result.verdict.evidence[:120],
            )
            return {
                "overall_score": None,
                "strengths": [],
                "improvements": [
                    "Your request looks like it might be asking me to "
                    "rewrite the essay rather than give feedback. I can "
                    "score and probe — but I won't write the prose for "
                    "you. Send the draft again and I'll give you specific "
                    "feedback."
                ],
                "prompt_alignment_score": None,
                "raw_feedback": {
                    "guardrail_blocked": True,
                    "judge_score": result.verdict.score,
                    "judge_category": result.verdict.category,
                },
                "feedback_type": feedback_type,
            }

        fb = result.feedback
        # Translate the structured Coach output into the legacy
        # ai_feedback shape the existing API/UI expects. Average the
        # rubric to derive an overall_score in [0,100] for the simple
        # display path.
        rubric_avg = sum(fb.rubric_scores.values()) / max(1, len(fb.rubric_scores))
        overall = int(round(rubric_avg * 20))  # 1–5 → 20–100
        prompt_alignment = int(round(fb.rubric_scores.get("prompt_alignment", 3) * 20))
        return {
            "overall_score": overall,
            "strengths": [
                f"{k}: {v}/5"
                for k, v in fb.rubric_scores.items()
                if v >= 4
            ],
            "improvements": [
                f"P{i.get('paragraph_index')}: {i.get('issue', '')}"
                for i in fb.structural_issues
            ]
            + [f"Missing: {m}" for m in fb.missing_elements],
            "prompt_alignment_score": prompt_alignment,
            "questions_for_student": fb.questions_for_student,
            "prompt_alignment_notes": fb.prompt_alignment_notes,
            "rubric_scores": fb.rubric_scores,
            "raw_feedback": {
                "judge_score": result.verdict.score,
                "judge_category": result.verdict.category,
                "schema_version": fb.schema_version,
                "cost_usd": fb.cost_usd + result.verdict.cost_usd,
            },
            "feedback_type": feedback_type,
        }
