"""
Interview service (Spec 33) — propose, invite, confirm, conduct, score,
complete for admissions interviews.

On propose the institution fans out one interview per applicant and, for each,
posts an ``interview_invite`` Inbox message to the student (the student
Calendar item is auto-derived from the interviews table by ``CalendarService``,
so no calendar write is needed here). Scoring feeds the per-applicant review
packet (Spec 32) via the denormalized ``Interview.recommendation`` + the
``interview_scores`` rows surfaced on the student's review workspace.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.interview_invite import (
    InterviewInviteInput,
    InterviewInviteResult,
    get_interview_invite_drafter,
)
from unipaith.ai.interview_score_prefill import (
    InterviewScorePrefillInput,
    InterviewScorePrefillResult,
    get_interview_score_prefill,
)
from unipaith.config import settings
from unipaith.core.exceptions import BadRequestException, NotFoundException
from unipaith.models.application import (
    Application,
    Interview,
    InterviewScore,
    Rubric,
)
from unipaith.models.engagement import Conversation, Message
from unipaith.models.institution import Institution, Program, Reviewer
from unipaith.models.student import StudentProfile
from unipaith.models.user import User
from unipaith.schemas.interview import ASYNC_INTERVIEW_TYPES
from unipaith.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

# Reason-code wiring shared with the institution inbox (Spec 29 §4).
_INVITE_REASON = "interview_invite"
_INVITE_ACTION = "interview_invite"
# Spec 33 §5 — live interviews need three or more proposed slots.
MIN_LIVE_PROPOSED_SLOTS = 3

# A sensible interviewing rubric (§6) used when an institution hasn't authored a
# custom one yet, so the Score modal always has criteria to score against.
DEFAULT_INTERVIEW_RUBRIC = {
    "id": None,
    "rubric_name": "Interview rubric (default)",
    "program_id": None,
    "rubric_kind": "interview",
    "criteria": [
        {
            "key": "communication",
            "label": "Communication",
            "description": "Clarity, articulation, and active listening.",
            "max": 5,
        },
        {
            "key": "motivation_fit",
            "label": "Motivation & Fit",
            "description": "Genuine interest in and fit for the program.",
            "max": 5,
        },
        {
            "key": "critical_thinking",
            "label": "Critical Thinking",
            "description": "Reasoning, problem-solving, and depth.",
            "max": 5,
        },
        {
            "key": "preparation",
            "label": "Preparation",
            "description": "Knowledge of the program and role.",
            "max": 5,
        },
    ],
}


_TYPE_LABELS = {
    "live": "live interview",
    "recorded_async": "recorded (async) interview",
    "portfolio_review": "portfolio review",
    "technical_assessment": "technical assessment",
    "third_party_platform": "interview",
    # legacy values still render
    "video": "video interview",
    "phone": "phone interview",
    "in_person": "in-person interview",
}


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _first_slot(proposed_times) -> datetime | None:
    if isinstance(proposed_times, list) and proposed_times:
        parsed = [_parse_iso(t) for t in proposed_times if isinstance(t, str)]
        parsed = [p for p in parsed if p is not None]
        return min(parsed) if parsed else None
    return None


class InterviewService:
    """Manages the interview lifecycle for the admissions pipeline."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notifications = NotificationService(db)

    # ------------------------------------------------------------------
    # Interview scheduling (institution)
    # ------------------------------------------------------------------

    async def propose_interview(
        self,
        application_id: UUID,
        interviewer_id: UUID,
        interview_type: str,
        proposed_times: list[str],
        duration_minutes: int = 30,
        location_or_link: str | None = None,
        async_window_end: str | None = None,
        notes_to_student: str | None = None,
    ) -> Interview:
        """Create a single interview proposal (no invite side effects).

        Kept for internal reuse / back-compat. Live interviews require at least
        one proposed time; async types (recorded_async / technical_assessment)
        require a submission window instead.
        """
        is_async = interview_type in ASYNC_INTERVIEW_TYPES
        if not is_async and len(proposed_times or []) < MIN_LIVE_PROPOSED_SLOTS:
            raise BadRequestException(
                f"Live interviews require at least {MIN_LIVE_PROPOSED_SLOTS} proposed time slots"
            )
        if is_async and not async_window_end:
            raise BadRequestException(
                "A submission window deadline is required for async interviews"
            )

        app_result = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        if not app_result.scalar_one_or_none():
            raise NotFoundException("Application not found")

        interview = Interview(
            application_id=application_id,
            interviewer_id=interviewer_id,
            interview_type=interview_type,
            proposed_times=proposed_times or [],
            duration_minutes=duration_minutes,
            location_or_link=location_or_link,
            async_window_end=_parse_iso(async_window_end),
            notes_to_student=notes_to_student,
            status="proposed",
        )
        self.db.add(interview)
        await self.db.flush()
        return interview

    async def propose_interviews(
        self,
        *,
        institution_id: UUID,
        actor_user_id: UUID,
        application_ids: list[UUID],
        interview_type: str,
        proposed_times: list[str],
        duration_minutes: int = 30,
        location_or_link: str | None = None,
        async_window_end: str | None = None,
        notes_to_student: str | None = None,
        interviewer_id: UUID | None = None,
        ai_draft_used: bool = False,
    ) -> list[Interview]:
        """Propose an interview to one or more applicants (Spec 33 §3 step 1-2).

        For each application: validates it belongs to ``institution_id``, creates
        the interview, and posts an ``interview_invite`` Inbox message to the
        student. The student's Calendar item is auto-derived (CalendarService),
        so it appears without an explicit write here.
        """
        if interview_type not in (
            "live",
            "recorded_async",
            "portfolio_review",
            "technical_assessment",
            "third_party_platform",
        ):
            raise BadRequestException(f"Unknown interview type: {interview_type}")

        reviewer = await self._resolve_reviewer(actor_user_id, institution_id, interviewer_id)

        created: list[Interview] = []
        for app_id in application_ids:
            row = await self.db.execute(
                select(Application, Program, Institution, StudentProfile)
                .join(Program, Application.program_id == Program.id)
                .join(Institution, Program.institution_id == Institution.id)
                .join(StudentProfile, Application.student_id == StudentProfile.id)
                .where(Application.id == app_id, Program.institution_id == institution_id)
            )
            found = row.first()
            if not found:
                raise NotFoundException(f"Application {app_id} not found for this institution")
            application, program, institution, profile = found

            interview = await self.propose_interview(
                application_id=app_id,
                interviewer_id=reviewer.id,
                interview_type=interview_type,
                proposed_times=proposed_times,
                duration_minutes=duration_minutes,
                location_or_link=location_or_link,
                async_window_end=async_window_end,
                notes_to_student=notes_to_student,
            )
            await self._send_interview_invite(
                actor_user_id=actor_user_id,
                interview=interview,
                application=application,
                program=program,
                institution=institution,
                profile=profile,
                ai_draft_used=ai_draft_used,
            )
            created.append(interview)
        return created

    async def _resolve_reviewer(
        self, user_id: UUID, institution_id: UUID, interviewer_id: UUID | None
    ) -> Reviewer:
        """Resolve the interviewer: an explicit reviewer id, the caller's own
        reviewer profile, or a freshly-created one for the caller."""
        if interviewer_id is not None:
            rv = await self.db.scalar(
                select(Reviewer).where(
                    Reviewer.id == interviewer_id,
                    Reviewer.institution_id == institution_id,
                )
            )
            if rv is None:
                raise NotFoundException("Interviewer not found for this institution")
            return rv

        rv = await self.db.scalar(
            select(Reviewer).where(
                Reviewer.user_id == user_id,
                Reviewer.institution_id == institution_id,
            )
        )
        if rv is not None:
            return rv

        # The acting admin isn't a reviewer yet — create a profile so the
        # interview has an interviewer (FK NOT NULL).
        name = await self.db.scalar(select(User.email).where(User.id == user_id))
        reviewer = Reviewer(
            institution_id=institution_id,
            user_id=user_id,
            name=(name or "Admissions").split("@")[0],
            department="Admissions",
        )
        self.db.add(reviewer)
        await self.db.flush()
        return reviewer

    async def _send_interview_invite(
        self,
        *,
        actor_user_id: UUID,
        interview: Interview,
        application: Application,
        program: Program,
        institution: Institution,
        profile: StudentProfile,
        ai_draft_used: bool,
    ) -> None:
        """Post the interview-invite Inbox message + notify the student.

        Best-effort: a messaging/notification failure must not 5xx the propose.
        """
        try:
            body = interview.notes_to_student or self._default_invite_body(
                interview.interview_type, program.program_name, interview
            )
            due = interview.async_window_end or _first_slot(interview.proposed_times)

            conv = await self.db.scalar(
                select(Conversation).where(
                    Conversation.student_id == application.student_id,
                    Conversation.institution_id == institution.id,
                    Conversation.application_id == application.id,
                )
            )
            now = datetime.now(UTC)
            if conv is None:
                conv = Conversation(
                    student_id=application.student_id,
                    institution_id=institution.id,
                    program_id=program.id,
                    application_id=application.id,
                    subject=f"Interview invitation — {program.program_name}",
                    status="open",
                    started_at=now,
                    last_message_at=now,
                )
                self.db.add(conv)
                await self.db.flush()

            conv.reason_code = _INVITE_REASON
            conv.action_label = _INVITE_ACTION
            conv.due_date = _aware(due)
            conv.waiting_on = "student"
            conv.last_message_at = now
            if conv.status in (None, "closed"):
                conv.status = "open"

            message = Message(
                conversation_id=conv.id,
                sender_type="institution",
                sender_id=actor_user_id,
                message_body=body,
                status="sent",
                ai_draft_used=bool(ai_draft_used),
            )
            self.db.add(message)
            await self.db.flush()

            student_user_id = await self.db.scalar(
                select(StudentProfile.user_id).where(StudentProfile.id == application.student_id)
            )
            if student_user_id:
                preview = body.strip()
                if len(preview) > 160:
                    preview = preview[:157] + "…"
                await self.notifications.notify(
                    student_user_id,
                    "interview_invites",
                    title=f"{institution.name}: interview invitation",
                    body=preview,
                    action_url=f"/s/manage?tab=messages&thread={conv.id}",
                    metadata={
                        "thread_id": str(conv.id),
                        "reason_code": _INVITE_REASON,
                        "interview_id": str(interview.id),
                    },
                )
        except Exception as e:  # noqa: BLE001 — invite side effects never 5xx propose
            logger.warning("interview invite side effects failed for %s: %s", interview.id, e)

    @staticmethod
    def _default_invite_body(
        interview_type: str | None, program_name: str, interview: Interview
    ) -> str:
        label = _TYPE_LABELS.get((interview_type or "").lower(), "interview")
        if (interview_type or "") in ASYNC_INTERVIEW_TYPES and interview.async_window_end:
            deadline = _aware(interview.async_window_end)
            when = deadline.strftime("%b %d, %Y") if deadline else "the deadline"
            return (
                f"You've been invited to complete a {label} for {program_name}. "
                f"Please submit your responses by {when}. Open this thread for details."
            )
        return (
            f"You've been invited to a {label} for {program_name}. "
            "Please review the proposed time(s) and confirm one, or request a reschedule."
        )

    # ------------------------------------------------------------------
    # Querying (institution)
    # ------------------------------------------------------------------

    async def list_application_interviews(self, application_id: UUID) -> list[Interview]:
        """List all interviews associated with an application."""
        result = await self.db.execute(
            select(Interview).where(Interview.application_id == application_id)
        )
        return list(result.scalars().all())

    async def list_institution_interviews(
        self, institution_id: UUID, status_filter: str | None = None
    ) -> list[Interview]:
        """List all interviews across all programs of an institution."""
        stmt = (
            select(Interview)
            .join(Application, Interview.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        if status_filter:
            stmt = stmt.where(Interview.status == status_filter)
        stmt = stmt.order_by(Interview.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_student_interviews(self, student_id: UUID) -> list[Interview]:
        """Get all interviews across all of a student's applications."""
        result = await self.db.execute(
            select(Interview)
            .join(Application, Interview.application_id == Application.id)
            .where(Application.student_id == student_id)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Rich response assembly (Spec 33 §7)
    # ------------------------------------------------------------------

    async def build_views(self, interviews: list[Interview]) -> list[dict]:
        """Enrich interviews with applicant name, program, scores, and the
        async-expiry flag for the institution table response."""
        if not interviews:
            return []
        iv_ids = [iv.id for iv in interviews]
        app_ids = {iv.application_id for iv in interviews}

        app_rows = await self.db.execute(
            select(Application, Program, StudentProfile, User)
            .join(Program, Application.program_id == Program.id)
            .join(StudentProfile, Application.student_id == StudentProfile.id)
            .join(User, StudentProfile.user_id == User.id, isouter=True)
            .where(Application.id.in_(app_ids))
        )
        ctx: dict[UUID, tuple] = {}
        for app, program, profile, user in app_rows.all():
            ctx[app.id] = (app, program, profile, user)

        score_rows = await self.db.execute(
            select(InterviewScore).where(InterviewScore.interview_id.in_(iv_ids))
        )
        scores_by_iv: dict[UUID, list[InterviewScore]] = {}
        for s in score_rows.scalars().all():
            scores_by_iv.setdefault(s.interview_id, []).append(s)

        now = datetime.now(UTC)
        views: list[dict] = []
        for iv in interviews:
            app, program, profile, user = ctx.get(iv.application_id, (None, None, None, None))
            name = self._display_name(profile, user)
            link = iv.location_or_link or ""
            is_link = link.startswith("http")
            scores = scores_by_iv.get(iv.id, [])
            scores_sorted = sorted(scores, key=lambda s: s.created_at or now)
            views.append(
                {
                    "id": iv.id,
                    "application_id": iv.application_id,
                    "applicant": {
                        "student_id": app.student_id if app else None,
                        "name": name,
                    },
                    "program": {
                        "id": program.id if program else None,
                        "name": program.program_name if program else "",
                    },
                    "interviewer_id": iv.interviewer_id,
                    "interview_type": iv.interview_type,
                    "status": iv.status,
                    "async_expired": self._is_async_expired(iv, now),
                    "proposed_times": iv.proposed_times or [],
                    "proposed_slots": iv.proposed_times or [],
                    "confirmed_time": iv.confirmed_time,
                    "scheduled_at": iv.confirmed_time,
                    "duration_minutes": iv.duration_minutes,
                    "location": None if is_link else (link or None),
                    "meeting_link": link if is_link else None,
                    "location_or_link": iv.location_or_link,
                    "async_window_end": iv.async_window_end,
                    "recording_url": iv.recording_url,
                    "notes_to_student": iv.notes_to_student,
                    "recommendation": iv.recommendation,
                    "scores": [
                        {
                            "interviewer_id": s.interviewer_id,
                            "criterion_scores": s.criterion_scores,
                            "total_weighted_score": (
                                float(s.total_weighted_score)
                                if s.total_weighted_score is not None
                                else None
                            ),
                            "notes": s.interviewer_notes,
                            "recommendation": s.recommendation,
                            "created_at": s.created_at,
                        }
                        for s in scores_sorted
                    ],
                    "created_at": iv.created_at,
                }
            )
        return views

    async def build_view(self, interview: Interview) -> dict:
        views = await self.build_views([interview])
        return views[0]

    @staticmethod
    def _display_name(profile: StudentProfile | None, user: User | None) -> str:
        if profile:
            parts = [profile.first_name or "", profile.last_name or ""]
            full = " ".join(p for p in parts if p).strip()
            if full:
                return full
            if profile.preferred_name:
                return profile.preferred_name
        if user and user.email:
            return user.email.split("@")[0]
        return "Applicant"

    # ------------------------------------------------------------------
    # Interview rubrics (Spec 33 §6)
    # ------------------------------------------------------------------

    async def get_interview_rubrics(
        self, institution_id: UUID, program_id: UUID | None = None
    ) -> list[dict]:
        """Return the institution's active interviewing rubrics (kind='interview'),
        normalized to ``{id, rubric_name, program_id, criteria:[{key,label,
        description,max}]}``. Always includes the built-in default so the Score
        modal has criteria even before any custom rubric exists."""
        stmt = select(Rubric).where(
            Rubric.institution_id == institution_id,
            Rubric.rubric_kind == "interview",
            Rubric.is_active.is_(True),
        )
        if program_id is not None:
            stmt = stmt.where((Rubric.program_id == program_id) | (Rubric.program_id.is_(None)))
        rows = await self.db.execute(stmt)
        rubrics = [self._normalize_rubric(r) for r in rows.scalars().all()]
        rubrics.append(dict(DEFAULT_INTERVIEW_RUBRIC))
        return rubrics

    @staticmethod
    def _normalize_rubric(rubric: Rubric) -> dict:
        criteria_out: list[dict] = []
        for c in rubric.criteria or []:
            if not isinstance(c, dict):
                continue
            name = c.get("label") or c.get("name") or "Criterion"
            key = c.get("key") or str(name).strip().lower().replace(" ", "_").replace("&", "and")
            criteria_out.append(
                {
                    "key": key,
                    "label": name,
                    "description": c.get("description") or "",
                    "max": c.get("max") or c.get("max_score") or 5,
                }
            )
        if not criteria_out:
            criteria_out = list(DEFAULT_INTERVIEW_RUBRIC["criteria"])
        return {
            "id": rubric.id,
            "rubric_name": rubric.rubric_name,
            "program_id": rubric.program_id,
            "rubric_kind": "interview",
            "criteria": criteria_out,
        }

    @staticmethod
    def _is_async_expired(iv: Interview, now: datetime) -> bool:
        if (iv.interview_type or "") not in ASYNC_INTERVIEW_TYPES:
            return False
        if iv.recording_url:
            return False
        if (iv.status or "") in ("completed", "cancelled"):
            return False
        end = _aware(iv.async_window_end)
        return end is not None and end < now

    # ------------------------------------------------------------------
    # Student actions
    # ------------------------------------------------------------------

    async def confirm_time(
        self, student_id: UUID, interview_id: UUID, confirmed_time: str | None = None
    ) -> Interview:
        """Student confirms one of the proposed interview times (or accepts an async window)."""
        interview = await self._get_student_interview(student_id, interview_id)

        if interview.status != "proposed":
            raise BadRequestException("Only proposed interviews can be confirmed")

        is_async = (interview.interview_type or "") in ASYNC_INTERVIEW_TYPES
        if is_async:
            interview.status = "confirmed"
            interview.confirmed_time = _aware(interview.async_window_end) or datetime.now(UTC)
        else:
            if not confirmed_time:
                raise BadRequestException("Select one of the proposed times")
            proposed: list[str] = interview.proposed_times or []
            if confirmed_time not in proposed:
                raise BadRequestException("Selected time is not among the proposed options")
            interview.status = "confirmed"
            interview.confirmed_time = _parse_iso(confirmed_time)

        app_result = await self.db.execute(
            select(Application).where(Application.id == interview.application_id)
        )
        app = app_result.scalar_one_or_none()
        if app and app.status in ("submitted", "under_review"):
            app.status = "interview"

        await self.db.flush()
        return interview

    async def decline_interview(self, student_id: UUID, interview_id: UUID) -> Interview:
        interview = await self._get_student_interview(student_id, interview_id)
        if interview.status != "proposed":
            raise BadRequestException("Only proposed interviews can be declined")
        interview.status = "cancelled"
        await self.db.flush()
        return interview

    # ------------------------------------------------------------------
    # Interviewer / institution actions
    # ------------------------------------------------------------------

    async def complete_interview(self, interview_id: UUID) -> Interview:
        """Mark an interview as completed (§3 step 4)."""
        interview = await self._get_interview(interview_id)
        if interview.status not in ("confirmed", "proposed"):
            raise BadRequestException(
                "Only confirmed or proposed interviews can be marked completed"
            )
        interview.status = "completed"
        await self.db.flush()
        return interview

    async def cancel_interview(self, interview_id: UUID) -> Interview:
        """Cancel an interview (§7 / §13). Notifies the student best-effort."""
        interview = await self._get_interview(interview_id)
        if interview.status in ("completed", "cancelled"):
            raise BadRequestException("Interview is already completed or cancelled")
        interview.status = "cancelled"
        await self.db.flush()
        await self._notify_status_change(interview, "Interview cancelled")
        return interview

    async def mark_no_show(self, interview_id: UUID) -> Interview:
        """Mark an interview as a no-show (§7)."""
        interview = await self._get_interview(interview_id)
        if interview.status in ("completed", "cancelled", "no_show"):
            raise BadRequestException("Interview cannot be marked no-show from its current status")
        interview.status = "no_show"
        await self.db.flush()
        return interview

    async def reschedule_interview(
        self,
        interview_id: UUID,
        *,
        actor_user_id: UUID,
        proposed_times: list[str] | None = None,
        async_window_end: str | None = None,
        duration_minutes: int | None = None,
        location_or_link: str | None = None,
    ) -> Interview:
        """Institution reschedules an interview (§13 "Reschedule").

        Resets the interview to ``proposed`` with new times (live) or a new
        window (async), clears the confirmed time, and re-sends the invite so
        the student re-confirms.
        """
        interview = await self._get_interview(interview_id)
        if interview.status in ("completed", "cancelled"):
            raise BadRequestException("Cannot reschedule a completed or cancelled interview")

        is_async = (interview.interview_type or "") in ASYNC_INTERVIEW_TYPES
        if is_async:
            if not async_window_end:
                raise BadRequestException("A new submission window deadline is required")
            interview.async_window_end = _parse_iso(async_window_end)
        else:
            if len(proposed_times or []) < MIN_LIVE_PROPOSED_SLOTS:
                raise BadRequestException(
                    "Live interviews require at least "
                    f"{MIN_LIVE_PROPOSED_SLOTS} proposed time slots"
                )
            interview.proposed_times = proposed_times

        if duration_minutes is not None:
            interview.duration_minutes = duration_minutes
        if location_or_link is not None:
            interview.location_or_link = location_or_link
        interview.confirmed_time = None
        interview.status = "proposed"
        await self.db.flush()

        # Re-send the invite so the student re-confirms the new time(s).
        ctx = await self._load_interview_context(interview.application_id)
        if ctx is not None:
            application, program, institution, profile = ctx
            await self._send_interview_invite(
                actor_user_id=actor_user_id,
                interview=interview,
                application=application,
                program=program,
                institution=institution,
                profile=profile,
                ai_draft_used=False,
            )
        return interview

    async def request_reschedule(self, student_id: UUID, interview_id: UUID) -> Interview:
        """Student requests a reschedule (§8 "Reschedule requested → notify staff").

        Keeps the interview but flags the thread back to the institution and
        notifies staff so they can re-propose times.
        """
        interview = await self._get_student_interview(student_id, interview_id)
        if interview.status not in ("proposed", "confirmed"):
            raise BadRequestException("Only proposed or confirmed interviews can be rescheduled")
        await self.db.flush()
        await self._notify_institution_reschedule(interview)
        return interview

    async def score_interview(
        self,
        interview_id: UUID,
        interviewer_id: UUID,
        criterion_scores: dict,
        total_weighted_score: float | Decimal,
        interviewer_notes: str | None = None,
        recommendation: str | None = None,
        rubric_id: UUID | None = None,
    ) -> InterviewScore:
        """Record scores for a conducted interview (§3 step 5 → feeds packet §32).

        Scoreable once the interview has at least been confirmed (covers async
        submissions and no-shows where review advances without a live meeting,
        §8) — not while still merely proposed or already cancelled.
        """
        interview = await self._get_interview(interview_id)

        if interview.status in ("proposed", "cancelled"):
            raise BadRequestException(
                "Interview must be confirmed, completed, or marked no-show before scoring"
            )

        score = InterviewScore(
            interview_id=interview_id,
            interviewer_id=interviewer_id,
            rubric_id=rubric_id,
            criterion_scores=criterion_scores,
            total_weighted_score=Decimal(str(total_weighted_score)),
            interviewer_notes=interviewer_notes,
            recommendation=recommendation,
        )
        self.db.add(score)
        # Denormalize the latest recommendation onto the interview so the §4 KPI
        # table + review packet read it without a join.
        if recommendation:
            interview.recommendation = recommendation
        # Scoring a still-confirmed interview implies it was conducted.
        if interview.status == "confirmed":
            interview.status = "completed"
        await self.db.flush()
        return score

    # ------------------------------------------------------------------
    # AI helpers (Spec 33 §9) — gated by ai_interview_v2_enabled; null on failure
    # ------------------------------------------------------------------

    async def draft_invite(
        self,
        *,
        institution_id: UUID,
        application_id: UUID,
        interview_type: str,
        proposed_times: list[str],
        async_window_end: str | None,
        duration_minutes: int | None,
        location_or_link: str | None,
    ) -> InterviewInviteResult | None:
        """Draft an invite message via the Haiku agent. Returns None when the
        flag is off or the agent fails — the UI omits the AI draft."""
        if not settings.ai_interview_v2_enabled:
            return None
        row = await self.db.execute(
            select(Application, Program, Institution, StudentProfile)
            .join(Program, Application.program_id == Program.id)
            .join(Institution, Program.institution_id == Institution.id)
            .join(StudentProfile, Application.student_id == StudentProfile.id)
            .where(Application.id == application_id, Program.institution_id == institution_id)
        )
        found = row.first()
        if not found:
            raise NotFoundException("Application not found for this institution")
        _app, program, institution, profile = found
        view = InterviewInviteInput(
            institution_name=institution.name,
            applicant_name=self._display_name(profile, None),
            program_name=program.program_name,
            interview_type=interview_type,
            proposed_slots=proposed_times or [],
            async_window_end=async_window_end,
            duration_minutes=duration_minutes,
            location_or_link=location_or_link,
        )
        return await get_interview_invite_drafter().draft(input_view=view, db=self.db)

    async def score_prefill(
        self,
        *,
        institution_id: UUID,
        interview_id: UUID,
        rubric_id: UUID | None,
        transcript_or_notes: str,
    ) -> InterviewScorePrefillResult | None:
        """Suggest rubric scores from a transcript via the Sonnet agent. Returns
        None when the flag is off, there's no transcript, or the agent fails."""
        if not settings.ai_interview_v2_enabled:
            return None
        row = await self.db.execute(
            select(Interview, Application, Program)
            .join(Application, Interview.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .where(Interview.id == interview_id, Program.institution_id == institution_id)
        )
        found = row.first()
        if not found:
            raise NotFoundException("Interview not found for this institution")
        interview, _app, program = found

        # Pick the rubric criteria to score against.
        criteria: list[dict] = []
        if rubric_id is not None:
            rubric = await self.db.scalar(
                select(Rubric).where(
                    Rubric.id == rubric_id, Rubric.institution_id == institution_id
                )
            )
            if rubric is not None:
                criteria = self._normalize_rubric(rubric)["criteria"]
        if not criteria:
            rubrics = await self.get_interview_rubrics(institution_id, program.id)
            criteria = rubrics[0]["criteria"] if rubrics else []

        view = InterviewScorePrefillInput(
            applicant_name="",
            program_name=program.program_name,
            interview_type=interview.interview_type or "live",
            rubric_criteria=criteria,
            transcript_or_notes=transcript_or_notes or (interview.notes_to_student or ""),
        )
        return await get_interview_score_prefill().prefill(input_view=view, db=self.db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _notify_status_change(self, interview: Interview, title: str) -> None:
        try:
            row = await self.db.execute(
                select(Application, Program, Institution, StudentProfile)
                .join(Program, Application.program_id == Program.id)
                .join(Institution, Program.institution_id == Institution.id)
                .join(StudentProfile, Application.student_id == StudentProfile.id)
                .where(Application.id == interview.application_id)
            )
            found = row.first()
            if not found:
                return
            _app, program, institution, profile = found
            if not profile.user_id:
                return
            await self.notifications.notify(
                profile.user_id,
                "interview_invites",
                title=f"{institution.name}: {title.lower()}",
                body=f"{title} for {program.program_name}.",
                action_url="/s/manage?tab=calendar",
                metadata={"interview_id": str(interview.id)},
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("interview status notify failed for %s: %s", interview.id, e)

    async def _load_interview_context(self, application_id: UUID):
        """Load (application, program, institution, profile) for an interview."""
        row = await self.db.execute(
            select(Application, Program, Institution, StudentProfile)
            .join(Program, Application.program_id == Program.id)
            .join(Institution, Program.institution_id == Institution.id)
            .join(StudentProfile, Application.student_id == StudentProfile.id)
            .where(Application.id == application_id)
        )
        return row.first()

    async def _notify_institution_reschedule(self, interview: Interview) -> None:
        """Notify the institution's admin that the student asked to reschedule (§8)."""
        try:
            ctx = await self._load_interview_context(interview.application_id)
            if ctx is None:
                return
            _app, program, institution, profile = ctx
            name = self._display_name(profile, None)
            if not institution.admin_user_id:
                return
            await self.notifications.notify(
                institution.admin_user_id,
                "interview_invites",
                title=f"{name}: reschedule requested",
                body=f"{name} asked to reschedule their {program.program_name} interview.",
                action_url="/i/interviews",
                metadata={"interview_id": str(interview.id)},
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("reschedule notify failed for %s: %s", interview.id, e)

    async def _get_interview(self, interview_id: UUID) -> Interview:
        result = await self.db.execute(select(Interview).where(Interview.id == interview_id))
        interview = result.scalar_one_or_none()
        if not interview:
            raise NotFoundException("Interview not found")
        return interview

    async def _get_student_interview(self, student_id: UUID, interview_id: UUID) -> Interview:
        result = await self.db.execute(
            select(Interview)
            .join(Application, Interview.application_id == Application.id)
            .where(
                Interview.id == interview_id,
                Application.student_id == student_id,
            )
        )
        interview = result.scalar_one_or_none()
        if not interview:
            raise NotFoundException("Interview not found for this student")
        return interview
