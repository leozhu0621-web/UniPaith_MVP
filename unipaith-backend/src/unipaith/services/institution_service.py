from __future__ import annotations

import math
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.jobs import on_program_updated
from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from unipaith.models.application import Application, OfferLetter
from unipaith.models.engagement import Conversation, Message
from unipaith.models.institution import (
    Campaign,
    CampaignRecipient,
    Event,
    Institution,
    Program,
    TargetSegment,
)
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.workflow import Notification
from unipaith.schemas.institution import (
    AnalyticsResponse,
    CampaignMetricsResponse,
    CreateCampaignRequest,
    CreateInstitutionRequest,
    CreateProgramRequest,
    CreateSegmentRequest,
    DashboardSummaryResponse,
    MonthlyApplicationCount,
    PaginatedResponse,
    ProgramApplicationCount,
    ProgramSummaryResponse,
    UpdateCampaignRequest,
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
        await self.db.refresh(institution)
        return institution

    async def update_institution(
        self, user_id: UUID, data: UpdateInstitutionRequest
    ) -> Institution:
        institution = await self._get_institution_for_user(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(institution, key, value)
        await self.db.flush()
        await self.db.refresh(institution)
        return institution

    # --- Programs ---

    async def list_programs(self, institution_id: UUID) -> list[Program]:
        result = await self.db.execute(
            select(Program).where(Program.institution_id == institution_id)
        )
        return list(result.scalars().all())

    async def get_program(self, institution_id: UUID, program_id: UUID) -> Program:
        return await self._verify_program_ownership(institution_id, program_id)

    async def create_program(self, institution_id: UUID, data: CreateProgramRequest) -> Program:
        program = Program(
            institution_id=institution_id,
            is_published=False,
            **data.model_dump(),
        )
        self.db.add(program)
        await self.db.flush()
        await on_program_updated(self.db, program.id)
        await self.db.refresh(program)
        return program

    async def update_program(
        self, institution_id: UUID, program_id: UUID, data: UpdateProgramRequest
    ) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(program, key, value)
        await self.db.flush()
        await on_program_updated(self.db, program.id)
        await self.db.refresh(program)
        return program

    async def publish_program(self, institution_id: UUID, program_id: UUID) -> Program:
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
        await on_program_updated(self.db, program.id)
        await self.db.refresh(program)
        return program

    async def unpublish_program(self, institution_id: UUID, program_id: UUID) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        program.is_published = False
        await self.db.flush()
        await on_program_updated(self.db, program.id)
        await self.db.refresh(program)
        return program

    async def delete_program(self, institution_id: UUID, program_id: UUID) -> None:
        program = await self._verify_program_ownership(institution_id, program_id)
        app_count = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(Application.program_id == program_id)
        )
        if app_count.scalar_one() > 0:
            raise ConflictException("Cannot delete program with existing applications")
        await self.db.delete(program)
        await self.db.flush()

    # --- Target Segments ---

    async def list_segments(self, institution_id: UUID) -> list[TargetSegment]:
        result = await self.db.execute(
            select(TargetSegment).where(TargetSegment.institution_id == institution_id)
        )
        return list(result.scalars().all())

    async def create_segment(
        self, institution_id: UUID, data: CreateSegmentRequest
    ) -> TargetSegment:
        segment = TargetSegment(institution_id=institution_id, **data.model_dump())
        self.db.add(segment)
        await self.db.flush()
        await self.db.refresh(segment)
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
        await self.db.refresh(segment)
        return segment

    async def delete_segment(self, institution_id: UUID, segment_id: UUID) -> None:
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

    async def resolve_segment_members(
        self, institution_id: UUID, segment_id: UUID,
    ) -> list[UUID]:
        """Execute segment criteria and return matching student IDs."""
        result = await self.db.execute(
            select(TargetSegment).where(
                TargetSegment.id == segment_id,
                TargetSegment.institution_id == institution_id,
            )
        )
        segment = result.scalar_one_or_none()
        if not segment:
            raise NotFoundException("Segment not found")

        criteria = segment.criteria or {}
        programs = await self.list_programs(institution_id)
        program_ids = [p.id for p in programs]
        if segment.program_id:
            program_ids = [segment.program_id]
        if not program_ids:
            return []

        stmt = (
            select(StudentProfile.id)
            .distinct()
        )

        # Filter by application status
        statuses = criteria.get("statuses")
        if statuses:
            stmt = stmt.join(
                Application, Application.student_id == StudentProfile.user_id
            ).where(
                Application.program_id.in_(program_ids),
                Application.status.in_(statuses),
            )

        # Filter by minimum match score
        min_match_score = criteria.get("min_match_score")
        if min_match_score is not None:
            stmt = stmt.join(
                MatchResult, MatchResult.student_id == StudentProfile.id
            ).where(
                MatchResult.program_id.in_(program_ids),
                MatchResult.match_score >= min_match_score,
                MatchResult.is_stale.is_(False),
            )

        # If no specific criteria, return all students who have applied
        if not statuses and min_match_score is None:
            stmt = stmt.join(
                Application, Application.student_id == StudentProfile.user_id
            ).where(
                Application.program_id.in_(program_ids),
                Application.status != "draft",
            )

        result = await self.db.execute(stmt)
        return [row[0] for row in result.all()]

    # --- Dashboard Summary ---

    async def get_dashboard_summary(self, institution_id: UUID) -> DashboardSummaryResponse:
        # Program counts
        prog_result = await self.db.execute(
            select(
                func.count().label("total"),
                func.count().filter(Program.is_published.is_(True)).label("published"),
            ).where(Program.institution_id == institution_id)
        )
        prog_row = prog_result.one()

        # Total applications (non-draft) across all programs
        app_count_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.status != "draft",
            )
        )
        total_apps = app_count_result.scalar_one()

        # Pending review count
        pending_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.status.in_(["submitted", "under_review"]),
                Application.decision.is_(None),
            )
        )
        pending_review = pending_result.scalar_one()

        # Active events count
        now = datetime.now(UTC)
        events_result = await self.db.execute(
            select(func.count())
            .select_from(Event)
            .where(
                Event.institution_id == institution_id,
                Event.end_time > now,
            )
        )
        active_events = events_result.scalar_one()

        # Unread messages count
        unread_result = await self.db.execute(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(
                Conversation.institution_id == institution_id,
                Message.sender_type == "student",
                Message.read_at.is_(None),
            )
        )
        unread_messages = unread_result.scalar_one()

        # Acceptance rate
        decisions_result = await self.db.execute(
            select(Application.decision, func.count())
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.decision.isnot(None),
            )
            .group_by(Application.decision)
        )
        decisions = {row[0]: row[1] for row in decisions_result.all()}
        decided_count = sum(decisions.values())
        admitted_count = decisions.get("admitted", 0)
        acceptance_rate = admitted_count / decided_count if decided_count > 0 else None

        # Yield rate
        yield_result = await self.db.execute(
            select(
                func.count().label("total_offers"),
                func.count().filter(OfferLetter.student_response == "accepted").label("accepted"),
            )
            .select_from(OfferLetter)
            .join(Application, OfferLetter.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        yield_row = yield_result.one()
        yield_rate = (
            yield_row.accepted / yield_row.total_offers if yield_row.total_offers > 0 else None
        )

        return DashboardSummaryResponse(
            program_count=prog_row.total,
            published_program_count=prog_row.published,
            total_applications=total_apps,
            pending_review_count=pending_review,
            active_events_count=active_events,
            unread_messages_count=unread_messages,
            acceptance_rate=acceptance_rate,
            yield_rate=yield_rate,
        )

    # --- Analytics ---

    async def get_analytics(self, institution_id: UUID) -> AnalyticsResponse:
        # Base query for institution's applications (non-draft)
        base_filter = [
            Program.institution_id == institution_id,
            Application.status != "draft",
        ]

        # Total applications
        total_result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .join(Program, Application.program_id == Program.id)
            .where(*base_filter)
        )
        total_apps = total_result.scalar_one()

        # Apps by status
        status_result = await self.db.execute(
            select(Application.status, func.count())
            .join(Program, Application.program_id == Program.id)
            .where(*base_filter)
            .group_by(Application.status)
        )
        apps_by_status = {row[0]: row[1] for row in status_result.all()}

        # Decisions breakdown
        decisions_result = await self.db.execute(
            select(Application.decision, func.count())
            .join(Program, Application.program_id == Program.id)
            .where(*base_filter, Application.decision.isnot(None))
            .group_by(Application.decision)
        )
        decisions_breakdown = {row[0]: row[1] for row in decisions_result.all()}

        # Acceptance rate
        decided_count = sum(decisions_breakdown.values())
        admitted_count = decisions_breakdown.get("admitted", 0)
        acceptance_rate = admitted_count / decided_count if decided_count > 0 else None

        # Average match score
        avg_score_result = await self.db.execute(
            select(func.avg(Application.match_score))
            .join(Program, Application.program_id == Program.id)
            .where(*base_filter, Application.match_score.isnot(None))
        )
        avg_match_score_raw = avg_score_result.scalar_one()
        avg_match_score = float(avg_match_score_raw) if avg_match_score_raw else None

        # Yield rate: accepted offers / total offers sent
        yield_result = await self.db.execute(
            select(
                func.count().label("total_offers"),
                func.count().filter(OfferLetter.student_response == "accepted").label("accepted"),
            )
            .select_from(OfferLetter)
            .join(Application, OfferLetter.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        yield_row = yield_result.one()
        yield_rate = (
            yield_row.accepted / yield_row.total_offers if yield_row.total_offers > 0 else None
        )

        # Apps by program
        prog_result = await self.db.execute(
            select(Program.program_name, func.count())
            .select_from(Application)
            .join(Program, Application.program_id == Program.id)
            .where(*base_filter)
            .group_by(Program.program_name)
            .order_by(func.count().desc())
        )
        apps_by_program = [
            ProgramApplicationCount(program_name=row[0], count=row[1]) for row in prog_result.all()
        ]

        # Apps by month (last 12 months)
        month_result = await self.db.execute(
            select(
                func.to_char(Application.submitted_at, "YYYY-MM").label("month"),
                func.count(),
            )
            .join(Program, Application.program_id == Program.id)
            .where(
                *base_filter,
                Application.submitted_at.isnot(None),
            )
            .group_by("month")
            .order_by("month")
        )
        apps_by_month = [
            MonthlyApplicationCount(month=row[0], count=row[1]) for row in month_result.all()
        ]

        return AnalyticsResponse(
            total_applications=total_apps,
            acceptance_rate=acceptance_rate,
            avg_match_score=avg_match_score,
            yield_rate=yield_rate,
            apps_by_status=apps_by_status,
            apps_by_program=apps_by_program,
            apps_by_month=apps_by_month,
            decisions_breakdown=decisions_breakdown,
        )

    # --- Campaigns ---

    async def list_campaigns(
        self, institution_id: UUID, status_filter: str | None = None
    ) -> list[Campaign]:
        stmt = select(Campaign).where(Campaign.institution_id == institution_id)
        if status_filter:
            stmt = stmt.where(Campaign.status == status_filter)
        stmt = stmt.order_by(Campaign.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_campaign(self, institution_id: UUID, data: CreateCampaignRequest) -> Campaign:
        campaign = Campaign(
            institution_id=institution_id,
            status="draft",
            **data.model_dump(),
        )
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def update_campaign(
        self, institution_id: UUID, campaign_id: UUID, data: UpdateCampaignRequest
    ) -> Campaign:
        campaign = await self._verify_campaign_ownership(institution_id, campaign_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(campaign, key, value)
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def delete_campaign(self, institution_id: UUID, campaign_id: UUID) -> None:
        campaign = await self._verify_campaign_ownership(institution_id, campaign_id)
        if campaign.status == "sent":
            raise BadRequestException("Cannot delete a sent campaign")
        await self.db.delete(campaign)
        await self.db.flush()

    async def preview_campaign_audience(
        self, institution_id: UUID, campaign_id: UUID,
    ) -> int:
        """Return the number of students that would receive this campaign."""
        campaign = await self._verify_campaign_ownership(institution_id, campaign_id)
        if campaign.segment_id:
            student_ids = await self.resolve_segment_members(
                institution_id, campaign.segment_id,
            )
            return len(student_ids)
        # No segment — count all non-draft applicants for the campaign's program(s)
        programs = await self.list_programs(institution_id)
        program_ids = [campaign.program_id] if campaign.program_id else [p.id for p in programs]
        if not program_ids:
            return 0
        result = await self.db.execute(
            select(func.count(Application.student_id.distinct())).where(
                Application.program_id.in_(program_ids),
                Application.status != "draft",
            )
        )
        return result.scalar_one() or 0

    async def send_campaign(self, institution_id: UUID, campaign_id: UUID) -> Campaign:
        campaign = await self._verify_campaign_ownership(institution_id, campaign_id)
        if campaign.status == "sent":
            raise BadRequestException("Campaign already sent")
        if not campaign.message_subject and not campaign.message_body:
            raise BadRequestException("Campaign must have subject or body")

        # Resolve recipients from segment
        student_ids: list[UUID] = []
        if campaign.segment_id:
            student_ids = await self.resolve_segment_members(
                institution_id, campaign.segment_id,
            )
        else:
            # No segment — target all non-draft applicants for the campaign's program(s)
            programs = await self.list_programs(institution_id)
            program_ids = [campaign.program_id] if campaign.program_id else [p.id for p in programs]
            if program_ids:
                result = await self.db.execute(
                    select(Application.student_id)
                    .distinct()
                    .where(
                        Application.program_id.in_(program_ids),
                        Application.status != "draft",
                    )
                )
                student_ids = [row[0] for row in result.all()]

        # Create CampaignRecipient rows and in-app notifications
        now = datetime.now(UTC)
        for sid in student_ids:
            # Deduplicate
            existing = await self.db.execute(
                select(CampaignRecipient).where(
                    CampaignRecipient.campaign_id == campaign_id,
                    CampaignRecipient.student_id == sid,
                )
            )
            if existing.scalar_one_or_none():
                continue
            recipient = CampaignRecipient(
                campaign_id=campaign_id,
                student_id=sid,
                delivered_at=now,
            )
            self.db.add(recipient)

            # Create in-app notification (map student_profile.id → user_id)
            profile_result = await self.db.execute(
                select(StudentProfile.user_id).where(StudentProfile.id == sid)
            )
            user_id = profile_result.scalar_one_or_none()
            if user_id:
                notification = Notification(
                    user_id=user_id,
                    title=campaign.message_subject or campaign.campaign_name,
                    body=campaign.message_body or "",
                    notification_type="campaign",
                    action_url="/s/messages",
                )
                self.db.add(notification)

        campaign.status = "sent"
        campaign.sent_at = now
        await self.db.flush()

        # Send emails for email-type campaigns
        if campaign.campaign_type in ("email", None):
            from unipaith.services.campaign_email_service import CampaignEmailService

            inst_result = await self.db.execute(
                select(Institution).where(Institution.id == institution_id)
            )
            inst = inst_result.scalar_one_or_none()
            inst_name = inst.name if inst else "UniPaith"

            program_name = None
            if campaign.program_id:
                prog_result = await self.db.execute(
                    select(Program).where(Program.id == campaign.program_id)
                )
                p = prog_result.scalar_one_or_none()
                program_name = p.program_name if p else None

            email_svc = CampaignEmailService(self.db)
            await email_svc.send_campaign_emails(campaign, inst_name, program_name)

        await self.db.refresh(campaign)
        return campaign

    async def get_campaign_metrics(
        self, institution_id: UUID, campaign_id: UUID
    ) -> CampaignMetricsResponse:
        await self._verify_campaign_ownership(institution_id, campaign_id)
        result = await self.db.execute(
            select(
                func.count().label("total"),
                func.count().filter(CampaignRecipient.delivered_at.isnot(None)).label("delivered"),
                func.count().filter(CampaignRecipient.opened_at.isnot(None)).label("opened"),
                func.count().filter(CampaignRecipient.clicked_at.isnot(None)).label("clicked"),
                func.count().filter(CampaignRecipient.responded_at.isnot(None)).label("responded"),
            ).where(CampaignRecipient.campaign_id == campaign_id)
        )
        row = result.one()
        return CampaignMetricsResponse(
            campaign_id=campaign_id,
            total_recipients=row.total,
            delivered=row.delivered,
            opened=row.opened,
            clicked=row.clicked,
            responded=row.responded,
        )

    async def _verify_campaign_ownership(self, institution_id: UUID, campaign_id: UUID) -> Campaign:
        result = await self.db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.institution_id == institution_id,
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise NotFoundException("Campaign not found")
        return campaign

    # --- Public Program Browsing ---

    async def search_programs(
        self,
        query: str | None = None,
        country: str | None = None,
        degree_type: str | None = None,
        institution_id: UUID | None = None,
        min_tuition: int | None = None,
        max_tuition: int | None = None,
        sort_by: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[ProgramSummaryResponse]:
        stmt = (
            select(Program, Institution)
            .join(Institution, Program.institution_id == Institution.id)
            .where(Program.is_published.is_(True))
        )

        if query:
            from sqlalchemy import literal_column

            regconfig = literal_column("'english'::regconfig")
            search_text = (
                func.coalesce(Program.program_name, "")
                + " "
                + func.coalesce(Program.description_text, "")
                + " "
                + func.coalesce(Program.department, "")
            )
            ts_vector = func.to_tsvector(regconfig, search_text)
            ts_query = func.plainto_tsquery(regconfig, query)
            stmt = stmt.where(ts_vector.op("@@")(ts_query))
        if country:
            stmt = stmt.where(Institution.country.ilike(f"%{country}%"))
        if degree_type:
            stmt = stmt.where(Program.degree_type == degree_type)
        if institution_id:
            stmt = stmt.where(Program.institution_id == institution_id)
        if min_tuition is not None:
            stmt = stmt.where(Program.tuition >= min_tuition)
        if max_tuition is not None:
            stmt = stmt.where(Program.tuition <= max_tuition)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        if sort_by == "tuition_asc":
            stmt = stmt.order_by(Program.tuition.asc().nulls_last())
        elif sort_by == "tuition_desc":
            stmt = stmt.order_by(Program.tuition.desc().nulls_last())
        elif sort_by == "deadline":
            stmt = stmt.order_by(Program.application_deadline.asc().nulls_last())
        else:
            stmt = stmt.order_by(Program.program_name.asc())

        offset = (page - 1) * page_size
        results = await self.db.execute(stmt.offset(offset).limit(page_size))
        rows = results.all()

        items = [
            ProgramSummaryResponse(
                id=prog.id,
                institution_id=prog.institution_id,
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
            select(Program).where(Program.id == program_id, Program.is_published.is_(True))
        )
        program = result.scalar_one_or_none()
        if not program:
            raise NotFoundException("Program not found")
        return program

    async def get_public_institution(self, institution_id: UUID) -> Institution:
        result = await self.db.execute(
            select(Institution).where(Institution.id == institution_id)
        )
        institution = result.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution not found")
        return institution

    async def semantic_search_programs(
        self,
        query: str,
        limit: int = 20,
    ) -> list[ProgramSummaryResponse]:
        from unipaith.ai.embedding_client import get_embedding_client

        client = get_embedding_client()
        query_embedding = await client.embed_text(query)
        vec_str = "[" + ",".join(str(float(v)) for v in query_embedding) + "]"

        vector_query = text(
            "SELECT e.entity_id, 1 - (e.embedding <=> cast(:query_vec as vector)) as similarity "
            "FROM embeddings e "
            "JOIN programs p ON e.entity_id = p.id "
            "WHERE e.entity_type = 'program' "
            "AND p.is_published = true "
            "ORDER BY e.embedding <=> cast(:query_vec as vector) "
            "LIMIT :limit"
        )
        result = await self.db.execute(vector_query, {"query_vec": vec_str, "limit": limit})
        rows = result.fetchall()

        program_ids = [row[0] for row in rows]
        if not program_ids:
            return []

        programs_result = await self.db.execute(
            select(Program)
            .where(Program.id.in_(program_ids))
            .options(selectinload(Program.institution))
        )
        programs = {program.id: program for program in programs_result.scalars().all()}

        ordered: list[ProgramSummaryResponse] = []
        for program_id, _similarity in rows:
            program = programs.get(program_id)
            if not program:
                continue
            ordered.append(
                ProgramSummaryResponse(
                    id=program.id,
                    institution_id=program.institution_id,
                    program_name=program.program_name,
                    degree_type=program.degree_type,
                    department=program.department,
                    tuition=program.tuition,
                    application_deadline=program.application_deadline,
                    institution_name=program.institution.name if program.institution else "",
                    institution_country=program.institution.country if program.institution else "",
                )
            )
        return ordered

    # --- Helpers ---

    async def _get_institution_for_user(self, user_id: UUID) -> Institution:
        result = await self.db.execute(
            select(Institution).where(Institution.admin_user_id == user_id)
        )
        institution = result.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution not found")
        return institution

    async def _verify_program_ownership(self, institution_id: UUID, program_id: UUID) -> Program:
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
            select(func.count())
            .select_from(Program)
            .where(
                Program.institution_id == institution_id,
                Program.is_published.is_(True),
            )
        )
        return result.scalar_one()
