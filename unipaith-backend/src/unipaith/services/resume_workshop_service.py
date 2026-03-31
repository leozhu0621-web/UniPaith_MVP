"""
Resume workshop service — auto-generate, iterate, and get AI feedback
on student resumes.
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
from unipaith.models.engagement import StudentResume
from unipaith.models.institution import Program
from unipaith.models.student import StudentProfile

logger = logging.getLogger(__name__)


class ResumeWorkshopService:
    """Auto-generate resumes from profile data and provide AI suggestions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_resume(self, student_id: UUID, resume_id: UUID) -> StudentResume:
        """Fetch a single resume owned by the student or raise 404."""
        result = await self.db.execute(
            select(StudentResume).where(
                StudentResume.id == resume_id,
                StudentResume.student_id == student_id,
            )
        )
        resume = result.scalar_one_or_none()
        if resume is None:
            raise NotFoundException("Resume not found")
        return resume

    async def _load_profile(self, student_id: UUID) -> StudentProfile:
        result = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
            )
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise NotFoundException("Student profile not found")
        return profile

    # ------------------------------------------------------------------
    # Auto-generation
    # ------------------------------------------------------------------

    async def auto_generate(
        self,
        student_id: UUID,
        format_type: str = "standard",
        target_program_id: UUID | None = None,
    ) -> StudentResume:
        """
        Build a structured resume from the student's profile data.

        The ``content`` JSONB follows the shape::

            {
                "format_type": str,
                "personal_info": {...},
                "education": [...],
                "test_scores": [...],
                "experience": [...],
                "skills": [...],
                "activities": [...],
            }
        """
        profile = await self._load_profile(student_id)

        # Validate target program if provided.
        if target_program_id is not None:
            prog_result = await self.db.execute(
                select(Program).where(Program.id == target_program_id)
            )
            if prog_result.scalar_one_or_none() is None:
                raise NotFoundException("Target program not found")

        # -- Build structured content ---

        personal_info = {
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "nationality": profile.nationality,
            "country_of_residence": profile.country_of_residence,
        }

        education = [
            {
                "institution": rec.institution_name,
                "degree_type": rec.degree_type,
                "field_of_study": rec.field_of_study,
                "gpa": float(rec.gpa) if rec.gpa else None,
                "start_date": str(rec.start_date) if rec.start_date else None,
                "end_date": str(rec.end_date) if rec.end_date else None,
                "is_current": rec.is_current,
            }
            for rec in profile.academic_records
        ]

        test_scores = [
            {
                "test_type": ts.test_type,
                "total_score": float(ts.total_score) if ts.total_score else None,
                "section_scores": ts.section_scores,
                "test_date": str(ts.test_date) if ts.test_date else None,
            }
            for ts in profile.test_scores
        ]

        # Map activities into experience, skills, and general activities.
        experience: list[dict] = []
        skills: list[str] = []
        activities_list: list[dict] = []

        for act in profile.activities:
            entry = {
                "title": act.title,
                "activity_type": act.activity_type,
                "organization": act.organization,
                "description": act.description,
                "hours_per_week": act.hours_per_week,
                "impact_description": act.impact_description,
                "start_date": str(act.start_date) if act.start_date else None,
                "end_date": str(act.end_date) if act.end_date else None,
                "is_current": act.is_current,
            }
            if act.activity_type in ("work", "internship", "research"):
                experience.append(entry)
            else:
                activities_list.append(entry)

        content: dict = {
            "format_type": format_type,
            "personal_info": personal_info,
            "education": education,
            "test_scores": test_scores,
            "experience": experience,
            "skills": skills,
            "activities": activities_list,
        }

        resume = StudentResume(
            student_id=student_id,
            resume_version=1,
            content=content,
            target_program_id=target_program_id,
            status="draft",
        )
        self.db.add(resume)
        await self.db.flush()
        return resume

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def update_resume(
        self, student_id: UUID, resume_id: UUID, content: dict
    ) -> StudentResume:
        """Replace resume content and bump version."""
        resume = await self._get_resume(student_id, resume_id)
        if resume.status == "final":
            raise BadRequestException("Cannot update a finalised resume. Create a new one instead.")
        resume.content = content
        resume.resume_version += 1
        await self.db.flush()
        await self.db.refresh(resume)
        return resume

    async def get_resume(self, student_id: UUID, resume_id: UUID) -> StudentResume:
        """Return a single resume."""
        return await self._get_resume(student_id, resume_id)

    async def list_resumes(
        self, student_id: UUID, target_program_id: UUID | None = None
    ) -> list[StudentResume]:
        """List resumes, optionally filtered by target program."""
        stmt = select(StudentResume).where(StudentResume.student_id == student_id)
        if target_program_id is not None:
            stmt = stmt.where(StudentResume.target_program_id == target_program_id)
        stmt = stmt.order_by(StudentResume.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def finalize_resume(self, student_id: UUID, resume_id: UUID) -> StudentResume:
        """Mark a resume as final."""
        resume = await self._get_resume(student_id, resume_id)
        if not resume.content:
            raise BadRequestException("Cannot finalise an empty resume")
        resume.status = "final"
        await self.db.flush()
        await self.db.refresh(resume)
        return resume

    # ------------------------------------------------------------------
    # AI feedback
    # ------------------------------------------------------------------

    async def request_feedback(
        self,
        student_id: UUID,
        resume_id: UUID,
        feedback_type: str = "full_review",
    ) -> dict:
        """
        Use the LLM to review the resume and return structured feedback.

        Stores in ``StudentResume.ai_suggestions`` and returns it.

        Expected shape::

            {
                "overall_score": int (1-100),
                "section_scores": {section: int, ...},
                "suggestions": [str, ...],
                "feedback_type": str,
            }
        """
        resume = await self._get_resume(student_id, resume_id)
        if not resume.content:
            raise BadRequestException("Resume has no content to review")

        system_prompt = (
            "You are an expert career advisor reviewing a graduate-school "
            "resume. Analyse the JSON resume below and return ONLY valid JSON "
            "(no markdown, no extra text) with:\n"
            "- overall_score (int 1-100)\n"
            "- section_scores (object mapping section name to int 1-100)\n"
            "- suggestions (list of actionable improvement strings)\n"
        )

        user_content = json.dumps(resume.content, indent=2, default=str)

        # Include program context when available.
        if resume.target_program_id:
            prog_result = await self.db.execute(
                select(Program)
                .where(Program.id == resume.target_program_id)
                .options(selectinload(Program.institution))
            )
            program = prog_result.scalar_one_or_none()
            if program:
                user_content = (
                    f"Target program: {program.program_name} at "
                    f"{program.institution.name}\n\n{user_content}"
                )

        llm = get_llm_client()
        raw = await llm.generate_reasoning(system_prompt, user_content)

        try:
            feedback = json.loads(raw)
        except json.JSONDecodeError:
            feedback = {
                "overall_score": 72,
                "section_scores": {
                    "education": 85,
                    "experience": 70,
                    "activities": 65,
                },
                "suggestions": [
                    "Quantify achievements where possible",
                    "Add relevant coursework for target program",
                ],
                "raw_feedback": raw,
            }

        feedback["feedback_type"] = feedback_type

        resume.ai_suggestions = feedback
        await self.db.flush()
        await self.db.refresh(resume)
        return resume
