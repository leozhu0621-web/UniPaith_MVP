import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from unipaith.models.application import (
    Application,
    ApplicationSubmission,
    OfferLetter,
)
from unipaith.models.institution import Program


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Student-facing ---

    async def create_application(
        self, student_id: UUID, program_id: UUID
    ) -> Application:
        result = await self.db.execute(
            select(Program).where(
                Program.id == program_id, Program.is_published.is_(True)
            )
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

    async def list_student_applications(
        self, student_id: UUID
    ) -> list[Application]:
        result = await self.db.execute(
            select(Application).where(Application.student_id == student_id)
        )
        return list(result.scalars().all())

    async def get_student_application(
        self, student_id: UUID, application_id: UUID
    ) -> Application:
        return await self._get_application_for_student(student_id, application_id)

    async def submit_application(
        self, student_id: UUID, application_id: UUID
    ) -> Application:
        app = await self._get_application_for_student(student_id, application_id)

        if app.status != "draft":
            raise BadRequestException("Only draft applications can be submitted")

        app.status = "submitted"
        app.submitted_at = datetime.now(timezone.utc)

        confirmation = f"UNI-{uuid.uuid4().hex[:8].upper()}"
        submission = ApplicationSubmission(
            application_id=app.id,
            submitted_at=app.submitted_at,
            confirmation_number=confirmation,
        )
        self.db.add(submission)
        await self.db.flush()
        return app

    async def withdraw_application(
        self, student_id: UUID, application_id: UUID
    ) -> None:
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
        return await self._get_application_for_institution(
            institution_id, application_id
        )

    async def make_decision(
        self,
        institution_id: UUID,
        application_id: UUID,
        decision: str,
        decision_notes: str | None = None,
        reviewer_id: UUID | None = None,
    ) -> Application:
        app = await self._get_application_for_institution(
            institution_id, application_id
        )
        if app.status not in ("submitted", "under_review", "interview"):
            raise BadRequestException(
                "Application must be submitted/under review to make a decision"
            )

        app.status = "decision_made"
        app.decision = decision
        app.decision_at = datetime.now(timezone.utc)
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
        app = await self._get_application_for_institution(
            institution_id, application_id
        )
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
        offer.response_at = datetime.now(timezone.utc)
        offer.decline_reason = decline_reason if response == "declined" else None

        if response == "accepted":
            offer.status = "accepted"
        else:
            offer.status = "declined"

        await self.db.flush()
        return offer

    # --- Helpers ---

    async def _get_application_for_student(
        self, student_id: UUID, application_id: UUID
    ) -> Application:
        result = await self.db.execute(
            select(Application).where(
                Application.id == application_id,
                Application.student_id == student_id,
            )
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
