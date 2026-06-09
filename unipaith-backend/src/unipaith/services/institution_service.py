from __future__ import annotations

import json
import logging
import math
import re
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import case, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
    UnprocessableEntityException,
)
from unipaith.core.media_urls import resolve_media_urls
from unipaith.models.application import (
    Application,
    IntegritySignal,
    Interview,
    OfferLetter,
    ReviewAssignment,
)
from unipaith.models.engagement import Conversation, Message, StudentEngagementSignal
from unipaith.models.institution import (
    Campaign,
    CampaignAction,
    CampaignLink,
    CampaignRecipient,
    Event,
    EventRSVP,
    Inquiry,
    Institution,
    InstitutionDataset,
    InstitutionPost,
    IntakeRound,
    Program,
    Promotion,
    School,
    TargetSegment,
)
from unipaith.models.matching import MatchResult
from unipaith.models.outcomes import ProgramOutcome
from unipaith.models.settings import InstitutionTeamInvite
from unipaith.models.student import StudentProfile
from unipaith.models.workflow import Notification
from unipaith.schemas.institution import (
    AnalyticsResponse,
    CampaignAttribution,
    CampaignAttributionDetail,
    CampaignLinkResponse,
    CreateCampaignLinkRequest,
    CreateDatasetRequest,
    CreateInstitutionRequest,
    CreatePostRequest,
    CreateProgramRequest,
    CreatePromotionRequest,
    CreateSegmentRequest,
    DashboardSummaryResponse,
    DatasetPreviewResponse,
    DatasetReplaceRequest,
    DatasetResponse,
    DatasetUploadResponse,
    EventAttribution,
    FunnelStage,
    InquiryResponse,
    LinkPerformance,
    MonthlyApplicationCount,
    NLPSearchResponse,
    PaginatedResponse,
    PostMediaUploadResponse,
    PostResponse,
    PriorityQueueItem,
    ProgramApplicationCount,
    ProgramSummaryResponse,
    PromotionResponse,
    SubmitInquiryRequest,
    UpdateDatasetRequest,
    UpdateInquiryRequest,
    UpdateInstitutionRequest,
    UpdatePostRequest,
    UpdateProgramRequest,
    UpdatePromotionRequest,
    UpdateSegmentRequest,
)

logger = logging.getLogger(__name__)


