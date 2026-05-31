"""
Checklist service — auto-generate and manage application checklists.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.core.exceptions import NotFoundException
from unipaith.models.application import Application, ApplicationChecklist
from unipaith.models.institution import Program
from unipaith.models.student import StudentProfile

logger = logging.getLogger(__name__)


class ChecklistService:
    """Generate and query per-application readiness checklists."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _load_application(self, student_id: UUID, application_id: UUID) -> Application:
        """Fetch an application owned by the student or raise 404."""
        result = await self.db.execute(
            select(Application).where(
                Application.id == application_id,
                Application.student_id == student_id,
            )
        )
        app = result.scalar_one_or_none()
        if app is None:
            raise NotFoundException("Application not found")
        return app

    async def _load_program(self, program_id: UUID) -> Program:
        result = await self.db.execute(select(Program).where(Program.id == program_id))
        prog = result.scalar_one_or_none()
        if prog is None:
            raise NotFoundException("Program not found")
        return prog

    async def _load_student_profile(self, student_id: UUID) -> StudentProfile:
        result = await self.db.execute(
            select(StudentProfile)
            .where(StudentProfile.id == student_id)
            .options(
                selectinload(StudentProfile.academic_records),
                selectinload(StudentProfile.test_scores),
                selectinload(StudentProfile.activities),
                selectinload(StudentProfile.documents),
            )
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            raise NotFoundException("Student profile not found")
        return profile

    # ------------------------------------------------------------------
    # Item builders
    # ------------------------------------------------------------------

    def _build_items(self, program: Program, profile: StudentProfile) -> list[dict]:
        """
        Derive checklist items from program requirements and student data.

        Each item: ``{name, category, required, completed, description}``
        """
        reqs: dict = program.requirements or {}
        items: list[dict] = []

        # 1. Personal information
        has_personal = bool(
            profile.first_name
            and profile.last_name
            and profile.nationality
            and profile.country_of_residence
        )
        items.append(
            {
                "name": "Personal Information",
                "category": "personal_info",
                "required": True,
                "completed": has_personal,
                "description": "Full name, nationality, and country of residence.",
            }
        )

        # 2. Academic records
        has_academics = len(profile.academic_records) > 0
        items.append(
            {
                "name": "Academic Records",
                "category": "academic_records",
                "required": True,
                "completed": has_academics,
                "description": "At least one academic record with GPA.",
            }
        )

        # 3. Test scores — conditionally required
        gre_required = reqs.get("gre_required", False)
        toefl_min = reqs.get("toefl_min")
        ielts_min = reqs.get("ielts_min")

        has_gre = any(s.test_type == "gre" for s in profile.test_scores)
        has_english = any(s.test_type in ("toefl", "ielts") for s in profile.test_scores)

        if gre_required:
            items.append(
                {
                    "name": "GRE Score",
                    "category": "test_scores",
                    "required": True,
                    "completed": has_gre,
                    "description": "GRE scores are required for this program.",
                }
            )

        if toefl_min or ielts_min:
            desc_parts: list[str] = []
            if toefl_min:
                desc_parts.append(f"TOEFL minimum: {toefl_min}")
            if ielts_min:
                desc_parts.append(f"IELTS minimum: {ielts_min}")
            items.append(
                {
                    "name": "English Proficiency",
                    "category": "test_scores",
                    "required": True,
                    "completed": has_english,
                    "description": ". ".join(desc_parts) + ".",
                }
            )

        # 4. Essays
        essay_prompts: list[dict] = reqs.get("essays", [])
        if essay_prompts:
            items.append(
                {
                    "name": "Essays",
                    "category": "essays",
                    "required": True,
                    "completed": False,  # Will be refined per-essay later if needed.
                    "description": f"{len(essay_prompts)} essay(s) required.",
                }
            )
        else:
            items.append(
                {
                    "name": "Statement of Purpose",
                    "category": "essays",
                    "required": True,
                    "completed": False,
                    "description": "A statement of purpose or personal statement.",
                }
            )

        # 5. Resume / CV
        items.append(
            {
                "name": "Resume / CV",
                "category": "resume",
                "required": True,
                "completed": False,  # Checked separately by the resume workshop.
                "description": "An up-to-date academic resume or CV.",
            }
        )

        # 6. Recommendation letters
        rec_count = reqs.get("recommendation_letters", 2)
        items.append(
            {
                "name": "Recommendation Letters",
                "category": "recommendation_letters",
                "required": True,
                "completed": False,
                "description": f"{rec_count} recommendation letter(s) required.",
            }
        )

        # 7. Supporting documents
        required_docs: list[str] = reqs.get("required_documents", [])
        has_doc_types = {d.document_type for d in profile.documents}
        for doc_name in required_docs:
            items.append(
                {
                    "name": doc_name,
                    "category": "documents",
                    "required": True,
                    "completed": doc_name.lower().replace(" ", "_") in has_doc_types,
                    "description": f"Upload: {doc_name}.",
                }
            )

        return items

    @staticmethod
    def _compute_completion(items: list[dict]) -> int:
        """Return completion percentage (0-100)."""
        required_items = [i for i in items if i["required"]]
        if not required_items:
            return 100
        completed = sum(1 for i in required_items if i["completed"])
        return int((completed / len(required_items)) * 100)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_checklist(
        self, student_id: UUID, application_id: UUID
    ) -> ApplicationChecklist:
        """
        Auto-generate a checklist for an application based on program
        requirements and what the student has already completed.
        Upserts the ``ApplicationChecklist`` row.
        """
        app = await self._load_application(student_id, application_id)
        program = await self._load_program(app.program_id)
        profile = await self._load_student_profile(student_id)

        items = self._build_items(program, profile)
        completion = self._compute_completion(items)

        # Upsert
        result = await self.db.execute(
            select(ApplicationChecklist).where(
                ApplicationChecklist.student_id == student_id,
                ApplicationChecklist.program_id == app.program_id,
            )
        )
        checklist = result.scalar_one_or_none()
        if checklist is None:
            checklist = ApplicationChecklist(
                student_id=student_id,
                program_id=app.program_id,
                items=items,
                completion_percentage=completion,
                auto_generated_at=datetime.now(UTC),
            )
            self.db.add(checklist)
        else:
            checklist.items = items
            checklist.completion_percentage = completion
            checklist.auto_generated_at = datetime.now(UTC)

        await self.db.flush()
        return checklist

    async def get_checklist(self, student_id: UUID, application_id: UUID) -> ApplicationChecklist:
        """Return an existing checklist for the application."""
        app = await self._load_application(student_id, application_id)
        result = await self.db.execute(
            select(ApplicationChecklist).where(
                ApplicationChecklist.student_id == student_id,
                ApplicationChecklist.program_id == app.program_id,
            )
        )
        checklist = result.scalar_one_or_none()
        if checklist is None:
            raise NotFoundException("Checklist not found — generate one first")
        return checklist

    async def readiness_check(self, student_id: UUID, application_id: UUID) -> dict:
        """
        Evaluate readiness for submission.

        Returns::

            {
                "is_ready": bool,
                "completion_percentage": int,
                "missing_items": [str, ...],
                "warnings": [str, ...],
            }
        """
        app = await self._load_application(student_id, application_id)
        program = await self._load_program(app.program_id)
        profile = await self._load_student_profile(student_id)

        items = self._build_items(program, profile)
        completion = self._compute_completion(items)

        missing = [i["name"] for i in items if i["required"] and not i["completed"]]

        warnings: list[str] = []
        # Deadline proximity warning.
        if program.application_deadline:
            days_left = (program.application_deadline - date.today()).days
            if days_left < 0:
                warnings.append("The application deadline has passed.")
            elif days_left <= 7:
                warnings.append(f"Deadline is in {days_left} day(s) — submit soon!")
            elif days_left <= 30:
                warnings.append(f"Deadline is in {days_left} days — start finalising.")

        is_ready = len(missing) == 0
        stored = await self._load_stored_items(student_id, app.program_id)
        if app.submission_mode == "external" and stored:
            missing = [
                (i.get("item_name") or i.get("name") or "Item")
                for i in stored
                if i.get("required", True) and not i.get("student_marked_complete")
            ]
            is_ready = len(missing) == 0

        return {
            "is_ready": is_ready,
            "ready": is_ready,
            "completion_percentage": completion,
            "missing_items": missing,
            "warnings": warnings,
        }

    async def _load_stored_items(self, student_id: UUID, program_id: UUID) -> list[dict] | None:
        result = await self.db.execute(
            select(ApplicationChecklist).where(
                ApplicationChecklist.student_id == student_id,
                ApplicationChecklist.program_id == program_id,
            )
        )
        row = result.scalar_one_or_none()
        return list(row.items) if row and row.items else None

    async def _get_or_build_items(
        self, student_id: UUID, application_id: UUID
    ) -> tuple[Application, list[dict]]:
        app = await self._load_application(student_id, application_id)
        program = await self._load_program(app.program_id)
        profile = await self._load_student_profile(student_id)
        prior = await self._load_stored_items(student_id, app.program_id)
        items = self._build_items(program, profile)
        if prior:
            marks = {
                str(p.get("id") or p.get("name")): p.get("student_marked_complete")
                for p in prior
                if p.get("student_marked_complete")
            }
            for item in items:
                key = str(item.get("id") or item.get("name"))
                if marks.get(key):
                    item["student_marked_complete"] = True
                    item["completed"] = True
                    item["status"] = "completed"
        return app, items

    def first_missing_action(self, items: list[dict]) -> str | None:
        for item in items:
            if item.get("required", True) and not item.get("completed"):
                return f"Complete {item.get('name', 'item')}"
        return None

    async def apply_item_completions(
        self,
        student_id: UUID,
        application_id: UUID,
        completions: dict[str, bool],
    ) -> ApplicationChecklist:
        checklist = await self.get_checklist(student_id, application_id)
        items = list(checklist.items or [])
        for item in items:
            key = str(item.get("id") or item.get("name"))
            if completions.get(key):
                item["student_marked_complete"] = True
                item["completed"] = True
                item["status"] = "completed"
        checklist.items = items
        checklist.completion_percentage = self._compute_completion(items)
        await self.db.flush()
        return checklist
