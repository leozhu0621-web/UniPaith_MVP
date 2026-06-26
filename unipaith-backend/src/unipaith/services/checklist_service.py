"""
Checklist service — auto-generate and manage the program-adaptive application
checklist (spec 15 §5). Each item carries type / owner / expected format /
required-level / status / mismatch so the workspace can render it consistently
and the "ready to submit" gate (spec 15 §4.2) can evaluate completeness.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from unipaith.core.exceptions import NotFoundException
from unipaith.models.application import Application, ApplicationChecklist
from unipaith.models.engagement import StudentEssay, StudentResume
from unipaith.models.institution import Program, ProgramChecklistItem
from unipaith.models.student import RecommendationRequest, StudentProfile

logger = logging.getLogger(__name__)

# Essay / resume / recommendation statuses that count as "done".
_DONE_ESSAY_STATUSES = {"finalized", "final", "complete", "completed", "submitted", "reviewed"}
_DONE_RESUME_STATUSES = {"finalized", "final", "complete", "completed"}
_SUBMITTED_REC_STATUSES = {"submitted", "complete", "completed", "received"}
_PENDING_REC_STATUSES = {"requested", "in_progress", "sent", "pending"}

# Map an institution-published checklist category → (item_type, owner) for display.
_CATEGORY_META: dict[str, tuple[str, str]] = {
    "essay": ("essay", "student"),
    "test_score": ("test", "student"),
    "recommendation": ("recommendation", "recommender"),
    "interview": ("interview", "student"),
    "portfolio": ("portfolio", "student"),
    "document": ("document", "student"),
    "financial": ("fee", "student"),
    "other": ("document", "student"),
}


class ChecklistService:
    """Generate and query per-application readiness checklists."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Loaders
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

    async def _load_published_items(self, program_id: UUID) -> list[ProgramChecklistItem]:
        """The institution's published requirement checklist (spec 15 §5)."""
        result = await self.db.execute(
            select(ProgramChecklistItem)
            .where(
                ProgramChecklistItem.program_id == program_id,
                ProgramChecklistItem.is_active.is_(True),
            )
            .order_by(ProgramChecklistItem.sort_order)
        )
        return list(result.scalars().all())

    async def _load_materials(
        self, student_id: UUID, program_id: UUID
    ) -> tuple[list[StudentEssay], StudentResume | None, list[RecommendationRequest]]:
        essays = (
            (
                await self.db.execute(
                    select(StudentEssay).where(
                        StudentEssay.student_id == student_id,
                        StudentEssay.program_id == program_id,
                    )
                )
            )
            .scalars()
            .all()
        )
        resume = (
            await self.db.execute(
                select(StudentResume)
                .where(StudentResume.student_id == student_id)
                .order_by(StudentResume.resume_version.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
        recs = (
            (
                await self.db.execute(
                    select(RecommendationRequest).where(
                        RecommendationRequest.student_id == student_id,
                    )
                )
            )
            .scalars()
            .all()
        )
        # Recommenders targeting this program OR with no specific target apply here.
        recs = [r for r in recs if r.target_program_id in (None, program_id)]
        return list(essays), resume, recs

    async def _load_manual_keys(self, student_id: UUID, program_id: UUID) -> set[str]:
        """Item keys the student manually marked complete (external mode / §7)."""
        result = await self.db.execute(
            select(ApplicationChecklist).where(
                ApplicationChecklist.student_id == student_id,
                ApplicationChecklist.program_id == program_id,
            )
        )
        checklist = result.scalar_one_or_none()
        if checklist is None or not checklist.items:
            return set()
        return {
            it.get("key") for it in checklist.items if it.get("manual_complete") and it.get("key")
        }

    # ------------------------------------------------------------------
    # Completion helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _essays_done(essays: list[StudentEssay]) -> str:
        if any((e.status or "").lower() in _DONE_ESSAY_STATUSES for e in essays):
            return "completed"
        if any((e.content or "").strip() for e in essays):
            return "in_progress"
        return "not_started"

    @staticmethod
    def _resume_done(resume: StudentResume | None) -> str:
        if resume is None:
            return "not_started"
        if (resume.status or "").lower() in _DONE_RESUME_STATUSES:
            return "completed"
        return "in_progress"

    @staticmethod
    def _recs_done(recs: list[RecommendationRequest], required: int) -> str:
        submitted = sum(1 for r in recs if (r.status or "").lower() in _SUBMITTED_REC_STATUSES)
        if submitted >= required:
            return "completed"
        if submitted > 0 or any((r.status or "").lower() in _PENDING_REC_STATUSES for r in recs):
            return "in_progress"
        return "not_started"

    # ------------------------------------------------------------------
    # Item builders
    # ------------------------------------------------------------------

    def _item(
        self,
        *,
        key: str,
        name: str,
        category: str,
        item_type: str,
        owner: str,
        required: bool,
        status: str,
        expected_format: str | None = None,
        description: str | None = None,
        requirement_level: str | None = None,
        manual_keys: set[str] | None = None,
    ) -> dict:
        if manual_keys and key in manual_keys:
            status = "completed"
        completed = status == "completed"
        # A required item left blocked is a mismatch the UI flags early (§5).
        mismatch = status == "blocked"
        return {
            "key": key,
            "name": name,
            "item_name": name,
            "category": category,
            "item_type": item_type,
            "owner": owner,
            "required": required,
            "requirement_level": requirement_level or ("required" if required else "optional"),
            "expected_format": expected_format,
            "status": status,
            "completed": completed,
            "manual_complete": bool(manual_keys and key in manual_keys),
            "mismatch": mismatch,
            "description": description,
        }

    def _build_items(
        self,
        program: Program,
        profile: StudentProfile,
        published: list[ProgramChecklistItem],
        essays: list[StudentEssay],
        resume: StudentResume | None,
        recs: list[RecommendationRequest],
        manual_keys: set[str] | None = None,
    ) -> list[dict]:
        """Derive checklist items (spec 15 §5) from the program's published
        requirement checklist (preferred) or the legacy ``requirements`` blob,
        joined with what the student has actually completed."""
        manual_keys = manual_keys or set()
        reqs: dict = program.requirements or {}
        rec_required = int(reqs.get("recommendation_letters", 2) or 2)
        items: list[dict] = []

        # --- Always: the student's own core record (spec 44 §4.2 core fields) ---
        has_personal = bool(
            profile.first_name
            and profile.last_name
            and profile.nationality
            and profile.country_of_residence
        )
        items.append(
            self._item(
                key="personal_info",
                name="Personal Information",
                category="personal_info",
                item_type="form",
                owner="student",
                required=True,
                status="completed" if has_personal else "not_started",
                expected_format="Full name, nationality, country of residence",
                description="Your core identity record.",
                manual_keys=manual_keys,
            )
        )
        items.append(
            self._item(
                key="academic_records",
                name="Academic Records",
                category="academic_records",
                item_type="transcript",
                owner="student",
                required=True,
                status="completed" if len(profile.academic_records) > 0 else "not_started",
                expected_format="At least one degree record with GPA",
                description="Your academic history.",
                manual_keys=manual_keys,
            )
        )

        essay_status = self._essays_done(essays)
        resume_status = self._resume_done(resume)
        rec_status = self._recs_done(recs, rec_required)
        doc_types = {d.document_type for d in profile.documents}
        # Inputs for satisfying institution-named document / test_score items that
        # the student's coarse upload types can't name (see the override below).
        uploaded_doc_count = len(profile.documents)
        doc_seen = 0
        test_types = {s.test_type for s in profile.test_scores}

        if published:
            # Institution-published requirement checklist drives the rest (§5).
            for pi in published:
                item_type, owner = _CATEGORY_META.get(pi.category, ("document", "student"))
                required = pi.requirement_level == "required"
                if pi.requirement_level == "not_applicable":
                    continue
                status = self._published_status(
                    pi, doc_types, essay_status, resume_status, rec_status
                )
                # An institution publishes free-text document / test_score items
                # ("Statement of Purpose", "GRE Scores"); the student's uploads use
                # 6 coarse types and `_published_status` only exact-matches those,
                # so a real upload/score never satisfied a named item and the
                # student was wrongly told "missing" + blocked from submitting.
                # Fill those two gaps from what's actually on file.
                if pi.category == "document" and status != "completed":
                    slug = pi.item_name.lower().replace(" ", "_")
                    if not ("resume" in slug or "cv" in slug):
                        # Credit each generic document requirement from the pool of
                        # uploaded documents in order — N uploads satisfy the first
                        # N items (no false-complete-all on a single upload).
                        status = "completed" if doc_seen < uploaded_doc_count else "not_started"
                        doc_seen += 1
                elif pi.category == "test_score":
                    name_l = (pi.item_name or "").lower()
                    mentioned = [
                        t
                        for t in (
                            "gre",
                            "gmat",
                            "toefl",
                            "ielts",
                            "sat",
                            "act",
                            "lsat",
                            "mcat",
                            "duolingo",
                        )
                        if t in name_l
                    ]
                    if mentioned:
                        status = (
                            "completed"
                            if any(t in test_types for t in mentioned)
                            else "not_started"
                        )
                    elif test_types:
                        # Generic "Test Scores" requirement, any score on file.
                        status = "completed"
                items.append(
                    self._item(
                        key=f"prog_{pi.id}",
                        name=pi.item_name,
                        category=pi.category,
                        item_type=item_type,
                        owner=owner,
                        required=required,
                        requirement_level=pi.requirement_level,
                        status=status,
                        expected_format=pi.instructions or pi.description,
                        description=pi.description,
                        manual_keys=manual_keys,
                    )
                )
            return items

        # --- Fallback: derive from the legacy requirements blob ---
        if reqs.get("gre_required"):
            has_gre = any(s.test_type == "gre" for s in profile.test_scores)
            items.append(
                self._item(
                    key="test_gre",
                    name="GRE Score",
                    category="test_scores",
                    item_type="test",
                    owner="student",
                    required=True,
                    status="completed" if has_gre else "not_started",
                    expected_format="Official GRE score report",
                    manual_keys=manual_keys,
                )
            )
        toefl_min, ielts_min = reqs.get("toefl_min"), reqs.get("ielts_min")
        if toefl_min or ielts_min:
            has_english = any(s.test_type in ("toefl", "ielts") for s in profile.test_scores)
            fmt = " · ".join(
                p
                for p in (
                    f"TOEFL ≥ {toefl_min}" if toefl_min else "",
                    f"IELTS ≥ {ielts_min}" if ielts_min else "",
                )
                if p
            )
            items.append(
                self._item(
                    key="test_english",
                    name="English Proficiency",
                    category="test_scores",
                    item_type="test",
                    owner="student",
                    required=True,
                    status="completed" if has_english else "not_started",
                    expected_format=fmt,
                    manual_keys=manual_keys,
                )
            )

        essay_prompts: list = reqs.get("essays", [])
        items.append(
            self._item(
                key="essays",
                name="Essays" if essay_prompts else "Statement of Purpose",
                category="essays",
                item_type="essay",
                owner="student",
                required=True,
                status=essay_status,
                expected_format=(
                    f"{len(essay_prompts)} essay(s)"
                    if essay_prompts
                    else "Statement of purpose / personal statement"
                ),
                manual_keys=manual_keys,
            )
        )
        items.append(
            self._item(
                key="resume",
                name="Resume / CV",
                category="resume",
                item_type="resume",
                owner="student",
                required=True,
                status=resume_status,
                expected_format="Up-to-date academic resume (PDF)",
                manual_keys=manual_keys,
            )
        )
        items.append(
            self._item(
                key="recommendations",
                name="Recommendation Letters",
                category="recommendation_letters",
                item_type="recommendation",
                owner="recommender",
                required=True,
                status=rec_status,
                expected_format=f"{rec_required} recommender(s)",
                manual_keys=manual_keys,
            )
        )

        for doc_name in reqs.get("required_documents", []):
            slug = doc_name.lower().replace(" ", "_")
            items.append(
                self._item(
                    key=f"doc_{slug}",
                    name=doc_name,
                    category="documents",
                    item_type="document",
                    owner="student",
                    required=True,
                    status="completed" if slug in doc_types else "not_started",
                    expected_format="Document upload",
                    manual_keys=manual_keys,
                )
            )

        return items

    @staticmethod
    def _published_status(
        pi: ProgramChecklistItem,
        doc_types: set[str],
        essay_status: str,
        resume_status: str,
        rec_status: str,
    ) -> str:
        """Best-effort completion for an institution-published item from student data.
        Categories we cannot infer (portfolio/interview/financial) rely on the
        student manually marking them complete (§7)."""
        if pi.category == "essay":
            return essay_status
        if pi.category == "recommendation":
            return rec_status
        if pi.category == "document":
            slug = pi.item_name.lower().replace(" ", "_")
            if slug in doc_types:
                return "completed"
            if "resume" in slug or "cv" in slug:
                return resume_status
            return "not_started"
        if pi.category == "test_score":
            return "not_started"
        return "not_started"

    @staticmethod
    def _compute_completion(items: list[dict]) -> int:
        """Return completion percentage (0-100) over REQUIRED items."""
        required_items = [i for i in items if i.get("required")]
        if not required_items:
            return 100
        completed = sum(1 for i in required_items if i.get("status") == "completed")
        return int((completed / len(required_items)) * 100)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def _gather(self, student_id: UUID, application_id: UUID):
        app = await self._load_application(student_id, application_id)
        program = await self._load_program(app.program_id)
        profile = await self._load_student_profile(student_id)
        published = await self._load_published_items(app.program_id)
        essays, resume, recs = await self._load_materials(student_id, app.program_id)
        manual_keys = await self._load_manual_keys(student_id, app.program_id)
        items = self._build_items(program, profile, published, essays, resume, recs, manual_keys)
        return app, program, items

    async def _upsert_checklist(
        self, student_id: UUID, program_id: UUID, items: list[dict]
    ) -> ApplicationChecklist:
        """Persist the rendered items, forcing the JSONB column dirty.

        ``flag_modified`` is required: assigning a list whose values equal the
        previously-loaded snapshot is otherwise NOT detected as a change.
        """
        completion = self._compute_completion(items)
        result = await self.db.execute(
            select(ApplicationChecklist).where(
                ApplicationChecklist.student_id == student_id,
                ApplicationChecklist.program_id == program_id,
            )
        )
        checklist = result.scalar_one_or_none()
        if checklist is None:
            checklist = ApplicationChecklist(
                student_id=student_id,
                program_id=program_id,
                items=items,
                completion_percentage=completion,
                auto_generated_at=datetime.now(UTC),
            )
            self.db.add(checklist)
        else:
            checklist.items = items
            checklist.completion_percentage = completion
            checklist.auto_generated_at = datetime.now(UTC)
            flag_modified(checklist, "items")
        await self.db.flush()
        return checklist

    async def generate_checklist(
        self, student_id: UUID, application_id: UUID
    ) -> ApplicationChecklist:
        """Auto-generate (upsert) a checklist; preserves manual completions."""
        app, _, items = await self._gather(student_id, application_id)
        checklist = await self._upsert_checklist(student_id, app.program_id, items)
        app.readiness_pct = checklist.completion_percentage
        await self.db.flush()
        return checklist

    async def get_checklist(self, student_id: UUID, application_id: UUID) -> ApplicationChecklist:
        """Return the checklist, generating one on first access."""
        app = await self._load_application(student_id, application_id)
        result = await self.db.execute(
            select(ApplicationChecklist).where(
                ApplicationChecklist.student_id == student_id,
                ApplicationChecklist.program_id == app.program_id,
            )
        )
        checklist = result.scalar_one_or_none()
        if checklist is None:
            return await self.generate_checklist(student_id, application_id)
        return checklist

    async def toggle_item(
        self, student_id: UUID, application_id: UUID, item_key: str, completed: bool
    ) -> ApplicationChecklist:
        """Manually mark a checklist item complete/incomplete (spec 15 §7 —
        external submissions, or any item the platform can't auto-verify).

        Builds the item set fresh from an in-memory manual-keys set (no in-place
        mutation of the loaded JSONB) so derived statuses re-evaluate while the
        manual override is preserved across regenerations.
        """
        app = await self._load_application(student_id, application_id)
        manual_keys = await self._load_manual_keys(student_id, app.program_id)
        if completed:
            manual_keys.add(item_key)
        else:
            manual_keys.discard(item_key)

        program = await self._load_program(app.program_id)
        profile = await self._load_student_profile(student_id)
        published = await self._load_published_items(app.program_id)
        essays, resume, recs = await self._load_materials(student_id, app.program_id)
        items = self._build_items(program, profile, published, essays, resume, recs, manual_keys)

        if item_key not in {it["key"] for it in items}:
            raise NotFoundException("Checklist item not found")

        checklist = await self._upsert_checklist(student_id, app.program_id, items)
        app.readiness_pct = checklist.completion_percentage
        await self.db.flush()
        return checklist

    async def readiness_check(self, student_id: UUID, application_id: UUID) -> dict:
        """Evaluate readiness for submission and persist ``readiness_pct``.

        Returns ``{is_ready, completion_percentage, missing_items, warnings}``.
        """
        app, program, items = await self._gather(student_id, application_id)
        completion = self._compute_completion(items)
        missing = [i["name"] for i in items if i.get("required") and i.get("status") != "completed"]

        warnings: list[str] = []
        if program.application_deadline:
            days_left = (program.application_deadline - date.today()).days
            if days_left < 0:
                warnings.append("The application deadline has passed.")
            elif days_left <= 7:
                warnings.append(f"Deadline is in {days_left} day(s) — submit soon!")
            elif days_left <= 30:
                warnings.append(f"Deadline is in {days_left} days — start finalising.")

        app.readiness_pct = completion
        await self.db.flush()
        return {
            "is_ready": len(missing) == 0,
            "completion_percentage": completion,
            "missing_items": missing,
            "warnings": warnings,
        }

    async def is_ready(self, student_id: UUID, application_id: UUID) -> tuple[bool, list[str]]:
        """Lightweight gate used by the submit flow."""
        result = await self.readiness_check(student_id, application_id)
        return result["is_ready"], result["missing_items"]