def _escape_like(value: str) -> str:
    """Escape SQL LIKE wildcard characters in user input."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _outcomes_int(prog: Program, key: str) -> int | None:
    """Extract an int from outcomes_data JSONB. Handles dict, JSON string, and None cases."""
    data = prog.outcomes_data
    if data is None:
        return None
    # JSONB sometimes deserializes as a string — handle that
    if isinstance(data, str):
        try:
            import json as _json

            data = _json.loads(data)
        except (ValueError, TypeError):
            return None
    if not isinstance(data, dict):
        return None
    val = data.get(key)
    if val is None:
        return None
    try:
        return int(float(val))  # float first so "137804.0" and 137804.0 both work
    except (ValueError, TypeError):
        return None


def _outcomes_float(prog: Program, key: str) -> float | None:
    """Extract a float from outcomes_data JSONB."""
    data = prog.outcomes_data
    if data is None:
        return None
    if isinstance(data, str):
        try:
            import json as _json

            data = _json.loads(data)
        except (ValueError, TypeError):
            return None
    if not isinstance(data, dict):
        return None
    val = data.get(key)
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# Spec 68 §6/§7 — the Featured filters/sorts read the typed `program_outcomes`
# table (authority-resolved) instead of the JSONB blob, with a legacy fallback
# during cutover. Legacy keys map onto the typed metric enum:
#   median_salary / earnings_*_median → salary_median
#   employment_rate                   → employment_rate
#   payback_months                    → payback_period_months
def _resolved_metric_subq(metric: str):
    """Authority-resolved typed ``value_numeric`` for one (program, metric),
    correlated to the outer ``Program`` row (Spec 68 §7: reported > licensed >
    crawled, then newest window)."""
    auth = case(
        (ProgramOutcome.source == "reported", 3),
        (ProgramOutcome.source == "licensed", 2),
        else_=1,
    )
    return (
        select(ProgramOutcome.value_numeric)
        .where(
            ProgramOutcome.program_id == Program.id,
            ProgramOutcome.metric == metric,
        )
        .order_by(
            auth.desc(),
            ProgramOutcome.reference_period.desc(),
            ProgramOutcome.updated_at.desc(),
        )
        .limit(1)
        .correlate(Program)
        .scalar_subquery()
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
        accreditation = update_data.pop("accreditation", None)
        if accreditation is not None:
            rd = dict(institution.ranking_data or {})
            trimmed = accreditation.strip()
            if trimmed:
                rd["accreditor"] = trimmed
            else:
                rd.pop("accreditor", None)
            institution.ranking_data = rd or None
        for key, value in update_data.items():
            setattr(institution, key, value)
        await self.db.flush()
        await self.db.refresh(institution)
        return institution

    # --- Setup wizard (Spec 30) ---

    _SETUP_STEP_NUM = {"profile": 1, "program": 2, "data": 3, "team": 4}

    async def _maybe_institution_for_user(self, user_id: UUID) -> Institution | None:
        """Like `_get_institution_for_user` but returns None instead of raising —
        the setup wizard's GET must work before the institution row exists."""
        result = await self.db.execute(
            select(Institution).where(Institution.admin_user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def _setup_signals(self, institution: Institution) -> dict:
        """Real-data signals backing each wizard step's completion (Spec 30 §5)."""
        prog_row = (
            await self.db.execute(
                select(
                    func.count().label("total"),
                    func.count().filter(Program.is_published.is_(True)).label("published"),
                ).where(Program.institution_id == institution.id)
            )
        ).one()
        first_program_id = (
            await self.db.execute(
                select(Program.id)
                .where(Program.institution_id == institution.id)
                .order_by(Program.created_at.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
        dataset_count = await self.db.scalar(
            select(func.count())
            .select_from(InstitutionDataset)
            .where(InstitutionDataset.institution_id == institution.id)
        )
        invite_count = await self.db.scalar(
            select(func.count())
            .select_from(InstitutionTeamInvite)
            .where(InstitutionTeamInvite.institution_id == institution.id)
        )
        has_profile = bool(
            institution.name
            and institution.type
            and institution.country
            and (institution.description_text or "").strip()
        )
        return {
            "program_count": int(prog_row.total or 0),
            "published_count": int(prog_row.published or 0),
            "first_program_id": str(first_program_id) if first_program_id else None,
            "dataset_count": int(dataset_count or 0),
            "invite_count": int(invite_count or 0),
            "has_profile": has_profile,
        }

    def _build_setup_view(self, institution: Institution, signals: dict) -> dict:
        """Merge stored wizard progress with real-data signals into the response
        shape. A step counts complete if the real data exists OR it was explicitly
        flagged/skipped — so a profile filled via Settings still satisfies setup."""
        stored = dict(institution.setup_state or {})
        stored_steps = dict(stored.get("steps_complete") or {})
        skipped = dict(stored.get("skipped") or {})
        steps_complete = {
            "profile": bool(signals["has_profile"]) or bool(stored_steps.get("profile")),
            "program": signals["program_count"] >= 1 or bool(stored_steps.get("program")),
            "data": (
                signals["dataset_count"] >= 1
                or bool(skipped.get("data"))
                or bool(stored_steps.get("data"))
            ),
            "team": (
                signals["invite_count"] >= 1
                or bool(skipped.get("team"))
                or bool(stored_steps.get("team"))
            ),
        }
        if institution.setup_complete:
            current: int | str = "done"
        else:
            # Resume on the step the user last navigated to (persisted via PATCH);
            # fall back to the first incomplete step for a fresh wizard.
            stored_step = stored.get("step")
            if isinstance(stored_step, int) and 1 <= stored_step <= 4:
                current = stored_step
            else:
                current = "done"
                for name in ("profile", "program", "data", "team"):
                    if not steps_complete[name]:
                        current = self._SETUP_STEP_NUM[name]
                        break
        return {
            "institution_id": str(institution.id),
            "step": current,
            "steps_complete": steps_complete,
            "skipped": {"data": bool(skipped.get("data")), "team": bool(skipped.get("team"))},
            "first_program_id": signals["first_program_id"],
            "setup_complete": bool(institution.setup_complete),
            "published_program_count": signals["published_count"],
        }

    async def get_setup_state(self, user_id: UUID) -> dict:
        institution = await self._maybe_institution_for_user(user_id)
        if institution is None:
            return {
                "institution_id": None,
                "step": 1,
                "steps_complete": {
                    "profile": False,
                    "program": False,
                    "data": False,
                    "team": False,
                },
                "skipped": {"data": False, "team": False},
                "first_program_id": None,
                "setup_complete": False,
                "published_program_count": 0,
            }
        signals = await self._setup_signals(institution)
        return self._build_setup_view(institution, signals)

    async def patch_setup_step(
        self,
        user_id: UUID,
        *,
        step: int | None = None,
        skip_data: bool | None = None,
        skip_team: bool | None = None,
        mark_complete: dict[str, bool] | None = None,
    ) -> dict:
        institution = await self._get_institution_for_user(user_id)
        # Rebuild as a new dict so SQLAlchemy detects the JSONB change.
        state = dict(institution.setup_state or {})
        skipped = dict(state.get("skipped") or {})
        sc = dict(state.get("steps_complete") or {})
        if step is not None:
            if step not in (1, 2, 3, 4):
                raise BadRequestException("step must be between 1 and 4")
            state["step"] = step
        if skip_data is not None:
            skipped["data"] = bool(skip_data)
        if skip_team is not None:
            skipped["team"] = bool(skip_team)
        if mark_complete:
            for key, value in mark_complete.items():
                if key in ("profile", "program", "data", "team"):
                    sc[key] = bool(value)
        state["skipped"] = skipped
        state["steps_complete"] = sc
        institution.setup_state = state
        await self.db.flush()
        await self.db.refresh(institution)
        signals = await self._setup_signals(institution)
        return self._build_setup_view(institution, signals)

    async def complete_setup(self, user_id: UUID) -> dict:
        institution = await self._get_institution_for_user(user_id)
        signals = await self._setup_signals(institution)
        view = self._build_setup_view(institution, signals)
        # Spec 30 §4 — minimum to finish: profile + one program.
        if not (view["steps_complete"]["profile"] and view["steps_complete"]["program"]):
            raise BadRequestException(
                "Add your institution profile and a first program before finishing setup"
            )
        institution.setup_complete = True
        state = dict(institution.setup_state or {})
        state["step"] = "done"
        institution.setup_state = state
        await self.db.flush()
        await self.db.refresh(institution)
        signals = await self._setup_signals(institution)
        return self._build_setup_view(institution, signals)

    # --- Programs ---

    async def list_programs(self, institution_id: UUID) -> list[Program]:
        result = await self.db.execute(
            select(Program).where(Program.institution_id == institution_id)
        )
        return list(result.scalars().all())

    async def get_program(self, institution_id: UUID, program_id: UUID) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        # Spec 23 §12 — blast-radius: how many applications reference this program.
        program.applications_count = await self._program_application_count(program_id)
        return program

    async def _program_application_count(self, program_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .where(Application.program_id == program_id)
        )
        return int(result.scalar_one() or 0)

    async def _verify_school_in_institution(self, institution_id: UUID, school_id: UUID) -> None:
        """A program's school (sub-institution) must belong to the same
        institution — guards against assigning another org's school."""
        result = await self.db.execute(
            select(School.id).where(
                School.id == school_id,
                School.institution_id == institution_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise BadRequestException("Selected school does not belong to this institution")

    async def create_program(self, institution_id: UUID, data: CreateProgramRequest) -> Program:
        if data.school_id is not None:
            await self._verify_school_in_institution(institution_id, data.school_id)
        program = Program(
            institution_id=institution_id,
            is_published=False,
            **data.model_dump(),
        )
        self.db.add(program)
        await self.db.flush()
        # AI feature extraction skipped (engine being rebuilt)
        await self.db.refresh(program)
        program.applications_count = 0
        return program

    async def update_program(
        self, institution_id: UUID, program_id: UUID, data: UpdateProgramRequest
    ) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        update_data = data.model_dump(exclude_unset=True)
        # Spec 23 §6 — optimistic lock. `expected_version` is a control field,
        # not a column: pull it out before applying fields to the model.
        expected_version = update_data.pop("expected_version", None)
        if expected_version is not None and int(program.feature_version) != int(expected_version):
            raise ConflictException("Someone else edited this. Reload to see their changes?")
        if update_data.get("school_id") is not None:
            await self._verify_school_in_institution(institution_id, update_data["school_id"])
        for key, value in update_data.items():
            setattr(program, key, value)
        if update_data:
            # Spec 06 §5.4 — bump the program version so the rationale cache
            # (keyed by program_version) invalidates on next read. Previously
            # the column didn't exist and this was a dead no-op.
            program.feature_version = int(getattr(program, "feature_version", 1) or 1) + 1
        await self.db.flush()
        await self.db.refresh(program)
        program.applications_count = await self._program_application_count(program_id)
        return program

    # Spec 23 §4/§6 — fields required before a program can be published, mapped
    # to the editor section that owns each one so the validation modal can
    # scroll the institution straight to the fix.
    def _publish_validation_errors(self, program: Program) -> list[dict]:
        missing: list[dict] = []
        if not program.program_name:
            missing.append(
                {
                    "field": "program_name",
                    "section": "identity",
                    "message": "Program name is required.",
                }
            )
        if not program.degree_type:
            missing.append(
                {
                    "field": "degree_type",
                    "section": "identity",
                    "message": "Degree type is required.",
                }
            )
        if not program.description_text:
            missing.append(
                {
                    "field": "description_text",
                    "section": "overview",
                    "message": "A program description is required.",
                }
            )
        has_cost_signal = (
            program.tuition is not None
            or program.application_deadline is not None
            or bool(program.cost_data)
            or bool(program.intake_rounds)
        )
        if not has_cost_signal:
            missing.append(
                {
                    "field": "cost_data",
                    "section": "costs",
                    "message": "Add tuition, a deadline, or cost details before publishing.",
                }
            )
        return missing

    async def publish_program(self, institution_id: UUID, program_id: UUID) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        missing = self._publish_validation_errors(program)
        if missing:
            raise UnprocessableEntityException(
                {
                    "message": "This program is missing required fields. Resolve to publish.",
                    "missing_fields": missing,
                }
            )
        program.is_published = True
        await self.db.flush()
        # AI feature extraction skipped (engine being rebuilt)
        await self.db.refresh(program)
        program.applications_count = await self._program_application_count(program_id)
        return program

    async def unpublish_program(self, institution_id: UUID, program_id: UUID) -> Program:
        program = await self._verify_program_ownership(institution_id, program_id)
        program.is_published = False
        await self.db.flush()
        # AI feature extraction skipped (engine being rebuilt)
        await self.db.refresh(program)
        program.applications_count = await self._program_application_count(program_id)
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
        self, institution_id: UUID, data: CreateSegmentRequest, created_by: UUID | None = None
    ) -> TargetSegment:
        segment = TargetSegment(
            institution_id=institution_id, created_by_user_id=created_by, **data.model_dump()
        )
        self.db.add(segment)
        await self.db.flush()
        await self.db.refresh(segment)
        return segment

    async def get_segment(self, institution_id: UUID, segment_id: UUID) -> TargetSegment:
        result = await self.db.execute(
            select(TargetSegment).where(
                TargetSegment.id == segment_id,
                TargetSegment.institution_id == institution_id,
            )
        )
        segment = result.scalar_one_or_none()
        if not segment:
            raise NotFoundException("Segment not found")
        return segment

    async def cache_segment_preview(
        self, institution_id: UUID, segment_id: UUID, count: int
    ) -> None:
        """Spec 26 §7 — persist the last preview audience size on the segment."""
        segment = await self.get_segment(institution_id, segment_id)
        segment.preview_audience_count = count
        segment.preview_generated_at = datetime.now(UTC)
        await self.db.flush()

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
        self,
        institution_id: UUID,
        segment_id: UUID,
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

        # Spec 26 — when the segment carries a nested rule tree, evaluate it via
        # the SegmentService engine (with outreach suppression) and return that.
        # Older segments with only flat `criteria` fall through to the legacy
        # AND-combined path below, keeping existing campaign wiring intact.
        if segment.rules:
            from unipaith.services.segment_service import SegmentService

            seg_svc = SegmentService(self.db)
            members = await seg_svc.evaluate_rules(
                institution_id, segment.rules, segment.program_id
            )
            members = await seg_svc.apply_suppression(members)
            return list(members)

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
            stmt = stmt.join(Application, Application.student_id == StudentProfile.id).where(
                *app_conditions
            )
        elif has_applied is False:
            # Exclude students who have any application for these programs
            has_criteria = True
            app_exists = (
                select(Application.id)
                .where(
                    Application.student_id == StudentProfile.id,
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
                match_conditions.append(MatchResult.match_score >= min_match_score / 100)
            if max_match_score is not None:
                match_conditions.append(MatchResult.match_score <= max_match_score / 100)
            if match_tiers:
                match_conditions.append(MatchResult.match_tier.in_(match_tiers))

            stmt = stmt.outerjoin(MatchResult, MatchResult.student_id == StudentProfile.id).where(
                *match_conditions
            )

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
                eng_conditions.append(StudentEngagementSignal.signal_type.in_(engagement_types))
            eng_subq = (
                select(StudentEngagementSignal.student_id)
                .where(*eng_conditions)
                .correlate(StudentProfile)
                .group_by(StudentEngagementSignal.student_id)
            )
            if min_engagement is not None:
                eng_subq = eng_subq.having(func.count() >= min_engagement)
            stmt = stmt.where(StudentProfile.id.in_(eng_subq))

        # --- Nationality filter ---
        nationalities = criteria.get("nationalities")
        if nationalities:
            has_criteria = True
            stmt = stmt.where(StudentProfile.nationality.in_(nationalities))

        # --- Fallback: if NO criteria at all, return all non-draft applicants ---
        if not has_criteria:
            stmt = stmt.join(Application, Application.student_id == StudentProfile.id).where(
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

        # --- Spec 31 · Admissions Intake contract (§2 / §8) ---
        day_ago = now - timedelta(days=1)
        four_h_ago = now - timedelta(hours=4)

        # Avg match (fitness) across the institution's applicant pool, 0–100.
        avg_fit_val = (
            await self.db.execute(
                select(func.avg(MatchResult.fitness_score))
                .select_from(MatchResult)
                .join(Program, MatchResult.program_id == Program.id)
                .where(Program.institution_id == institution_id)
            )
        ).scalar_one_or_none()
        avg_match = round(float(avg_fit_val) * 100) if avg_fit_val is not None else None

        # New inquiries (24h) + those still unanswered after 4h (§2 "3 unanswered ≥ 4h").
        new_inquiries_24h = (
            await self.db.execute(
                select(func.count())
                .select_from(Inquiry)
                .where(
                    Inquiry.institution_id == institution_id,
                    Inquiry.created_at >= day_ago,
                )
            )
        ).scalar_one() or 0
        unanswered_inquiries_4h = (
            await self.db.execute(
                select(func.count())
                .select_from(Inquiry)
                .where(
                    Inquiry.institution_id == institution_id,
                    Inquiry.status.in_(("new", "in_progress")),
                    Inquiry.created_at <= four_h_ago,
                )
            )
        ).scalar_one() or 0

        # Categorized priority queue (§2), each with a deep link.
        needs_assign = (
            await self.db.execute(
                select(func.count(func.distinct(Application.id)))
                .select_from(Application)
                .join(Program, Application.program_id == Program.id)
                .outerjoin(ReviewAssignment, ReviewAssignment.application_id == Application.id)
                .where(
                    Program.institution_id == institution_id,
                    Application.status.in_(("submitted", "under_review")),
                    Application.decision.is_(None),
                    ReviewAssignment.id.is_(None),
                )
            )
        ).scalar_one() or 0
        integrity_apps = (
            await self.db.execute(
                select(func.count(func.distinct(IntegritySignal.application_id))).where(
                    IntegritySignal.institution_id == institution_id,
                    IntegritySignal.status == "open",
                )
            )
        ).scalar_one() or 0
        integrity_signals_count = (
            await self.db.execute(
                select(func.count())
                .select_from(IntegritySignal)
                .where(
                    IntegritySignal.institution_id == institution_id,
                    IntegritySignal.status == "open",
                )
            )
        ).scalar_one() or 0
        interviews_pending = (
            await self.db.execute(
                select(func.count())
                .select_from(Interview)
                .join(Application, Interview.application_id == Application.id)
                .join(Program, Application.program_id == Program.id)
                .where(
                    Program.institution_id == institution_id,
                    Interview.confirmed_time.is_(None),
                    or_(
                        Interview.status.is_(None),
                        Interview.status.not_in(("completed", "cancelled", "declined")),
                    ),
                )
            )
        ).scalar_one() or 0

        priority_queue: list[PriorityQueueItem] = []
        if needs_assign:
            priority_queue.append(
                PriorityQueueItem(
                    category=(
                        f"{needs_assign} application"
                        f"{'s' if needs_assign != 1 else ''} need reviewer assignment"
                    ),
                    count=int(needs_assign),
                    deep_link="/i/admissions?tab=pipeline",
                )
            )
        if integrity_apps:
            priority_queue.append(
                PriorityQueueItem(
                    category=(
                        f"{integrity_apps} application"
                        f"{'s' if integrity_apps != 1 else ''} with integrity flags"
                    ),
                    count=int(integrity_apps),
                    deep_link="/i/admissions?tab=integrity",
                )
            )
        if interviews_pending:
            priority_queue.append(
                PriorityQueueItem(
                    category=(
                        f"{interviews_pending} interview confirmation"
                        f"{'s' if interviews_pending != 1 else ''} pending"
                    ),
                    count=int(interviews_pending),
                    deep_link="/i/admissions?tab=interviews",
                )
            )

        cycle = await self._derive_cycle(institution_id)
        try:
            from unipaith.services.dashboard_intelligence_service import (
                DashboardIntelligenceService,
            )

            fairness = await DashboardIntelligenceService(self.db).fairness_signal(institution_id)
        except Exception:  # noqa: BLE001 — fairness is advisory; never block the dashboard
            logger.exception("fairness signal failed; omitting")
            fairness = None

        return DashboardSummaryResponse(
            program_count=prog_row.total,
            published_program_count=prog_row.published,
            total_applications=total_apps,
            pending_review_count=pending_review,
            active_events_count=active_events,
            unread_messages_count=unread_messages,
            acceptance_rate=acceptance_rate,
            yield_rate=yield_rate,
            cycle=cycle,
            avg_match=avg_match,
            conversion_pct=acceptance_rate,
            projected_yield_pct=yield_rate,
            new_inquiries_24h=int(new_inquiries_24h),
            unanswered_inquiries_4h=int(unanswered_inquiries_4h),
            integrity_signals_count=int(integrity_signals_count),
            priority_queue=priority_queue,
            fairness=fairness,
        )

    async def _derive_cycle(self, institution_id: UUID) -> str | None:
        """Derive an admissions-cycle label (e.g. "Fall 2027"). Prefers the
        dominant active intake term; else the soonest upcoming program start;
        else next fall. Best-effort — never raises."""
        try:
            row = (
                await self.db.execute(
                    select(IntakeRound.intake_term, func.count().label("n"))
                    .join(Program, IntakeRound.program_id == Program.id)
                    .where(
                        Program.institution_id == institution_id,
                        IntakeRound.intake_term.isnot(None),
                        IntakeRound.is_active.is_(True),
                    )
                    .group_by(IntakeRound.intake_term)
                    .order_by(func.count().desc())
                    .limit(1)
                )
            ).first()
            if row and row[0]:
                return str(row[0])

            today = datetime.now(UTC).date()
            start = (
                await self.db.execute(
                    select(Program.program_start_date)
                    .where(
                        Program.institution_id == institution_id,
                        Program.program_start_date.isnot(None),
                        Program.program_start_date >= today,
                    )
                    .order_by(Program.program_start_date.asc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if start:
                season = "Spring" if start.month <= 4 else "Summer" if start.month <= 8 else "Fall"
                return f"{season} {start.year}"
        except Exception:  # noqa: BLE001
            logger.exception("cycle derivation failed; using fallback")
        return f"Fall {datetime.now(UTC).year + 1}"

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
            "submitted",
            "under_review",
            "interview",
            "decision_made",
        ]
        funnel: list[FunnelStage] = []
        prev_count = total_apps
        for stage in stage_order:
            stage_count = apps_by_status.get(stage, 0)
            rate = stage_count / prev_count if prev_count > 0 and funnel else None
            funnel.append(
                FunnelStage(
                    stage=stage,
                    count=stage_count,
                    conversion_rate=rate,
                )
            )
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
                    func.count()
                    .filter(
                        CampaignRecipient.delivered_at.isnot(None),
                    )
                    .label("delivered"),
                    func.count()
                    .filter(
                        CampaignRecipient.opened_at.isnot(None),
                    )
                    .label("opened"),
                    func.count()
                    .filter(
                        CampaignRecipient.clicked_at.isnot(None),
                    )
                    .label("clicked"),
                ).where(CampaignRecipient.campaign_id == camp.id)
            )
            m = metrics.one()
            # Count recipients who also applied
            app_count = (
                await self.db.scalar(
                    select(func.count(Application.id.distinct()))
                    .select_from(Application)
                    .join(
                        CampaignRecipient,
                        CampaignRecipient.student_id == Application.student_id,
                    )
                    .where(
                        CampaignRecipient.campaign_id == camp.id,
                        Application.status != "draft",
                    )
                )
                or 0
            )
            campaign_attr.append(
                CampaignAttribution(
                    campaign_id=camp.id,
                    campaign_name=camp.campaign_name,
                    recipients=m.total,
                    delivered=m.delivered,
                    opened=m.opened,
                    clicked=m.clicked,
                    applications_started=app_count,
                )
            )

        # --- Event attribution ---
        event_attr: list[EventAttribution] = []
        events = await self.db.execute(
            select(Event).where(
                Event.institution_id == institution_id,
            )
        )
        for evt in events.scalars().all():
            rsvp_count = (
                await self.db.scalar(
                    select(func.count())
                    .select_from(EventRSVP)
                    .where(
                        EventRSVP.event_id == evt.id,
                    )
                )
                or 0
            )
            attended_count = (
                await self.db.scalar(
                    select(func.count())
                    .select_from(EventRSVP)
                    .where(
                        EventRSVP.event_id == evt.id,
                        EventRSVP.attended_at.isnot(None),
                    )
                )
                or 0
            )
            apps_after = (
                await self.db.scalar(
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
                )
                or 0
            )
            event_attr.append(
                EventAttribution(
                    event_id=evt.id,
                    event_name=evt.event_name,
                    rsvps=rsvp_count,
                    attended=attended_count,
                    applications_after=apps_after,
                )
            )

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

    # Campaign CRUD / send / preview / metrics moved to CampaignService
    # (Spec 25). This service retains only segment resolution and the
    # trackable-link + attribution helpers used by the public redirect and
    # student-action endpoints.

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

    # --- Campaign Links & Attribution ---

    @staticmethod
    def _generate_short_code() -> str:
        import secrets
        import string

        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(10))

    async def create_campaign_link(
        self,
        institution_id: UUID,
        campaign_id: UUID,
        data: CreateCampaignLinkRequest,
    ) -> CampaignLinkResponse:
        await self._verify_campaign_ownership(institution_id, campaign_id)
        short_code = self._generate_short_code()
        link = CampaignLink(
            campaign_id=campaign_id,
            institution_id=institution_id,
            destination_type=data.destination_type,
            destination_id=data.destination_id,
            custom_url=data.custom_url,
            short_code=short_code,
            label=data.label,
        )
        self.db.add(link)
        await self.db.flush()
        await self.db.refresh(link)
        return await self._enrich_campaign_link(link)

    async def get_campaign_links(
        self,
        institution_id: UUID,
        campaign_id: UUID,
    ) -> list[CampaignLinkResponse]:
        await self._verify_campaign_ownership(institution_id, campaign_id)
        result = await self.db.execute(
            select(CampaignLink)
            .where(CampaignLink.campaign_id == campaign_id)
            .order_by(CampaignLink.created_at.desc())
        )
        links = list(result.scalars().all())
        return [await self._enrich_campaign_link(lnk) for lnk in links]

    async def delete_campaign_link(
        self,
        institution_id: UUID,
        campaign_id: UUID,
        link_id: UUID,
    ) -> None:
        await self._verify_campaign_ownership(institution_id, campaign_id)
        result = await self.db.execute(
            select(CampaignLink).where(
                CampaignLink.id == link_id,
                CampaignLink.campaign_id == campaign_id,
            )
        )
        link = result.scalar_one_or_none()
        if not link:
            raise NotFoundException("Campaign link not found")
        await self.db.delete(link)
        await self.db.flush()

    async def record_link_click(
        self,
        short_code: str,
        student_id: UUID | None = None,
    ) -> CampaignLink:
        result = await self.db.execute(
            select(CampaignLink).where(
                CampaignLink.short_code == short_code,
            )
        )
        link = result.scalar_one_or_none()
        if not link:
            raise NotFoundException("Link not found")
        link.click_count = (link.click_count or 0) + 1
        await self.db.flush()

        if student_id:
            action = CampaignAction(
                campaign_id=link.campaign_id,
                link_id=link.id,
                student_id=student_id,
                action_type="click",
                target_id=link.destination_id,
            )
            self.db.add(action)
            # Update CampaignRecipient.clicked_at
            recip_r = await self.db.execute(
                select(CampaignRecipient).where(
                    CampaignRecipient.campaign_id == link.campaign_id,
                    CampaignRecipient.student_id == student_id,
                )
            )
            recip = recip_r.scalar_one_or_none()
            if recip and not recip.clicked_at:
                recip.clicked_at = datetime.now(UTC)
            await self.db.flush()

        await self.db.refresh(link)
        return link

    async def record_campaign_action(
        self,
        campaign_id: UUID,
        student_id: UUID,
        action_type: str,
        target_id: UUID | None = None,
        link_id: UUID | None = None,
    ) -> None:
        action = CampaignAction(
            campaign_id=campaign_id,
            student_id=student_id,
            action_type=action_type,
            target_id=target_id,
            link_id=link_id,
        )
        self.db.add(action)
        # Mark the recipient as responded so §8 conversions reflect engagement.
        recip = await self.db.scalar(
            select(CampaignRecipient).where(
                CampaignRecipient.campaign_id == campaign_id,
                CampaignRecipient.student_id == student_id,
            )
        )
        if recip and not recip.responded_at:
            recip.responded_at = datetime.now(UTC)
        await self.db.flush()

    async def get_campaign_attribution(
        self,
        institution_id: UUID,
        campaign_id: UUID,
    ) -> CampaignAttributionDetail:
        campaign = await self._verify_campaign_ownership(
            institution_id,
            campaign_id,
        )
        # Recipient-level counts
        recip_r = await self.db.execute(
            select(
                func.count(CampaignRecipient.id),
                func.count(CampaignRecipient.delivered_at),
                func.count(CampaignRecipient.opened_at),
                func.count(CampaignRecipient.clicked_at),
            ).where(CampaignRecipient.campaign_id == campaign_id)
        )
        row = recip_r.one()
        total, delivered, opened, clicked = (
            row[0],
            row[1],
            row[2],
            row[3],
        )

        # Action-type counts
        action_counts: dict[str, int] = {}
        for atype in (
            "view",
            "save",
            "rsvp",
            "request_info",
            "apply",
        ):
            cnt_r = await self.db.execute(
                select(func.count(CampaignAction.id)).where(
                    CampaignAction.campaign_id == campaign_id,
                    CampaignAction.action_type == atype,
                )
            )
            action_counts[atype] = cnt_r.scalar() or 0

        # Per-link breakdown
        links_r = await self.db.execute(
            select(CampaignLink).where(
                CampaignLink.campaign_id == campaign_id,
            )
        )
        link_perfs: list[LinkPerformance] = []
        for lnk in links_r.scalars().all():
            dest_name = await self._resolve_destination_name(
                lnk.destination_type,
                lnk.destination_id,
            )
            lnk_views = await self._count_link_actions(
                lnk.id,
                "view",
            )
            lnk_saves = await self._count_link_actions(
                lnk.id,
                "save",
            )
            lnk_apps = await self._count_link_actions(
                lnk.id,
                "apply",
            )
            link_perfs.append(
                LinkPerformance(
                    link_id=lnk.id,
                    label=lnk.label,
                    destination_name=dest_name,
                    clicks=lnk.click_count or 0,
                    views=lnk_views,
                    saves=lnk_saves,
                    applications=lnk_apps,
                )
            )

        return CampaignAttributionDetail(
            campaign_id=campaign_id,
            campaign_name=campaign.campaign_name,
            recipients=total,
            delivered=delivered,
            opened=opened,
            clicked=clicked,
            views=action_counts.get("view", 0),
            saves=action_counts.get("save", 0),
            rsvps=action_counts.get("rsvp", 0),
            request_infos=action_counts.get("request_info", 0),
            applications=action_counts.get("apply", 0),
            links=link_perfs,
        )

    async def _count_link_actions(
        self,
        link_id: UUID,
        action_type: str,
    ) -> int:
        r = await self.db.execute(
            select(func.count(CampaignAction.id)).where(
                CampaignAction.link_id == link_id,
                CampaignAction.action_type == action_type,
            )
        )
        return r.scalar() or 0

    async def _resolve_destination_name(
        self,
        dest_type: str,
        dest_id: UUID | None,
    ) -> str | None:
        if not dest_id:
            return None
        if dest_type == "program":
            r = await self.db.execute(
                select(Program.program_name).where(
                    Program.id == dest_id,
                )
            )
            return r.scalar_one_or_none()
        if dest_type == "event":
            r = await self.db.execute(select(Event.event_name).where(Event.id == dest_id))
            return r.scalar_one_or_none()
        if dest_type == "institution":
            r = await self.db.execute(
                select(Institution.name).where(
                    Institution.id == dest_id,
                )
            )
            return r.scalar_one_or_none()
        return None

    @staticmethod
    def _build_trackable_url(short_code: str) -> str:
        return f"https://api.unipaith.co/api/v1/t/{short_code}"

    async def _enrich_campaign_link(
        self,
        link: CampaignLink,
    ) -> CampaignLinkResponse:
        dest_name = await self._resolve_destination_name(
            link.destination_type,
            link.destination_id,
        )
        return CampaignLinkResponse(
            id=link.id,
            campaign_id=link.campaign_id,
            institution_id=link.institution_id,
            destination_type=link.destination_type,
            destination_id=link.destination_id,
            custom_url=link.custom_url,
            short_code=link.short_code,
            label=link.label,
            click_count=link.click_count or 0,
            trackable_url=self._build_trackable_url(link.short_code),
            destination_name=dest_name,
            created_at=link.created_at,
        )

    # --- Inquiries ---

    async def submit_inquiry(
        self,
        data: SubmitInquiryRequest,
        student_id: UUID | None,
        student_name: str,
        student_email: str,
    ) -> InquiryResponse:
        inquiry = Inquiry(
            institution_id=data.institution_id,
            program_id=data.program_id,
            student_id=student_id,
            student_name=student_name,
            student_email=student_email,
            subject=data.subject,
            message=data.message,
            inquiry_type=data.inquiry_type,
            campaign_id=data.campaign_id,
        )
        self.db.add(inquiry)
        await self.db.flush()
        await self.db.refresh(inquiry)

        # Notify institution admin
        inst_r = await self.db.execute(
            select(Institution).where(
                Institution.id == data.institution_id,
            )
        )
        institution = inst_r.scalar_one_or_none()
        if institution:
            notif = Notification(
                user_id=institution.admin_user_id,
                title=f"New inquiry: {data.subject}",
                body=f"From {student_name} ({student_email})",
                notification_type="inquiry",
                action_url="/i/inquiries",
            )
            self.db.add(notif)
            await self.db.flush()

        prog_name = await self._get_program_name(inquiry.program_id)
        return self._build_inquiry_response(inquiry, prog_name)

    async def list_inquiries(
        self,
        institution_id: UUID,
        status_filter: str | None = None,
    ) -> list[InquiryResponse]:
        stmt = (
            select(Inquiry)
            .where(Inquiry.institution_id == institution_id)
            .order_by(Inquiry.created_at.desc())
        )
        if status_filter:
            stmt = stmt.where(Inquiry.status == status_filter)
        result = await self.db.execute(stmt)

        responses: list[InquiryResponse] = []
        for inq in result.scalars().all():
            pn = await self._get_program_name(inq.program_id)
            responses.append(self._build_inquiry_response(inq, pn))
        return responses

    async def update_inquiry(
        self,
        institution_id: UUID,
        inquiry_id: UUID,
        data: UpdateInquiryRequest,
    ) -> InquiryResponse:
        result = await self.db.execute(
            select(Inquiry).where(
                Inquiry.id == inquiry_id,
                Inquiry.institution_id == institution_id,
            )
        )
        inquiry = result.scalar_one_or_none()
        if not inquiry:
            raise NotFoundException("Inquiry not found")

        for key, val in data.model_dump(exclude_unset=True).items():
            setattr(inquiry, key, val)
        if data.response_text and not inquiry.responded_at:
            inquiry.responded_at = datetime.now(UTC)
            inquiry.status = "responded"

        await self.db.flush()
        await self.db.refresh(inquiry)
        pn = await self._get_program_name(inquiry.program_id)
        return self._build_inquiry_response(inquiry, pn)

    async def _get_program_name(
        self,
        program_id: UUID | None,
    ) -> str | None:
        if not program_id:
            return None
        r = await self.db.execute(
            select(Program.program_name).where(
                Program.id == program_id,
            )
        )
        return r.scalar_one_or_none()

    @staticmethod
    def _build_inquiry_response(inq: Inquiry, prog_name: str | None) -> InquiryResponse:
        return InquiryResponse(
            id=inq.id,
            institution_id=inq.institution_id,
            program_id=inq.program_id,
            student_id=inq.student_id,
            student_name=inq.student_name,
            student_email=inq.student_email,
            subject=inq.subject,
            message=inq.message,
            inquiry_type=inq.inquiry_type,
            status=inq.status,
            assigned_to=inq.assigned_to,
            response_text=inq.response_text,
            responded_at=inq.responded_at,
            campaign_id=inq.campaign_id,
            created_at=inq.created_at,
            updated_at=inq.updated_at,
            program_name=prog_name,
        )

    # --- Promotions ---

    async def list_promotions(
        self,
        institution_id: UUID,
    ) -> list[PromotionResponse]:
        result = await self.db.execute(
            select(Promotion)
            .where(Promotion.institution_id == institution_id)
            .order_by(Promotion.created_at.desc())
        )
        return [await self._enrich_promotion(p) for p in result.scalars().all()]

    async def create_promotion(
        self,
        institution_id: UUID,
        data: CreatePromotionRequest,
    ) -> PromotionResponse:
        targeting_dict = data.targeting.model_dump() if data.targeting else None
        promo = Promotion(
            institution_id=institution_id,
            program_id=data.program_id,
            promotion_type=data.promotion_type,
            title=data.title,
            description=data.description,
            targeting=targeting_dict,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            target_kind=data.target_kind,
            target_url=data.target_url,
        )
        self.db.add(promo)
        await self.db.flush()
        await self.db.refresh(promo)
        return await self._enrich_promotion(promo)

    async def update_promotion(
        self,
        institution_id: UUID,
        promotion_id: UUID,
        data: UpdatePromotionRequest,
    ) -> PromotionResponse:
        result = await self.db.execute(
            select(Promotion).where(
                Promotion.id == promotion_id,
                Promotion.institution_id == institution_id,
            )
        )
        promo = result.scalar_one_or_none()
        if not promo:
            raise NotFoundException("Promotion not found")

        update = data.model_dump(exclude_unset=True)
        if "targeting" in update and update["targeting"] is not None:
            t = update["targeting"]
            update["targeting"] = t.model_dump() if hasattr(t, "model_dump") else t
        for key, val in update.items():
            setattr(promo, key, val)

        # Auto-expire check
        if data.status == "active" and promo.ends_at:
            if promo.ends_at < datetime.now(UTC):
                promo.status = "expired"

        await self.db.flush()
        await self.db.refresh(promo)
        return await self._enrich_promotion(promo)

    async def delete_promotion(
        self,
        institution_id: UUID,
        promotion_id: UUID,
    ) -> None:
        result = await self.db.execute(
            select(Promotion).where(
                Promotion.id == promotion_id,
                Promotion.institution_id == institution_id,
            )
        )
        promo = result.scalar_one_or_none()
        if not promo:
            raise NotFoundException("Promotion not found")
        await self.db.delete(promo)
        await self.db.flush()

    async def get_active_promotions(
        self,
        region: str | None = None,
        country: str | None = None,
        degree_type: str | None = None,
    ) -> list[PromotionResponse]:
        """Public — get currently active promotions matching scope."""
        now = datetime.now(UTC)
        stmt = select(Promotion).where(
            Promotion.status == "active",
        )
        result = await self.db.execute(stmt)

        promos: list[PromotionResponse] = []
        for p in result.scalars().all():
            # Time-box check
            if p.starts_at and p.starts_at > now:
                continue
            if p.ends_at and p.ends_at < now:
                continue

            # Targeting scope filter
            targeting = p.targeting or {}
            if region and targeting.get("regions"):
                if region.lower() not in [r.lower() for r in targeting["regions"]]:
                    continue
            if country and targeting.get("countries"):
                if country.lower() not in [c.lower() for c in targeting["countries"]]:
                    continue
            if degree_type and targeting.get("degree_types"):
                if degree_type.lower() not in [d.lower() for d in targeting["degree_types"]]:
                    continue

            # Collect matching promotions
            promos.append(p)

        # Increment impressions and enrich
        results: list[PromotionResponse] = []
        for p in promos:
            p.impression_count = (p.impression_count or 0) + 1
        if promos:
            await self.db.flush()
            for p in promos:
                await self.db.refresh(p)
                results.append(await self._enrich_promotion(p))
        return results

    async def _enrich_promotion(
        self,
        promo: Promotion,
    ) -> PromotionResponse:
        prog_name = await self._get_program_name(promo.program_id)
        inst_name = None
        r = await self.db.execute(
            select(Institution.name).where(
                Institution.id == promo.institution_id,
            )
        )
        inst_name = r.scalar_one_or_none()

        # Eligibility: must have program published
        is_eligible = True
        if promo.program_id:
            pr = await self.db.execute(
                select(Program.is_published).where(
                    Program.id == promo.program_id,
                )
            )
            published = pr.scalar_one_or_none()
            if not published:
                is_eligible = False

        return PromotionResponse(
            id=promo.id,
            institution_id=promo.institution_id,
            program_id=promo.program_id,
            promotion_type=promo.promotion_type,
            title=promo.title,
            description=promo.description,
            targeting=promo.targeting,
            status=promo.status,
            starts_at=promo.starts_at,
            ends_at=promo.ends_at,
            impression_count=promo.impression_count or 0,
            click_count=promo.click_count or 0,
            target_kind=getattr(promo, "target_kind", "program") or "program",
            target_url=getattr(promo, "target_url", None),
            created_at=promo.created_at,
            updated_at=promo.updated_at,
            program_name=prog_name,
            institution_name=inst_name,
            is_eligible=is_eligible,
        )

    # --- Datasets ---

    async def list_datasets(self, institution_id: UUID) -> list[InstitutionDataset]:
        result = await self.db.execute(
            select(InstitutionDataset)
            .where(InstitutionDataset.institution_id == institution_id)
            .order_by(InstitutionDataset.created_at.desc())
        )
        return list(result.scalars().all())

    async def request_dataset_upload(
        self,
        institution_id: UUID,
        user_id: UUID,
        data: CreateDatasetRequest,
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
            coverage_start=data.coverage_start,
            coverage_end=data.coverage_end,
            status="uploaded",
            uploaded_by=user_id,
        )
        self.db.add(dataset)
        await self.db.flush()
        await self.db.refresh(dataset)
        return DatasetUploadResponse(dataset_id=dataset.id, upload_url=upload_url)

    async def confirm_dataset_upload(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        user_id: UUID,
        *,
        column_mapping: dict | None = None,
        skip_invalid_rows: bool = False,
        save_template: bool = False,
        template_name: str | None = None,
    ) -> tuple[InstitutionDataset, dict]:
        from unipaith.services.dataset_upload_service import DatasetUploadService

        return await DatasetUploadService(self.db).confirm_upload(
            institution_id,
            dataset_id,
            user_id,
            column_mapping=column_mapping,
            skip_invalid_rows=skip_invalid_rows,
            save_template=save_template,
            template_name=template_name,
        )

    async def get_dataset(self, institution_id: UUID, dataset_id: UUID) -> DatasetResponse:
        from unipaith.services.dataset_upload_service import dataset_used_by

        dataset = await self._verify_dataset_ownership(institution_id, dataset_id)
        from unipaith.core.s3 import S3Client

        s3 = S3Client()
        download_url = s3.generate_download_url(dataset.s3_key)
        resp = DatasetResponse.model_validate(dataset)
        resp.download_url = download_url
        resp.used_by = dataset_used_by(dataset.usage_scope)
        return resp

    async def get_dataset_preview(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        *,
        limit: int = 100,
    ) -> DatasetPreviewResponse:
        from unipaith.services.dataset_upload_service import DatasetUploadService

        data = await DatasetUploadService(self.db).get_preview(
            institution_id, dataset_id, limit=limit
        )
        return DatasetPreviewResponse(**data)

    async def request_dataset_replace_upload(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        data: DatasetReplaceRequest,
    ) -> DatasetUploadResponse:
        from unipaith.core.s3 import S3Client

        dataset = await self._verify_dataset_ownership(institution_id, dataset_id)
        s3_key = f"datasets/{institution_id}/{dataset.id}/staging/{uuid.uuid4()}/{data.file_name}"
        s3 = S3Client()
        upload_url = s3.generate_upload_url(s3_key, data.content_type)
        return DatasetUploadResponse(
            dataset_id=dataset.id, upload_url=upload_url, staging_s3_key=s3_key
        )

    async def confirm_dataset_replace(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        user_id: UUID,
        *,
        staging_s3_key: str,
        file_name: str,
        update_mode: str,
        column_mapping: dict | None = None,
        skip_invalid_rows: bool = False,
    ) -> tuple[InstitutionDataset, dict]:
        from unipaith.services.dataset_upload_service import DatasetUploadService

        return await DatasetUploadService(self.db).replace_or_append_file(
            institution_id,
            dataset_id,
            user_id,
            new_s3_key=staging_s3_key,
            new_file_name=file_name,
            mode=update_mode,
            column_mapping=column_mapping,
            skip_invalid_rows=skip_invalid_rows,
        )

    async def update_dataset(
        self,
        institution_id: UUID,
        dataset_id: UUID,
        data: UpdateDatasetRequest,
    ) -> InstitutionDataset:
        dataset = await self._verify_dataset_ownership(institution_id, dataset_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dataset, key, value)
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset

    async def delete_dataset(self, institution_id: UUID, dataset_id: UUID, user_id: UUID) -> None:
        from unipaith.services.dataset_upload_service import DatasetUploadService

        await DatasetUploadService(self.db).delete_dataset(institution_id, dataset_id, user_id)

    async def _verify_dataset_ownership(
        self,
        institution_id: UUID,
        dataset_id: UUID,
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
        delivery_format: str | None = None,
        campus_setting: str | None = None,
        max_duration_months: int | None = None,
        city: str | None = None,
        # Spec 10 — additive type-first search filters (constraint chips → kwargs).
        degree_types: list[str] | None = None,
        delivery_formats: list[str] | None = None,
        location: str | None = None,
        region: str | None = None,
        min_duration_months: int | None = None,
        min_acceptance_rate: float | None = None,
        max_acceptance_rate: float | None = None,
        start_year: int | None = None,
        program_name: str | None = None,
        # Spec 10 §5 — featured / outcome filters (program-level outcomes_data).
        min_median_salary: int | None = None,
        min_employment_rate: float | None = None,
        max_payback_months: int | None = None,
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
            stmt = stmt.where(Institution.country.ilike(f"%{_escape_like(country)}%"))
        if degree_type:
            stmt = stmt.where(Program.degree_type == degree_type)
        if institution_id:
            stmt = stmt.where(Program.institution_id == institution_id)
        if min_tuition is not None:
            stmt = stmt.where(Program.tuition >= min_tuition)
        if max_tuition is not None:
            stmt = stmt.where(Program.tuition <= max_tuition)
        if delivery_format:
            stmt = stmt.where(Program.delivery_format == delivery_format)
        if campus_setting:
            stmt = stmt.where(Program.campus_setting == campus_setting)
        if max_duration_months is not None:
            stmt = stmt.where(Program.duration_months <= max_duration_months)
        if city:
            stmt = stmt.where(Institution.city.ilike(f"%{_escape_like(city)}%"))
        # Spec 10 — chip-derived filters. degree_types/delivery_formats are
        # case-insensitive IN lists so a single chip can match DB synonyms
        # (e.g. format "in_person" → {in_person, on_campus}).
        if degree_types:
            stmt = stmt.where(
                func.lower(Program.degree_type).in_([d.lower() for d in degree_types])
            )
        if delivery_formats:
            stmt = stmt.where(
                func.lower(Program.delivery_format).in_([f.lower() for f in delivery_formats])
            )
        if location:
            loc = f"%{_escape_like(location)}%"
            stmt = stmt.where(
                or_(
                    Institution.country.ilike(loc),
                    Institution.region.ilike(loc),
                    Institution.city.ilike(loc),
                )
            )
        if region:
            stmt = stmt.where(Institution.region.ilike(f"%{_escape_like(region)}%"))
        if min_duration_months is not None:
            stmt = stmt.where(Program.duration_months >= min_duration_months)
        if min_acceptance_rate is not None:
            stmt = stmt.where(Program.acceptance_rate >= min_acceptance_rate)
        if max_acceptance_rate is not None:
            stmt = stmt.where(Program.acceptance_rate <= max_acceptance_rate)
        if start_year is not None:
            # Soft filter: keep programs with no start date set so a low-
            # confidence start_term chip doesn't zero out the results.
            stmt = stmt.where(
                or_(
                    Program.program_start_date.is_(None),
                    func.extract("year", Program.program_start_date) == start_year,
                )
            )
        if program_name:
            stmt = stmt.where(Program.program_name.ilike(f"%{_escape_like(program_name)}%"))
        # Spec 10 §5 — outcome filters over program-level outcomes_data. Programs
        # missing the metric are excluded (NULL JSON access → NULL → fails the
        # comparison), so these only ever narrow the set when applied.
        # Spec 68 §6 — typed `program_outcomes` first (authority-resolved §7),
        # legacy outcomes_data JSONB as the cutover fallback (dual-read).
        if min_median_salary is not None:
            salary_expr = func.coalesce(
                _resolved_metric_subq("salary_median"),
                Program.outcomes_data["median_salary"].as_integer(),
                Program.outcomes_data["earnings_4yr_median"].as_integer(),
                Program.outcomes_data["earnings_1yr_median"].as_integer(),
            )
            stmt = stmt.where(salary_expr >= min_median_salary)
        if min_employment_rate is not None:
            employment_expr = func.coalesce(
                _resolved_metric_subq("employment_rate"),
                Program.outcomes_data["employment_rate"].as_float(),
            )
            stmt = stmt.where(employment_expr >= min_employment_rate)
        if max_payback_months is not None:
            payback_expr = func.coalesce(
                _resolved_metric_subq("payback_period_months"),
                Program.outcomes_data["payback_months"].as_integer(),
            )
            stmt = stmt.where(payback_expr <= max_payback_months)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        if sort_by == "tuition_asc":
            stmt = stmt.order_by(Program.tuition.asc().nulls_last())
        elif sort_by == "tuition_desc":
            stmt = stmt.order_by(Program.tuition.desc().nulls_last())
        elif sort_by == "deadline":
            stmt = stmt.order_by(
                Program.application_deadline.asc().nulls_last(),
            )
        elif sort_by == "salary_desc":
            stmt = stmt.order_by(
                func.coalesce(
                    _resolved_metric_subq("salary_median"),
                    Program.outcomes_data["median_salary"].as_integer(),
                )
                .desc()
                .nulls_last(),
            )
        elif sort_by == "employment_desc":
            stmt = stmt.order_by(
                func.coalesce(
                    _resolved_metric_subq("employment_rate"),
                    Program.outcomes_data["employment_rate"].as_float(),
                )
                .desc()
                .nulls_last(),
            )
        elif sort_by == "payback_asc":
            stmt = stmt.order_by(
                func.coalesce(
                    _resolved_metric_subq("payback_period_months"),
                    Program.outcomes_data["payback_months"].as_integer(),
                )
                .asc()
                .nulls_last(),
            )
        elif sort_by == "acceptance_asc":
            stmt = stmt.order_by(Program.acceptance_rate.asc().nulls_last())
        elif sort_by == "acceptance_desc":
            stmt = stmt.order_by(Program.acceptance_rate.desc().nulls_last())
        elif sort_by == "recently_added":
            stmt = stmt.order_by(Program.created_at.desc().nulls_last())
        else:
            stmt = stmt.order_by(Program.program_name.asc())

        offset = (page - 1) * page_size
        results = await self.db.execute(stmt.offset(offset).limit(page_size))
        rows = results.all()

        # Spec 68 §6 — resolve typed outcomes for this page in one query; the
        # response prefers them, falling back to legacy JSONB during cutover.
        from unipaith.services.outcomes_service import OutcomesService

        _resolved = await OutcomesService(self.db).resolve_program_metrics_bulk(
            [prog.id for prog, _inst in rows],
            ["salary_median", "employment_rate", "payback_period_months"],
        )

        items = [
            ProgramSummaryResponse(
                id=prog.id,
                institution_id=prog.institution_id,
                program_name=prog.program_name,
                degree_type=prog.degree_type,
                department=prog.department,
                # Program-level fields stay null when unknown — do NOT fall back to
                # institution-wide tuition/acceptance because those mislead students
                # (e.g., NYU's 9% university acceptance ≠ Tisch's program-specific rate).
                # Institution-level values are available via `ranking_data` for context.
                tuition=prog.tuition,
                duration_months=prog.duration_months,
                delivery_format=prog.delivery_format,
                acceptance_rate=(
                    float(prog.acceptance_rate) if prog.acceptance_rate is not None else None
                ),
                application_deadline=prog.application_deadline,
                institution_name=inst.name,
                institution_country=inst.country,
                institution_city=inst.city,
                # Program-level outcomes only — do NOT fall back to institution
                # earnings_10yr_median or graduation_rate. Institution-wide values
                # are available via the institution ranking_data for context, but
                # showing them on program cards misleads students (e.g., NYU's
                # 82509 institution 10yr median shown uniformly for every program
                # without Scorecard-by-CIP coverage).
                median_salary=(
                    int(_resolved[(prog.id, "salary_median")])
                    if (prog.id, "salary_median") in _resolved
                    else _outcomes_int(prog, "median_salary")
                    or _outcomes_int(prog, "earnings_4yr_median")
                    or _outcomes_int(prog, "earnings_1yr_median")
                ),
                employment_rate=_resolved.get(
                    (prog.id, "employment_rate"),
                    _outcomes_float(prog, "employment_rate"),
                ),
                payback_months=(
                    int(_resolved[(prog.id, "payback_period_months")])
                    if (prog.id, "payback_period_months") in _resolved
                    else _outcomes_int(prog, "payback_months")
                ),
                description_text=prog.description_text,
                media_urls=prog.media_urls,
                highlights=prog.highlights,
                institution_logo_url=inst.logo_url,
                institution_image_url=(
                    (prog.media_urls or [None])[0]
                    if prog.media_urls
                    else (inst.media_gallery or [None])[0]
                    if inst.media_gallery
                    else None
                ),
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
        result = await self.db.execute(select(Institution).where(Institution.id == institution_id))
        institution = result.scalar_one_or_none()
        if not institution:
            raise NotFoundException("Institution not found")
        return institution

    async def semantic_search_programs(
        self,
        query: str,
        limit: int = 20,
    ) -> list[ProgramSummaryResponse]:
        # AI embedding engine is being rebuilt — return empty results
        return []

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
        self,
        institution_id: UUID,
        include_drafts: bool = True,
    ) -> list[PostResponse]:
        q = select(InstitutionPost).where(InstitutionPost.institution_id == institution_id)
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
        self,
        institution_id: UUID,
        user_id: UUID,
        data: CreatePostRequest,
    ) -> PostResponse:
        post = InstitutionPost(
            institution_id=institution_id,
            author_id=user_id,
            title=data.title,
            body=data.body,
            media_urls=(
                [m if isinstance(m, dict) else {"url": m} for m in data.media_urls]
                if data.media_urls
                else None
            ),
            tagged_program_ids=(
                [str(pid) for pid in data.tagged_program_ids] if data.tagged_program_ids else None
            ),
            tagged_intake=data.tagged_intake,
            status=data.status,
            scheduled_for=data.scheduled_for,
            is_template=data.is_template,
            template_name=data.template_name,
            ctas=([c.model_dump(mode="json") for c in data.ctas] if data.ctas else None),
            visibility=(data.visibility.model_dump(mode="json") if data.visibility else None),
        )
        if data.status == "published":
            post.published_at = datetime.now(UTC)
        self.db.add(post)
        await self.db.flush()
        await self.db.refresh(post)
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
        # Spec 27 §2.4 / §2.3 — store CTAs + visibility as JSON-safe dicts.
        if "ctas" in update_data:
            update_data["ctas"] = (
                [c.model_dump(mode="json") for c in data.ctas] if data.ctas else None
            )
        if "visibility" in update_data:
            update_data["visibility"] = (
                data.visibility.model_dump(mode="json") if data.visibility else None
            )
        was_published = post.status == "published"
        for key, value in update_data.items():
            setattr(post, key, value)
        if not was_published and post.status == "published":
            post.published_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(post)
        return await self._enrich_post(post)

    async def delete_post(
        self,
        institution_id: UUID,
        post_id: UUID,
    ) -> None:
        post = await self._get_post(institution_id, post_id)
        await self.db.delete(post)
        await self.db.flush()

    async def pin_post(
        self,
        institution_id: UUID,
        post_id: UUID,
    ) -> PostResponse:
        post = await self._get_post(institution_id, post_id)
        post.pinned = not post.pinned
        await self.db.flush()
        await self.db.refresh(post)
        return await self._enrich_post(post)

    async def publish_post(
        self,
        institution_id: UUID,
        post_id: UUID,
    ) -> PostResponse:
        post = await self._get_post(institution_id, post_id)
        post.status = "published"
        post.published_at = datetime.now(UTC)
        await self.db.flush()
        await self.db.refresh(post)
        return await self._enrich_post(post)

    # Spec 27 §5 — per-object engagement: (object_type, action) -> counter column.
    _ENGAGEMENT_COLUMNS: dict[tuple[str, str], str] = {
        ("post", "view"): "view_count",
        ("post", "click"): "click_count",
        ("post", "save"): "save_count",
        ("post", "request_info"): "request_info_count",
        ("post", "apply_started"): "apply_started_count",
        ("event", "view"): "view_count",
        ("promotion", "view"): "impression_count",
        ("promotion", "impression"): "impression_count",
        ("promotion", "click"): "click_count",
    }

    async def record_engagement(
        self,
        object_type: str,
        object_id: UUID,
        action: str,
        student_id: UUID | None = None,
    ) -> None:
        """Spec 27 §5 — increment a per-object performance counter, and (Spec 28)
        record a per-student attribution event for the analytics funnel.

        Best-effort: an unknown (type, action) pair is ignored for the counter so
        a new client event never 500s the caller. Atomic increment (no
        read-modify-write).
        """
        model_map = {"post": InstitutionPost, "event": Event, "promotion": Promotion}
        model = model_map.get(object_type)
        if model is None:
            return
        col = self._ENGAGEMENT_COLUMNS.get((object_type, action))
        if col is not None:
            await self.db.execute(
                update(model).where(model.id == object_id).values({col: getattr(model, col) + 1})
            )
            await self.db.flush()

        # Spec 28 — the canonical event-sourced store the funnel reads from.
        # post/event/promotion engagement has no durable domain table to
        # backfill from (the counters above are anonymous totals), so capture it
        # live here with the authenticated student.
        from unipaith.services.attribution_service import AttributionService

        obj = await self.db.get(model, object_id)
        if obj is not None:
            await AttributionService(self.db).record(
                institution_id=obj.institution_id,
                student_id=student_id,
                source_kind=object_type,
                source_id=object_id,
                action=action,
                program_id=getattr(obj, "program_id", None),
            )

    async def request_post_media_upload(
        self,
        institution_id: UUID,
        content_type: str,
    ) -> PostMediaUploadResponse:
        from unipaith.core.s3 import S3Client

        s3 = S3Client()
        key = f"institutions/{institution_id}/posts/media/{uuid.uuid4()}"
        upload_url = s3.generate_upload_url(key, content_type)
        return PostMediaUploadResponse(upload_url=upload_url, media_key=key)

    async def list_post_templates(
        self,
        institution_id: UUID,
    ) -> list[PostResponse]:
        result = await self.db.execute(
            select(InstitutionPost)
            .where(
                InstitutionPost.institution_id == institution_id,
                InstitutionPost.is_template.is_(True),
            )
            .order_by(InstitutionPost.created_at.desc())
        )
        posts = list(result.scalars().all())
        return [await self._enrich_post(p) for p in posts]

    async def get_public_posts(
        self,
        institution_id: UUID,
        school_id: UUID | None = None,
        program_id: UUID | None = None,
        institution_scope: bool = False,
    ) -> list[PostResponse]:
        query = (
            select(InstitutionPost)
            .where(
                InstitutionPost.institution_id == institution_id,
                InstitutionPost.status == "published",
            )
            .order_by(
                InstitutionPost.pinned.desc(),
                InstitutionPost.published_at.desc().nulls_last(),
            )
        )
        if school_id is not None:
            query = query.where(InstitutionPost.school_id == school_id)
        if program_id is not None:
            query = query.where(InstitutionPost.program_id == program_id)
        if institution_scope:
            # Institution page: only institution-wide items, so a school/program
            # copy of the same article doesn't duplicate the MIT-wide one.
            query = query.where(
                InstitutionPost.school_id.is_(None),
                InstitutionPost.program_id.is_(None),
            )
        result = await self.db.execute(query)
        posts = list(result.scalars().all())
        # Spec 27 §2.3 — public pages exclude posts scoped non-public.
        posts = [
            p
            for p in posts
            if not (isinstance(p.visibility, dict) and p.visibility.get("public") is False)
        ]
        return [await self._enrich_post(p) for p in posts]

    async def _get_post(
        self,
        institution_id: UUID,
        post_id: UUID,
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
            user_r = await self.db.execute(select(User.email).where(User.id == post.author_id))
            author_email = user_r.scalar_one_or_none()

        program_names: list[str] | None = None
        tag_ids = post.tagged_program_ids
        if tag_ids and isinstance(tag_ids, list) and len(tag_ids) > 0:
            prog_r = await self.db.execute(
                select(Program.program_name).where(Program.id.in_(tag_ids))
            )
            program_names = list(prog_r.scalars().all())

        return PostResponse(
            id=post.id,
            institution_id=post.institution_id,
            author_id=post.author_id,
            title=post.title,
            body=post.body,
            media_urls=resolve_media_urls(post.media_urls),
            pinned=post.pinned,
            tagged_program_ids=post.tagged_program_ids,
            tagged_intake=post.tagged_intake,
            status=post.status,
            scheduled_for=post.scheduled_for,
            published_at=post.published_at,
            is_template=post.is_template,
            template_name=post.template_name,
            view_count=post.view_count,
            click_count=post.click_count or 0,
            save_count=post.save_count or 0,
            request_info_count=post.request_info_count or 0,
            apply_started_count=post.apply_started_count or 0,
            ctas=post.ctas,
            visibility=post.visibility,
            source=post.source,
            source_url=post.source_url,
            image_url=post.image_url,
            school_id=post.school_id,
            program_id=post.program_id,
            created_at=post.created_at,
            updated_at=post.updated_at,
            author_email=author_email,
            program_names=program_names,
        )

    # ------------------------------------------------------------------
    # NLP Search
    # ------------------------------------------------------------------

    async def nlp_search_programs(self, query: str) -> NLPSearchResponse:
        """Parse a natural-language query into structured filters via LLM,
        then delegate to search_programs()."""

        parsed = await self._parse_nlp_query(query)

        results = await self.search_programs(
            query=parsed.get("parsed_query"),
            country=parsed.get("country"),
            degree_type=parsed.get("degree_type"),
            min_tuition=parsed.get("min_tuition"),
            max_tuition=parsed.get("max_tuition"),
            sort_by=parsed.get("sort_by"),
        )

        interpretation = parsed.get(
            "interpretation",
            f"Showing results for: {query}",
        )

        filters_applied = {
            k: v for k, v in parsed.items() if k != "interpretation" and v is not None
        }

        return NLPSearchResponse(
            filters_applied=filters_applied,
            results=results,
            interpretation=interpretation,
        )

    async def _parse_nlp_query(self, query: str) -> dict:
        """Interpret a natural-language query into structured search constraints.

        Spec 10 §3 / Spec 45 §12 — the ``DiscoveryQueryInterpreter``. This is the
        deterministic, offline rule-based default (AI_MOCK_MODE-safe and the
        fallback the spec mandates): it extracts degree level, delivery format,
        location, and budget so each surfaces as an individually editable /
        removable chip (Spec 09 §5.1, Spec 10 §4). The LLM interpreter can swap
        in behind this exact output shape with no caller change.
        """
        return interpret_search_query(query)


# ── Rule-based query interpreter (Spec 10 §3 / Spec 45 §12) ─────────────────
# Deterministic + offline so it works in AI_MOCK_MODE and as the spec-mandated
# default before the LLM DiscoveryQueryInterpreter is wired in. The output shape
# matches what the LLM path returns, so swapping the implementation needs no
# caller change. Pure function (no DB / no I/O) → trivially unit-testable.

# Order matters: PhD and MBA are checked before the generic master's rule.
_DEGREE_RULES: list[tuple[str, str]] = [
    (r"\bph\.?\s*d\b|\bdoctoral\b|\bdoctorate\b", "phd"),
    (r"\bm\.?b\.?a\b", "masters"),
    (r"\bmaster'?s?\b|\bmsc?\b|\bm\.s\.?\b|\bgraduate\b|\bgrad\b", "masters"),
    (r"\bbachelor'?s?\b|\bb\.?s\b|\bb\.?a\b|\bundergraduate\b|\bundergrad\b", "bachelor"),
    (r"\bcertificate\b|\bcertification\b", "certificate"),
]
_FORMAT_RULES: list[tuple[str, str]] = [
    (r"\bonline\b", "online"),
    (r"\bhybrid\b", "hybrid"),
    (r"\bin[\s-]?person\b|\bon[\s-]?campus\b", "in_person"),
]
_COUNTRY_RULES: list[tuple[str, str]] = [
    (r"\bunited states\b|\bu\.?s\.?a\b|\bu\.?s\b|\bamerica\b", "United States"),
    (r"\bunited kingdom\b|\bu\.?k\b|\bengland\b|\bbritain\b", "United Kingdom"),
    (r"\bcanada\b", "Canada"),
    (r"\baustralia\b", "Australia"),
    (r"\bgermany\b", "Germany"),
    (r"\bsingapore\b", "Singapore"),
]
_DEGREE_LABELS = {
    "phd": "PhD",
    "masters": "Master's",
    "bachelor": "Bachelor's",
    "certificate": "Certificate",
}
_FORMAT_LABELS = {"online": "Online", "hybrid": "Hybrid", "in_person": "In person"}
_NOISE_WORDS = re.compile(
    r"\b(programs?|degrees?|courses?|schools?|universit(?:y|ies)|find|show|me|looking|"
    r"want|in|for|the|a|an|with|near|around|that|are|is)\b",
    re.IGNORECASE,
)
_BUDGET_TRIGGER = re.compile(
    r"(?:under|below|less than|cheaper than|<=?|≤|max(?:imum)?|up to|within|"
    r"budget(?:\s+of)?|no more than)\s*\$?\s*(\d[\d,]*)\s*(k|thousand)?",
    re.IGNORECASE,
)
_BUDGET_DOLLAR = re.compile(r"\$\s*(\d[\d,]*)\s*(k|thousand)?", re.IGNORECASE)


def _money_label(amount: int) -> str:
    return f"${amount // 1000}k" if amount % 1000 == 0 else f"${amount:,}"


def interpret_search_query(raw: str) -> dict:
    """Extract structured search constraints from a natural-language query.

    Returns the param dict consumed by ``search_programs`` plus a human-readable
    ``interpretation``. Unmatched text becomes ``parsed_query`` (the keyword for
    full-text search). All keys are always present (None when not detected).
    """
    text = (raw or "").strip()
    low = text.lower()
    out: dict = {
        "parsed_query": None,
        "country": None,
        "city": None,
        "degree_type": None,
        "max_tuition": None,
        "min_tuition": None,
        "delivery_format": None,
        "sort_by": None,
    }
    residual = text
    parts: list[str] = []

    def _consume(pattern: str) -> None:
        nonlocal residual
        residual = re.sub(pattern, " ", residual, flags=re.IGNORECASE)

    for pattern, value in _DEGREE_RULES:
        if re.search(pattern, low):
            out["degree_type"] = value
            _consume(pattern)
            parts.append(_DEGREE_LABELS[value])
            break

    for pattern, value in _FORMAT_RULES:
        if re.search(pattern, low):
            out["delivery_format"] = value
            _consume(pattern)
            parts.append(_FORMAT_LABELS[value])
            break

    for pattern, value in _COUNTRY_RULES:
        if re.search(pattern, low):
            out["country"] = value
            _consume(pattern)
            parts.append(value)
            break

    budget = _BUDGET_TRIGGER.search(low) or _BUDGET_DOLLAR.search(low)
    if budget is not None:
        amount = int(budget.group(1).replace(",", ""))
        if (budget.group(2) or "").lower() in {"k", "thousand"}:
            amount *= 1000
        out["max_tuition"] = amount
        _consume(re.escape(budget.group(0)))
        parts.append(f"under {_money_label(amount)}")

    # Clean the keyword residual: drop noise words + leftover symbols.
    residual = _NOISE_WORDS.sub(" ", residual)
    residual = re.sub(r"[$<>≤=,]", " ", residual)
    residual = re.sub(r"\s+", " ", residual).strip(" -·,")
    if residual:
        out["parsed_query"] = residual

    if residual and parts:
        out["interpretation"] = residual + " · " + " · ".join(parts)
    elif residual:
        out["interpretation"] = residual
    elif parts:
        out["interpretation"] = " · ".join(parts)
    else:
        out["interpretation"] = f"Showing results for: {text}" if text else "All programs"
    return out


def _safe_json(text: str):
    """Safely parse JSON from LLM output, stripping markdown fences."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"[\[\{].*[\]\}]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None
