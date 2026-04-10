from __future__ import annotations

import logging
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.llm_client import get_llm_client
from unipaith.config import settings
from unipaith.core.exceptions import ConflictException, NotFoundException
from unipaith.schemas.conversation import (
    AssistantMessageResponse,
    ConfidenceLevel,
    ConfidenceReportResponse,
    ConfidenceSummaryResponse,
    ConversationDomain,
    ConversationRequirementResponse,
    ConversationSessionResponse,
    ConversationStage,
    ConversationStateDeltaResponse,
    ConversationTurnRequest,
    ConversationTurnResponse,
    DomainConfidenceResponse,
    ListConversationRequirementsResponse,
    ResolveConflictResponse,
    ResumeCheckpointResponse,
    ShortlistUnlockResponse,
    ShortlistUnlockThresholdsResponse,
    UpdateConversationRequirementRequest,
)
from unipaith.services.student_service import StudentService

logger = logging.getLogger("unipaith.conversation_service")


@dataclass
class _RequirementState:
    requirement_id: UUID
    domain: ConversationDomain
    field: str
    value: object | None
    priority: str
    source: str
    confidence: int
    status: str
    evidence_turn_ids: list[UUID] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class _ConflictState:
    conflict_id: UUID
    reason: str
    resolution_options: list[str]
    selected_resolution: str | None = None


@dataclass
class _ConversationSessionState:
    session_id: UUID
    student_id: UUID
    current_stage: ConversationStage = "understand_context"
    active_domain: ConversationDomain = "career_outcome"
    turn_count: int = 0
    last_updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_assistant_prompt: str | None = None
    requirements: dict[UUID, _RequirementState] = field(default_factory=dict)
    conflicts: dict[UUID, _ConflictState] = field(default_factory=dict)


_SESSIONS_BY_STUDENT: dict[UUID, _ConversationSessionState] = {}

_TEMPLATE_REPLY = (
    "Thanks for sharing that — I have updated your {domain} context. "
    "You are making solid progress. Next, we can fill one "
    "missing requirement to increase recommendation confidence "
    "and keep your plan calm and clear."
)

