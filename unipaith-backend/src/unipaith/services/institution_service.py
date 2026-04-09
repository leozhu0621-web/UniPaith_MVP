from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from unipaith.ai.jobs import on_program_updated
from unipaith.config import settings
from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from unipaith.models.application import Application, OfferLetter
from unipaith.models.engagement import Conversation, Message, StudentEngagementSignal
from unipaith.models.institution import (
    Campaign,
    CampaignRecipient,
    Event,
    EventRSVP,
    Institution,
    InstitutionDataset,
    InstitutionPost,
    Program,
    TargetSegment,
)
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.workflow import Notification
from unipaith.schemas.institution import (
    AnalyticsResponse,
    CampaignAttribution,
    CampaignMetricsResponse,
    CreateCampaignRequest,
    CreateDatasetRequest,
    CreateInstitutionRequest,
    CreatePostRequest,
    CreateProgramRequest,
    CreateSegmentRequest,
    DashboardSummaryResponse,
    DatasetPreviewResponse,
    DatasetResponse,
    DatasetUploadResponse,
    EventAttribution,
    FunnelStage,
    MonthlyApplicationCount,
    PaginatedResponse,
    PostMediaUploadResponse,
    PostResponse,
    ProgramApplicationCount,
    ProgramSummaryResponse,
    UpdateCampaignRequest,
    UpdateDatasetRequest,
    UpdateInstitutionRequest,
    UpdatePostRequest,
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
        """Execute segment criteria and return matching student IDs.

        Supported criteria keys (all AND-combined):
            statuses        - string[]  : Application.status IN values
            decisions       - string[]  : Application.decision IN values
            min_match_score - number    : MatchResult.match_score >= value/100
            max_match_score - number    : MatchResult.match_score <= value/100
            match_tiers     - number[]  : MatchResult.match_tier IN values
            min_engagement_signals - number : COUNT(StudentEngagementSignal) >= value
            engagement_types - string[] : StudentEngagementSignal.signal_type IN values
            nationalities   - string[]  : StudentProfile.nationality IN values
            has_applied     - boolean   : EXISTS / NOT EXISTS Application
            applied_after   - string    : Application.submitted_at >= ISO date
        """
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

        # Track whether any criteria key was actually specified
        has_criteria = False

        stmt = select(StudentProfile.id).distinct()

        # --- Application-based criteria (statuses, decisions, applied_after) ---
        statuses = criteria.get("statuses")
        decisions = criteria.get("decisions")
        applied_after = criteria.get("applied_after")
        has_applied = criteria.get("has_applied")

        need_app_join = bool(statuses or decisions or applied_after or (has_applied is True))

        if need_app_join:
            has_criteria = True
            app_conditions = [
                Application.program_id.in_(program_ids),
            ]
            if statuses:
                app_conditions.append(Application.status.in_(statuses))
            if decisions:
                app_conditions.append(Application.decision.in_(decisions))
            if applied_after:
                app_conditions.append(
                    Application.submitted_at >= datetime.fromisoformat(applied_after)
                )
            stmt = stmt.join(
                Application, Application.student_id == StudentProfile.user_id
            ).where(*app_conditions)
        elif has_applied is False:
            # Exclude students who have any application for these programs
            has_criteria = True
            app_exists = (
                select(Application.id)
                .where(
                    Application.student_id == StudentProfile.user_id,
                    Application.program_id.in_(program_ids),
                )
                .correlate(StudentProfile)
                .exists()
            )
            stmt = stmt.where(~app_exists)

        # --- Match-based criteria (min/max score, tiers) ---
        min_match_score = criteria.get("min_match_score")
        max_match_score = criteria.get("max_match_score")
        match_tiers = criteria.get("match_tiers")

        if min_match_score is not None or max_match_score is not None or match_tiers:
            has_criteria = True
            match_conditions = [
                MatchResult.program_id.in_(program_ids),
                MatchResult.is_stale.is_(False),
            ]
            if min_match_score is not None:
                match_conditions.append(
                    MatchResult.match_score >= min_match_score / 100
                )
            if max_match_score is not None:
                match_conditions.append(
                    MatchResult.match_score <= max_match_score / 100
                )
            if match_tiers:
                match_conditions.append(MatchResult.match_tier.in_(match_tiers))

            stmt = stmt.outerjoin(
                MatchResult, MatchResult.student_id == StudentProfile.id
            ).where(*match_conditions)

        # --- Engagement criteria (min count, signal types) ---
        min_engagement = criteria.get("min_engagement_signals")
        engagement_types = criteria.get("engagement_types")

        if min_engagement is not None or engagement_types:
            has_criteria = True
            eng_conditions = [
                StudentEngagementSignal.student_id == StudentProfile.id,
                StudentEngagementSignal.program_id.in_(program_ids),
            ]
            if engagement_types:
                eng_conditions.append(
                    StudentEngagementSignal.signal_type.in_(engagement_types)
                )
            eng_subq = (
                select(StudentEngagementSignal.student_id)
                .where(*eng_conditions)
                .correlate(StudentProfile)
                .group_by(StudentEngagementSignal.student_id)
            )
            if min_engagement is not None:
                eng_subq = eng_subq.having(func.count() >= min_engagement)
            stmt = stmt.where(
                StudentProfile.id.in_(eng_subq)
            )

        # --- Nationality filter ---
        nationalities = criteria.get("nationalities")
        if nationalities:
            has_criteria = True
            stmt = stmt.where(StudentProfile.nationality.in_(nationalities))

        # --- Fallback: if NO criteria at all, return all non-draft applicants ---
        if not has_criteria:
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

        # --- Funnel: cumulative stage counting ---
        stage_order = [
            "submitted", "under_review", "interview", "decision_made",
        ]
        funnel: list[FunnelStage] = []
        prev_count = total_apps
        for stage in stage_order:
            stage_count = apps_by_status.get(stage, 0)
            rate = (
                stage_count / prev_count
                if prev_count > 0 and funnel
                else None
            )
            funnel.append(FunnelStage(
                stage=stage,
                count=stage_count,
                conversion_rate=rate,
            ))
            if stage_count > 0:
                prev_count = stage_count

        # --- Campaign attribution ---
        campaign_attr: list[CampaignAttribution] = []
        sent_campaigns = await self.db.execute(
            select(Campaign).where(
                Campaign.institution_id == institution_id,
                Campaign.status == "sent",
            )
        )
        for camp in sent_campaigns.scalars().all():
            metrics = await self.db.execute(
                select(
                    func.count().label("total"),
                    func.count().filter(
                        CampaignRecipient.delivered_at.isnot(None),
                    ).label("delivered"),
                    func.count().filter(
                        CampaignRecipient.opened_at.isnot(None),
                    ).label("opened"),
                    func.count().filter(
                        CampaignRecipient.clicked_at.isnot(None),
                    ).label("clicked"),
                ).where(CampaignRecipient.campaign_id == camp.id)
            )
            m = metrics.one()
            # Count recipients who also applied
            app_count = await self.db.scalar(
                select(func.count(Application.id.distinct()))
                .select_from(Application)
                .join(
                    CampaignRecipient,
                    CampaignRecipient.student_id
                    == Application.student_id,
                )
                .where(
                    CampaignRecipient.campaign_id == camp.id,
                    Application.status != "draft",
                )
            ) or 0
            campaign_attr.append(CampaignAttribution(
                campaign_id=camp.id,
                campaign_name=camp.campaign_name,
                recipients=m.total,
                delivered=m.delivered,
                opened=m.opened,
                clicked=m.clicked,
                applications_started=app_count,
            ))

        # --- Event attribution ---
        event_attr: list[EventAttribution] = []
        events = await self.db.execute(
            select(Event).where(
                Event.institution_id == institution_id,
            )
        )
        for evt in events.scalars().all():
            rsvp_count = await self.db.scalar(
                select(func.count()).select_from(EventRSVP).where(
                    EventRSVP.event_id == evt.id,
                )
            ) or 0
            attended_count = await self.db.scalar(
                select(func.count()).select_from(EventRSVP).where(
                    EventRSVP.event_id == evt.id,
                    EventRSVP.attended_at.isnot(None),
                )
            ) or 0
            apps_after = await self.db.scalar(
                select(func.count(Application.id.distinct()))
                .select_from(Application)
                .join(
                    EventRSVP,
                    EventRSVP.student_id == Application.student_id,
                )
                .where(
                    EventRSVP.event_id == evt.id,
                    Application.status != "draft",
                )
            ) or 0
            event_attr.append(EventAttribution(
                event_id=evt.id,
                event_name=evt.event_name,
                rsvps=rsvp_count,
                attended=attended_count,
                applications_after=apps_after,
            ))

        return AnalyticsResponse(
            total_applications=total_apps,
            acceptance_rate=acceptance_rate,
            avg_match_score=avg_match_score,
            yield_rate=yield_rate,
            apps_by_status=apps_by_status,
            apps_by_program=apps_by_program,
            apps_by_month=apps_by_month,
            decisions_breakdown=decisions_breakdown,
            funnel_stages=funnel,
            campaign_attribution=campaign_attr,
            event_attribution=event_attr,
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

    # --- Datasets ---

    async def list_datasets(self, institution_id: UUID) -> list[InstitutionDataset]:
        result = await self.db.execute(
            select(InstitutionDataset)
            .where(InstitutionDataset.institution_id == institution_id)
            .order_by(InstitutionDataset.created_at.desc())
        )
        return list(result.scalars().all())

    async def request_dataset_upload(
        self, institution_id: UUID, user_id: UUID, data: CreateDatasetRequest,
    ) -> DatasetUploadResponse:
        from unipaith.core.s3 import S3Client

        s3_key = f"datasets/{institution_id}/{uuid.uuid4()}/{data.file_name}"
        s3 = S3Client()
        upload_url = s3.generate_upload_url(s3_key, data.content_type)

        dataset = InstitutionDataset(
            institution_id=institution_id,
            dataset_name=data.dataset_name,
            dataset_type=data.dataset_type,
            description=data.description,
            s3_key=s3_key,
            file_name=data.file_name,
            file_size_bytes=data.file_size_bytes,
            usage_scope=data.usage_scope,
            status="pending",
            uploaded_by=user_id,
        )
        self.db.add(dataset)
        await self.db.flush()
        await self.db.refresh(dataset)
        return DatasetUploadResponse(dataset_id=dataset.id, upload_url=upload_url)

    async def confirm_dataset_upload(
        self, institution_id: UUID, dataset_id: UUID,
    ) -> InstitutionDataset:
        dataset = await self._verify_dataset_ownership(institution_id, dataset_id)
        dataset.status = "validated"
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset

    async def get_dataset(self, institution_id: UUID, dataset_id: UUID) -> DatasetResponse:
        dataset = await self._verify_dataset_ownership(institution_id, dataset_id)
        from unipaith.core.s3 import S3Client

        s3 = S3Client()
        download_url = s3.generate_download_url(dataset.s3_key)
        resp = DatasetResponse.model_validate(dataset)
        resp.download_url = download_url
        return resp

    async def get_dataset_preview(
        self, institution_id: UUID, dataset_id: UUID,
    ) -> DatasetPreviewResponse:
        dataset = await self._verify_dataset_ownership(institution_id, dataset_id)
        import csv
        import io

        # Read file from S3 (or local)
        if settings.s3_local_mode:
            from pathlib import Path

            local_path = Path(settings.s3_local_path) / dataset.s3_key
            if not local_path.exists():
                return DatasetPreviewResponse(columns=[], rows=[], total_rows=0)
            content = local_path.read_text(encoding="utf-8")
        else:
            import boto3

            client = boto3.client("s3", region_name=settings.aws_region)
            obj = client.get_object(Bucket=settings.s3_bucket_name, Key=dataset.s3_key)
            content = obj["Body"].read().decode("utf-8")

        reader = csv.DictReader(io.StringIO(content))
        columns = reader.fieldnames or []
        rows = []
        total = 0
        for row in reader:
            total += 1
            if len(rows) < 10:
                rows.append(dict(row))

        # Update row_count if not set
        if dataset.row_count is None:
            dataset.row_count = total
            await self.db.flush()

        return DatasetPreviewResponse(columns=list(columns), rows=rows, total_rows=total)

    async def update_dataset(
        self, institution_id: UUID, dataset_id: UUID, data: UpdateDatasetRequest,
    ) -> InstitutionDataset:
        dataset = await self._verify_dataset_ownership(institution_id, dataset_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dataset, key, value)
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset

    async def delete_dataset(self, institution_id: UUID, dataset_id: UUID) -> None:
        dataset = await self._verify_dataset_ownership(institution_id, dataset_id)
        from unipaith.core.s3 import S3Client

        S3Client().delete_object(dataset.s3_key)
        await self.db.delete(dataset)
        await self.db.flush()

    async def _verify_dataset_ownership(
        self, institution_id: UUID, dataset_id: UUID,
    ) -> InstitutionDataset:
        result = await self.db.execute(
            select(InstitutionDataset).where(
                InstitutionDataset.id == dataset_id,
                InstitutionDataset.institution_id == institution_id,
            )
        )
        dataset = result.scalar_one_or_none()
        if not dataset:
            raise NotFoundException("Dataset not found")
        return dataset

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

    # ------------------------------------------------------------------ #
    # Posts
    # ------------------------------------------------------------------ #

    async def list_posts(
        self, institution_id: UUID, include_drafts: bool = True,
    ) -> list[PostResponse]:
        q = (
            select(InstitutionPost)
            .where(InstitutionPost.institution_id == institution_id)
        )
        if not include_drafts:
            q = q.where(InstitutionPost.status == "published")
        q = q.order_by(
            InstitutionPost.pinned.desc(),
            InstitutionPost.published_at.desc().nulls_last(),
            InstitutionPost.created_at.desc(),
        )
        result = await self.db.execute(q)
        posts = list(result.scalars().all())
        return [await self._enrich_post(p) for p in posts]

    async def create_post(
        self, institution_id: UUID, user_id: UUID, data: CreatePostRequest,
    ) -> PostResponse:
        post = InstitutionPost(
            institution_id=institution_id,
            author_id=user_id,
            title=data.title,
            body=data.body,
            media_urls=(
                [m if isinstance(m, dict) else {"url": m} for m in data.media_urls]
                if data.media_urls else None
            ),
            tagged_program_ids=(
                [str(pid) for pid in data.tagged_program_ids]
                if data.tagged_program_ids else None
            ),
            tagged_intake=data.tagged_intake,
            status=data.status,
            scheduled_for=data.scheduled_for,
            is_template=data.is_template,
            template_name=data.template_name,
        )
        if data.status == "published":
            post.published_at = datetime.now(UTC)
        self.db.add(post)
        await self.db.flush()
        return await self._enrich_post(post)

    async def update_post(
        self,
        institution_id: UUID,
        post_id: UUID,
        data: UpdatePostRequest,
    ) -> PostResponse:
        post = await self._get_post(institution_id, post_id)
        update_data = data.model_dump(exclude_unset=True)
        if "tagged_program_ids" in update_data and update_data["tagged_program_ids"]:
            update_data["tagged_program_ids"] = [
                str(pid) for pid in update_data["tagged_program_ids"]
            ]
        was_published = post.status == "published"
        for key, value in update_data.items():
            setattr(post, key, value)
        if not was_published and post.status == "published":
            post.published_at = datetime.now(UTC)
        await self.db.flush()
        return await self._enrich_post(post)

    async def delete_post(
        self, institution_id: UUID, post_id: UUID,
    ) -> None:
        post = await self._get_post(institution_id, post_id)
        await self.db.delete(post)
        await self.db.flush()

    async def pin_post(
        self, institution_id: UUID, post_id: UUID,
    ) -> PostResponse:
        post = await self._get_post(institution_id, post_id)
        post.pinned = not post.pinned
        await self.db.flush()
        return await self._enrich_post(post)

    async def publish_post(
        self, institution_id: UUID, post_id: UUID,
    ) -> PostResponse:
        post = await self._get_post(institution_id, post_id)
        post.status = "published"
        post.published_at = datetime.now(UTC)
        await self.db.flush()
        return await self._enrich_post(post)

    async def request_post_media_upload(
        self, institution_id: UUID, content_type: str,
    ) -> PostMediaUploadResponse:
        from unipaith.core.s3 import S3Client
        s3 = S3Client()
        key = f"institutions/{institution_id}/posts/media/{uuid.uuid4()}"
        upload_url = s3.generate_upload_url(key, content_type)
        return PostMediaUploadResponse(upload_url=upload_url, media_key=key)

    async def list_post_templates(
        self, institution_id: UUID,
    ) -> list[PostResponse]:
        result = await self.db.execute(
            select(InstitutionPost).where(
                InstitutionPost.institution_id == institution_id,
                InstitutionPost.is_template.is_(True),
            ).order_by(InstitutionPost.created_at.desc())
        )
        posts = list(result.scalars().all())
        return [await self._enrich_post(p) for p in posts]

    async def get_public_posts(
        self, institution_id: UUID,
    ) -> list[PostResponse]:
        result = await self.db.execute(
            select(InstitutionPost).where(
                InstitutionPost.institution_id == institution_id,
                InstitutionPost.status == "published",
            ).order_by(
                InstitutionPost.pinned.desc(),
                InstitutionPost.published_at.desc().nulls_last(),
            )
        )
        posts = list(result.scalars().all())
        return [await self._enrich_post(p) for p in posts]

    async def _get_post(
        self, institution_id: UUID, post_id: UUID,
    ) -> InstitutionPost:
        result = await self.db.execute(
            select(InstitutionPost).where(
                InstitutionPost.id == post_id,
                InstitutionPost.institution_id == institution_id,
            )
        )
        post = result.scalar_one_or_none()
        if not post:
            raise NotFoundException("Post not found")
        return post

    async def _enrich_post(self, post: InstitutionPost) -> PostResponse:
        from unipaith.models.user import User
        author_email: str | None = None
        if post.author_id:
            user_r = await self.db.execute(
                select(User.email).where(User.id == post.author_id)
            )
            author_email = user_r.scalar_one_or_none()

        program_names: list[str] | None = None
        tag_ids = post.tagged_program_ids
        if tag_ids and isinstance(tag_ids, list) and len(tag_ids) > 0:
            prog_r = await self.db.execute(
                select(Program.program_name).where(
                    Program.id.in_(tag_ids)
                )
            )
            program_names = list(prog_r.scalars().all())

        return PostResponse(
            id=post.id,
            institution_id=post.institution_id,
            author_id=post.author_id,
            title=post.title,
            body=post.body,
            media_urls=post.media_urls,
            pinned=post.pinned,
            tagged_program_ids=post.tagged_program_ids,
            tagged_intake=post.tagged_intake,
            status=post.status,
            scheduled_for=post.scheduled_for,
            published_at=post.published_at,
            is_template=post.is_template,
            template_name=post.template_name,
            view_count=post.view_count,
            created_at=post.created_at,
            updated_at=post.updated_at,
            author_email=author_email,
            program_names=program_names,
        )
