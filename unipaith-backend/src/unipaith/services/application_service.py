from __future__ import annotations

import random
import string
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from unipaith.models.application import (
    Application,
    ApplicationSubmission,
    OfferLetter,
)
from unipaith.models.engagement import StudentEssay, StudentResume
from unipaith.models.institution import Program
from unipaith.models.student import StudentProfile


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Student-facing ---

    async def create_application(self, student_id: UUID, program_id: UUID) -> Application:
        result = await self.db.execute(
            select(Program).where(Program.id == program_id, Program.is_published.is_(True))
        )
        if not result.scalar_one_or_none():
            raise NotFoundException("Program not found or not published")

        existing = await self.db.execute(
            select(Application).where(
                Application.student_id == student_id,
                Application.program_id == program_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Application already exists for this program")

        app = Application(
            student_id=student_id,
            program_id=program_id,
            status="draft",
            completeness_status="incomplete",
        )
        self.db.add(app)
        await self.db.flush()
        return app

    async def list_student_applications(self, student_id: UUID) -> list[Application]:
        result = await self.db.execute(
            select(Application)
            .where(Application.student_id == student_id)
            .options(selectinload(Application.program))
        )
        return list(result.scalars().all())

    async def get_student_application(self, student_id: UUID, application_id: UUID) -> Application:
        return await self._get_application_for_student(student_id, application_id)

    async def submit_application(self, student_id: UUID, application_id: UUID) -> Application:
        app = await self._get_application_for_student(student_id, application_id)

        if app.status != "draft":
            raise BadRequestException("Only draft applications can be submitted")

        app.status = "submitted"
        app.submitted_at = datetime.now(UTC)

        confirmation = f"UNI-{uuid.uuid4().hex[:8].upper()}"
        submission = ApplicationSubmission(
            application_id=app.id,
            submitted_at=app.submitted_at,
            confirmation_number=confirmation,
        )
        self.db.add(submission)
        await self.db.flush()
        await self.db.refresh(app)
        return app

    async def withdraw_application(self, student_id: UUID, application_id: UUID) -> None:
        app = await self._get_application_for_student(student_id, application_id)
        if app.status not in ("draft", "submitted"):
            raise BadRequestException("Cannot withdraw application in current state")
        await self.db.delete(app)
        await self.db.flush()

    # --- Institution-facing ---

    async def list_program_applications(
        self, institution_id: UUID, program_id: UUID
    ) -> list[Application]:
        program = await self.db.execute(
            select(Program).where(
                Program.id == program_id,
                Program.institution_id == institution_id,
            )
        )
        if not program.scalar_one_or_none():
            raise NotFoundException("Program not found")

        result = await self.db.execute(
            select(Application).where(
                Application.program_id == program_id,
                Application.status != "draft",
            )
        )
        return list(result.scalars().all())

    async def get_application_detail(
        self, institution_id: UUID, application_id: UUID
    ) -> Application:
        return await self._get_application_for_institution(institution_id, application_id)

    async def make_decision(
        self,
        institution_id: UUID,
        application_id: UUID,
        decision: str,
        decision_notes: str | None = None,
        reviewer_id: UUID | None = None,
    ) -> Application:
        app = await self._get_application_for_institution(institution_id, application_id)
        if app.status not in ("submitted", "under_review", "interview"):
            raise BadRequestException(
                "Application must be submitted/under review to make a decision"
            )

        app.status = "decision_made"
        app.decision = decision
        app.decision_at = datetime.now(UTC)
        app.decision_notes = decision_notes
        app.decision_by = reviewer_id
        await self.db.flush()
        return app

    async def create_offer(
        self,
        institution_id: UUID,
        application_id: UUID,
        offer_type: str,
        tuition_amount: int | None = None,
        scholarship_amount: int = 0,
        assistantship_details: dict | None = None,
        financial_package_total: int | None = None,
        conditions: dict | None = None,
        response_deadline=None,
    ) -> OfferLetter:
        app = await self._get_application_for_institution(institution_id, application_id)
        if app.decision != "admitted":
            raise BadRequestException("Can only create offers for admitted applications")

        existing = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == application_id)
        )
        if existing.scalar_one_or_none():
            raise ConflictException("Offer already exists for this application")

        offer = OfferLetter(
            application_id=application_id,
            offer_type=offer_type,
            tuition_amount=tuition_amount,
            scholarship_amount=scholarship_amount,
            assistantship_details=assistantship_details,
            financial_package_total=financial_package_total,
            conditions=conditions,
            response_deadline=response_deadline,
            status="draft",
        )
        self.db.add(offer)
        await self.db.flush()
        return offer

    # --- Student offer response ---

    async def respond_to_offer(
        self,
        student_id: UUID,
        application_id: UUID,
        response: str,
        decline_reason: str | None = None,
    ) -> OfferLetter:
        app = await self._get_application_for_student(student_id, application_id)
        result = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id == app.id)
        )
        offer = result.scalar_one_or_none()
        if not offer:
            raise NotFoundException("No offer found for this application")
        if offer.status not in ("sent", "approved"):
            raise BadRequestException("Offer is not available for response")

        offer.student_response = response
        offer.response_at = datetime.now(UTC)
        offer.decline_reason = decline_reason if response == "declined" else None

        if response == "accepted":
            offer.status = "accepted"
        else:
            offer.status = "declined"

        await self.db.flush()
        return offer

    async def update_status(
        self,
        institution_id: UUID,
        application_id: UUID,
        new_status: str,
    ) -> Application:
        allowed_transitions: dict[str, list[str]] = {
            "submitted": ["under_review"],
            "under_review": ["interview", "decision_made"],
            "interview": ["decision_made", "under_review"],
        }

        app = await self._get_application_for_institution(institution_id, application_id)
        current = app.status
        allowed = allowed_transitions.get(current, [])
        if new_status not in allowed:
            raise BadRequestException(
                f"Cannot transition from '{current}' to '{new_status}'. Allowed: {allowed}"
            )
        app.status = new_status
        await self.db.flush()
        await self.db.refresh(app)
        return app

    # --- Submission with guardrails ---

    async def submit_application_with_guardrails(
        self, student_id: UUID, application_id: UUID
    ) -> Application:
        """Submit an application with full readiness validation and snapshot.

        1. Verifies the application exists, belongs to the student, and is in
           ``draft`` status.
        2. Runs a readiness check via :class:`ChecklistService`.
        3. If not ready, raises :class:`BadRequestException` with the list of
           missing items.
        4. Creates an :class:`ApplicationSubmission` with a frozen snapshot of
           all student materials.
        5. Generates a unique confirmation number (``UP-{year}-{6 chars}``).
        6. Transitions the application to ``submitted``.

        Returns:
            The updated :class:`Application` instance.
        """
        from unipaith.services.checklist_service import ChecklistService

        app = await self._get_application_for_student(student_id, application_id)

        if app.status != "draft":
            raise BadRequestException("Only draft applications can be submitted")

        # Run readiness check
        checklist_svc = ChecklistService(self.db)
        readiness = await checklist_svc.readiness_check(student_id, application_id)

        if not readiness["is_ready"]:
            missing = ", ".join(readiness["missing_items"])
            raise BadRequestException(
                f"Application is not ready for submission. Missing: {missing}"
            )

        # Build frozen snapshot
        snapshot = await self._build_submission_snapshot(student_id, application_id, app.program_id)

        # Generate unique confirmation number: UP-{year}-{6 random alphanumeric}
        year = datetime.now(UTC).year
        random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        confirmation = f"UP-{year}-{random_part}"

        now = datetime.now(UTC)
        app.status = "submitted"
        app.submitted_at = now
        app.completeness_status = "complete"

        submission = ApplicationSubmission(
            application_id=app.id,
            submitted_documents=snapshot,
            submitted_at=now,
            confirmation_number=confirmation,
        )
        self.db.add(submission)
        await self.db.flush()
        await self.db.refresh(app)
        return app

    async def _build_submission_snapshot(
        self, student_id: UUID, application_id: UUID, program_id: UUID
    ) -> dict:
        """Build a frozen JSONB snapshot of all student materials at submission time.

        Captures profile, academic records, test scores, activities,
        documents, essays (for this program), and the latest resume.

        Returns:
            A dictionary suitable for storing in
            ``ApplicationSubmission.submitted_documents``.
        """
        # Load profile with eager-loaded relationships
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
        if not profile:
            raise NotFoundException("Student profile not found")

        # Load essays for this program
        essay_result = await self.db.execute(
            select(StudentEssay).where(
                StudentEssay.student_id == student_id,
                StudentEssay.program_id == program_id,
            )
        )
        essays = list(essay_result.scalars().all())

        # Load latest resume
        resume_result = await self.db.execute(
            select(StudentResume)
            .where(StudentResume.student_id == student_id)
            .order_by(StudentResume.resume_version.desc())
            .limit(1)
        )
        resume = resume_result.scalar_one_or_none()

        snapshot: dict = {
            "snapshot_at": datetime.now(UTC).isoformat(),
            "profile": {
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "nationality": profile.nationality,
                "country_of_residence": profile.country_of_residence,
                "bio_text": profile.bio_text,
                "goals_text": profile.goals_text,
            },
            "academic_records": [
                {
                    "institution_name": r.institution_name,
                    "degree_type": r.degree_type,
                    "field_of_study": r.field_of_study,
                    "gpa": str(r.gpa) if r.gpa else None,
                    "gpa_scale": r.gpa_scale,
                    "start_date": r.start_date.isoformat() if r.start_date else None,
                    "end_date": r.end_date.isoformat() if r.end_date else None,
                    "is_current": r.is_current,
                    "honors": r.honors,
                    "thesis_title": r.thesis_title,
                    "country": r.country,
                }
                for r in profile.academic_records
            ],
            "test_scores": [
                {
                    "test_type": s.test_type,
                    "total_score": str(s.total_score) if s.total_score else None,
                    "section_scores": s.section_scores,
                    "test_date": s.test_date.isoformat() if s.test_date else None,
                }
                for s in profile.test_scores
            ],
            "activities": [
                {
                    "activity_type": a.activity_type,
                    "title": a.title,
                    "organization": a.organization,
                    "description": a.description,
                    "start_date": a.start_date.isoformat() if a.start_date else None,
                    "end_date": a.end_date.isoformat() if a.end_date else None,
                }
                for a in profile.activities
            ],
            "documents": [
                {
                    "document_type": d.document_type,
                    "file_name": d.file_name,
                    "file_url": d.file_url,
                }
                for d in profile.documents
            ],
            "essays": [
                {
                    "prompt_text": e.prompt_text,
                    "content": e.content,
                    "word_count": e.word_count,
                    "status": e.status,
                }
                for e in essays
            ],
            "resume": (
                {
                    "content": resume.content,
                    "rendered_pdf_url": resume.rendered_pdf_url,
                    "version": resume.resume_version,
                }
                if resume
                else None
            ),
        }
        return snapshot

    # --- Helpers ---

    async def _get_application_for_student(
        self, student_id: UUID, application_id: UUID
    ) -> Application:
        result = await self.db.execute(
            select(Application)
            .where(
                Application.id == application_id,
                Application.student_id == student_id,
            )
            .options(selectinload(Application.program))
        )
        app = result.scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found")
        return app

    async def _get_application_for_institution(
        self, institution_id: UUID, application_id: UUID
    ) -> Application:
        result = await self.db.execute(
            select(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Application.id == application_id,
                Program.institution_id == institution_id,
            )
        )
        app = result.scalar_one_or_none()
        if not app:
            raise NotFoundException("Application not found")
        return app