_REQUIRED_FIELDS_BY_DOMAIN: dict[ConversationDomain, list[str]] = {
    "budget_finance": ["max_annual_tuition"],
    "timeline_intake": ["target_intake"],
    "eligibility_compliance": ["language_test_min"],
    "country_location": ["allowed_countries"],
    "career_outcome": ["primary_goal"],
    "academic_readiness": [],
    "learning_preferences": [],
}


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.student_service = StudentService(db)
        self.llm = get_llm_client()

    async def send_turn(
        self, student_user_id: UUID, body: ConversationTurnRequest
    ) -> ConversationTurnResponse:
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None:
            session = _ConversationSessionState(session_id=uuid4(), student_id=profile.id)
            _SESSIONS_BY_STUDENT[profile.id] = session
            await self._bootstrap_requirements(session, student_user_id)

        session.turn_count += 1
        session.last_updated_at = datetime.now(UTC)
        turn_id = uuid4()
        conflicts_before = len(session.conflicts)

        selected_domain = self._pick_domain(body.message)
        session.active_domain = selected_domain
        session.current_stage = self._pick_stage(session.turn_count)

        if "budget" in body.message.lower() and "full scholarship" in body.message.lower():
            conflict_id = uuid4()
            session.conflicts[conflict_id] = _ConflictState(
                conflict_id=conflict_id,
                reason=(
                    "Potential tradeoff between low budget ceiling"
                    " and scholarship-only requirement."
                ),
                resolution_options=[
                    "Increase budget range",
                    "Expand country set",
                    "Keep strict constraints and accept fewer options",
                ],
            )

        assistant_text = await self._build_assistant_reply(selected_domain, body.message, session)
        session.last_assistant_prompt = assistant_text

        if selected_domain == "budget_finance":
            self._upsert_requirement(
                session=session,
                domain="budget_finance",
                field="max_annual_tuition",
                value=self._extract_budget_hint(body.message),
                source="inferred",
                evidence_turn_id=turn_id,
            )

        confidence = self._compute_confidence(session)
        return ConversationTurnResponse(
            session=self._to_session_response(session),
            assistant_message=AssistantMessageResponse(
                message_id=uuid4(),
                reply_text=assistant_text,
                why_asked=(
                    f"I am focusing on {selected_domain}"
                    " because this directly affects shortlist quality."
                ),
                suggested_next_actions=self._next_actions(session),
            ),
            state_delta=ConversationStateDeltaResponse(
                updated_domains=[selected_domain],
                new_requirements_count=1 if selected_domain == "budget_finance" else 0,
                new_conflicts_count=len(session.conflicts) - conflicts_before,
            ),
            confidence_summary=confidence,
        )

    async def get_session(self, student_user_id: UUID) -> ConversationSessionResponse:
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None:
            session = _ConversationSessionState(session_id=uuid4(), student_id=profile.id)
            _SESSIONS_BY_STUDENT[profile.id] = session
            await self._bootstrap_requirements(session, student_user_id)
        return self._to_session_response(session)

    async def get_resume_checkpoint(self, student_user_id: UUID) -> ResumeCheckpointResponse:
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None:
            raise NotFoundException("Conversation session not found")

        return ResumeCheckpointResponse(
            session=self._to_session_response(session),
            checkpoint_summary=(
                f"You are in {session.current_stage} with focus on {session.active_domain}. "
                f"Confidence is {self._compute_confidence(session).global_confidence}%."
            ),
            open_tasks=self._open_tasks(session),
            last_assistant_prompt=session.last_assistant_prompt,
        )

    async def list_requirements(
        self, student_user_id: UUID
    ) -> ListConversationRequirementsResponse:
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None:
            return ListConversationRequirementsResponse(requirements=[])
        return ListConversationRequirementsResponse(
            requirements=[
                self._to_requirement_response(req) for req in session.requirements.values()
            ]
        )

    async def update_requirement(
        self,
        student_user_id: UUID,
        requirement_id: UUID,
        body: UpdateConversationRequirementRequest,
    ) -> ConversationRequirementResponse:
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None or requirement_id not in session.requirements:
            raise NotFoundException("Requirement not found")

        req = session.requirements[requirement_id]
        if body.status is not None:
            req.status = body.status
        if body.priority is not None:
            req.priority = body.priority
        if body.value is not None:
            req.value = body.value
        req.updated_at = datetime.now(UTC)

        return self._to_requirement_response(req)

    async def get_confidence_report(self, student_user_id: UUID) -> ConfidenceReportResponse:
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None:
            raise NotFoundException("Conversation session not found")

        global_summary = self._compute_confidence(session)
        domain_scores: list[DomainConfidenceResponse] = []
        for domain, required_fields in _REQUIRED_FIELDS_BY_DOMAIN.items():
            domain_requirements = [
                r
                for r in session.requirements.values()
                if r.domain == domain and r.status != "rejected"
            ]
            field_set = {r.field for r in domain_requirements}
            missing = [field for field in required_fields if field not in field_set]
            coverage = (
                100
                if not required_fields
                else round(((len(required_fields) - len(missing)) / len(required_fields)) * 100)
            )
            has_conflict = bool(session.conflicts)
            status: str = (
                "sufficient"
                if coverage >= 65 and not has_conflict
                else ("conflicting" if has_conflict else "partial")
            )
            domain_scores.append(
                DomainConfidenceResponse(
                    domain=domain,
                    status=status,  # type: ignore[arg-type]
                    confidence=max(0, min(100, coverage)),
                    missing_fields=missing,
                    conflicts=[c.reason for c in session.conflicts.values()],
                )
            )

        return ConfidenceReportResponse(
            global_confidence=global_summary.global_confidence,
            global_level=global_summary.global_level,
            domain_scores=domain_scores,
            blocking_issues=self._blocking_issues(session),
            computed_at=datetime.now(UTC),
        )

    async def get_shortlist_unlock(self, student_user_id: UUID) -> ShortlistUnlockResponse:
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None:
            raise NotFoundException("Conversation session not found")

        confidence = self._compute_confidence(session)
        report = await self.get_confidence_report(student_user_id)
        required_domains = {"budget_finance", "timeline_intake", "eligibility_compliance"}
        domain_ok = all(
            next((d.confidence for d in report.domain_scores if d.domain == domain), 0) >= 65
            for domain in required_domains
        )
        eligible = confidence.global_confidence >= 70 and domain_ok and len(session.conflicts) == 0
        reasons = []
        if confidence.global_confidence >= 70:
            reasons.append("global_confidence_passed")
        if domain_ok:
            reasons.append("domain_minimums_passed")
        if len(session.conflicts) == 0:
            reasons.append("no_blocking_conflicts")

        missing_required_fields: list[str] = []
        for domain in required_domains:
            domain_info = next((d for d in report.domain_scores if d.domain == domain), None)
            if domain_info:
                missing_required_fields.extend(domain_info.missing_fields)

        return ShortlistUnlockResponse(
            eligible=eligible,
            reasons=reasons,
            thresholds=ShortlistUnlockThresholdsResponse(global_min=70, domain_min=65),
            blocking_conflicts=[c.reason for c in session.conflicts.values()],
            missing_required_fields=missing_required_fields,
            recommended_next_actions=self._next_actions(session),
        )

    async def resolve_conflict(
        self, student_user_id: UUID, conflict_id: UUID, selected_resolution: str
    ) -> ResolveConflictResponse:
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None or conflict_id not in session.conflicts:
            raise NotFoundException("Conflict not found")

        conflict = session.conflicts[conflict_id]
        if selected_resolution not in conflict.resolution_options:
            raise ConflictException("Selected resolution is not in available options")

        conflict.selected_resolution = selected_resolution
        del session.conflicts[conflict_id]
        confidence = self._compute_confidence(session)
        return ResolveConflictResponse(
            conflict_id=conflict_id,
            resolved=True,
            selected_resolution=selected_resolution,
            updated_confidence=confidence,
        )

    async def _bootstrap_requirements(
        self, session: _ConversationSessionState, student_user_id: UUID
    ) -> None:
        profile = await self.student_service._get_student_profile(student_user_id)
        preferences = await self.student_service.get_preferences(profile.id)
        if preferences and preferences.budget_max is not None:
            self._upsert_requirement(
                session=session,
                domain="budget_finance",
                field="max_annual_tuition",
                value=preferences.budget_max,
                source="imported",
                evidence_turn_id=uuid4(),
            )
        if preferences and preferences.preferred_countries:
            self._upsert_requirement(
                session=session,
                domain="country_location",
                field="allowed_countries",
                value=preferences.preferred_countries,
                source="imported",
                evidence_turn_id=uuid4(),
            )
        if profile.goals_text:
            self._upsert_requirement(
                session=session,
                domain="career_outcome",
                field="primary_goal",
                value=profile.goals_text,
                source="imported",
                evidence_turn_id=uuid4(),
            )

    def _upsert_requirement(
        self,
        session: _ConversationSessionState,
        domain: ConversationDomain,
        field: str,
        value: object | None,
        source: str,
        evidence_turn_id: UUID,
    ) -> None:
        existing = next(
            (r for r in session.requirements.values() if r.domain == domain and r.field == field),
            None,
        )
        if existing:
            existing.value = value if value is not None else existing.value
            existing.source = source
            existing.updated_at = datetime.now(UTC)
            existing.evidence_turn_ids.append(evidence_turn_id)
            existing.confidence = min(100, existing.confidence + 5)
            return

        req = _RequirementState(
            requirement_id=uuid4(),
            domain=domain,
            field=field,
            value=value,
            priority="must_have",
            source=source,
            confidence=70 if value is not None else 45,
            status="draft",
            evidence_turn_ids=[evidence_turn_id],
        )
        session.requirements[req.requirement_id] = req

    def _pick_stage(self, turn_count: int) -> ConversationStage:
        if turn_count <= 2:
            return "understand_context"
        if turn_count <= 4:
            return "identify_issues"
        if turn_count <= 6:
            return "define_demand"
        if turn_count <= 9:
            return "translate_requirements"
        return "ready_for_shortlist"

    def _pick_domain(self, message: str) -> ConversationDomain:
        lower = message.lower()
        if "budget" in lower or "tuition" in lower or "scholarship" in lower:
            return "budget_finance"
        if "deadline" in lower or "intake" in lower or "timeline" in lower:
            return "timeline_intake"
        if "visa" in lower or "ielts" in lower or "toefl" in lower or "requirement" in lower:
            return "eligibility_compliance"
        if "country" in lower or "location" in lower or "city" in lower:
            return "country_location"
        if "career" in lower or "job" in lower or "outcome" in lower:
            return "career_outcome"
        if "gpa" in lower or "test" in lower or "score" in lower:
            return "academic_readiness"
        return "learning_preferences"

    async def _build_assistant_reply(
        self,
        domain: ConversationDomain,
        message: str,
        session: _ConversationSessionState,
    ) -> str:
        if settings.ai_mock_mode:
            return _TEMPLATE_REPLY.format(domain=domain)

        system_prompt = (
            "You are a warm, knowledgeable admissions counselor at UniPaith. "
            "Your role is to help students explore their study-abroad goals "
            "and collect the information needed to generate a great program shortlist. "
            "Be encouraging, concise (2-4 sentences), and naturally guide the student "
            "toward filling gaps in their profile. Never sound robotic or formulaic. "
            "Ask one clear follow-up question to keep the conversation moving."
        )

        collected = self._active_requirements_map(session)
        user_context = (
            f"Student message: {message}\n"
            f"Current domain: {domain}\n"
            f"Conversation stage: {session.current_stage}\n"
            f"Collected requirements so far: {collected}\n"
            f"Open tasks: {self._open_tasks(session)}"
        )

        try:
            return await self.llm.generate_reasoning(system_prompt, user_context)
        except Exception:
            logger.exception("LLM call failed in _build_assistant_reply, falling back to template")
            return _TEMPLATE_REPLY.format(domain=domain)

    @staticmethod
    def _active_requirements_map(
        session: _ConversationSessionState,
    ) -> dict[str, object]:
        return {
            req.field: req.value
            for req in session.requirements.values()
            if req.status != "rejected" and req.value is not None
        }

    def _extract_budget_hint(self, message: str) -> int | None:
        digits = "".join(ch if ch.isdigit() else " " for ch in message).split()
        for token in digits:
            if len(token) >= 4:
                return int(token)
        return None

    def _compute_confidence(self, session: _ConversationSessionState) -> ConfidenceSummaryResponse:
        requirements = list(session.requirements.values())
        if not requirements:
            return ConfidenceSummaryResponse(global_confidence=30, global_level="insufficient")

        coverage = round(sum(req.confidence for req in requirements) / len(requirements))
        conflict_penalty = 15 if session.conflicts else 0
        score = max(0, min(100, coverage - conflict_penalty))

        level: ConfidenceLevel
        if score < 40:
            level = "insufficient"
        elif score < 70:
            level = "provisional"
        elif score < 85:
            level = "recommendation_ready"
        else:
            level = "high_confidence"
        return ConfidenceSummaryResponse(global_confidence=score, global_level=level)

    def _to_session_response(
        self, session: _ConversationSessionState
    ) -> ConversationSessionResponse:
        return ConversationSessionResponse(
            session_id=session.session_id,
            student_id=session.student_id,
            current_stage=session.current_stage,
            active_domain=session.active_domain,
            turn_count=session.turn_count,
            last_updated_at=session.last_updated_at,
        )

    def _to_requirement_response(
        self, requirement: _RequirementState
    ) -> ConversationRequirementResponse:
        return ConversationRequirementResponse(
            requirement_id=requirement.requirement_id,
            domain=requirement.domain,
            field=requirement.field,
            value=deepcopy(requirement.value),
            priority=requirement.priority,  # type: ignore[arg-type]
            source=requirement.source,  # type: ignore[arg-type]
            confidence=requirement.confidence,
            status=requirement.status,  # type: ignore[arg-type]
            evidence_turn_ids=requirement.evidence_turn_ids,
            updated_at=requirement.updated_at,
        )

    def _next_actions(self, session: _ConversationSessionState) -> list[str]:
        actions = []
        missing = self._open_tasks(session)
        if missing:
            actions.extend([f"fill:{task}" for task in missing[:3]])
        if session.conflicts:
            actions.append("resolve_conflict")
        if not actions:
            actions.append("review_shortlist")
        return actions

    def _open_tasks(self, session: _ConversationSessionState) -> list[str]:
        open_tasks: list[str] = []
        existing = {
            (req.domain, req.field)
            for req in session.requirements.values()
            if req.status != "rejected"
        }
        for domain, fields in _REQUIRED_FIELDS_BY_DOMAIN.items():
            for field_name in fields:
                if (domain, field_name) not in existing:
                    open_tasks.append(f"{domain}.{field_name}")
        return open_tasks

    async def get_conversation_context_summary(self, student_user_id: UUID) -> str:
        """Build a text summary of collected requirements for recommendation context."""
        profile = await self.student_service._get_student_profile(student_user_id)
        session = _SESSIONS_BY_STUDENT.get(profile.id)
        if session is None:
            return ""
        active = self._active_requirements_map(session)
        return "; ".join(f"{k} = {v}" for k, v in active.items()) if active else ""

    def _blocking_issues(self, session: _ConversationSessionState) -> list[str]:
        issues = []
        issues.extend([c.reason for c in session.conflicts.values()])
        issues.extend([f"Missing required field: {task}" for task in self._open_tasks(session)])
        return issues
