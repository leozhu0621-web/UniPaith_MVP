from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, time, timedelta
from typing import TypeVar
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.major_specific import StudentMajorSpecificSignals
from unipaith.models.my_space import MySpaceTaskState
from unipaith.models.strategy import StudentStrategy
from unipaith.models.student import RecommendationRequest, StudentDocument
from unipaith.models.user import User
from unipaith.models.workshops import WorkshopFeedbackRun
from unipaith.schemas.calendar import CalendarItem
from unipaith.schemas.inbox import ThreadSummary
from unipaith.schemas.my_space import (
    MySpaceMetric,
    MySpaceModuleItem,
    MySpaceOverview,
    MySpaceProvenance,
    MySpaceReadiness,
    MySpaceTask,
    MySpaceTaskPatch,
    MySpaceTaskStateResponse,
)
from unipaith.services.application_service import ApplicationService
from unipaith.services.calendar_service import CalendarService
from unipaith.services.inbox_service import InboxService
from unipaith.services.intake.intake_engine_service import IntakeEngineService
from unipaith.services.saved_list_service import SavedListService
from unipaith.services.student_service import StudentService

logger = logging.getLogger(__name__)

T = TypeVar("T")

URGENCY_RANK = {
    "focus_now": 0,
    "priority_window": 1,
    "gentle_attention": 2,
    "neutral": 3,
}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _due_date_to_datetime(value: date | datetime | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.combine(value, time(hour=23, minute=59), tzinfo=UTC)


def _urgency_for_due(due_at: datetime | None, *, now: datetime) -> str:
    if due_at is None:
        return "neutral"
    days = (due_at - now).total_seconds() / 86_400
    if days <= 3:
        return "focus_now"
    if days <= 14:
        return "priority_window"
    return "gentle_attention"


def _recommender_risk(due_at: datetime | None, *, now: datetime) -> tuple[str, str, str]:
    if due_at is None:
        return (
            "needs_deadline",
            "Letter requested; add a deadline so My Space can track risk.",
            "Recommendation deadline missing",
        )
    days = (due_at - now).total_seconds() / 86_400
    if days < 0:
        return (
            "overdue",
            "Letter is overdue. Nudge the recommender or prepare a backup.",
            "Recommendation overdue",
        )
    if days <= 3:
        return (
            "due_soon",
            "Letter is due soon. Nudge the recommender or confirm a backup.",
            "Recommendation due soon",
        )
    if days <= 14:
        return (
            "priority_window",
            "Letter is inside the priority window. Confirm they have what they need.",
            "Recommendation in priority window",
        )
    return (
        "requested",
        "Letter requested and not yet received.",
        "Letter not received",
    )


def _offer_decision_state(
    *,
    response: str | None,
    status: str | None,
    due_at: datetime | None,
    received_externally: bool,
    now: datetime,
) -> tuple[str, str, str | None, str]:
    external = "External offer recorded. " if received_externally else ""
    if status == "rescinded":
        return (
            "rescinded",
            f"{external}Offer was rescinded; keep the record for comparison history.",
            None,
            "neutral",
        )
    if response == "accepted":
        return (
            "accepted",
            f"{external}Offer accepted. Track deposit, conditions, and enrollment steps.",
            None,
            "neutral",
        )
    if response == "declined":
        return (
            "declined",
            f"{external}Offer declined. Keep cost and condition notes for your record.",
            None,
            "neutral",
        )
    if due_at is None:
        return (
            "needs_deadline",
            f"{external}Offer needs comparison; add a response deadline before you decide.",
            "Response deadline missing",
            "priority_window",
        )

    days = (due_at - now).total_seconds() / 86_400
    if days < 0:
        return (
            "overdue",
            f"{external}Response deadline has passed. Confirm whether the offer is still open.",
            "Offer response overdue",
            "focus_now",
        )
    if days <= 3:
        return (
            "due_soon",
            f"{external}Offer response is due soon. Compare cost, conditions, and fit now.",
            "Offer response due soon",
            "focus_now",
        )
    if days <= 14:
        return (
            "priority_window",
            f"{external}Offer is inside the decision window. Compare cost, conditions, and fit.",
            "Offer response window",
            "priority_window",
        )
    return (
        "compare_needed",
        f"{external}Offer needs comparison before response.",
        None,
        "gentle_attention",
    )


def _application_status_label(app: Application) -> str:
    status = app.status or "draft"
    decision_state = getattr(app, "decision_state", None)
    if status == "decision_made":
        return str(decision_state or app.decision or "decision_made")
    if status == "interview":
        return "interview"
    if status == "under_review":
        return "under_review"
    if status == "submitted":
        return "submitted"
    if app.readiness_pct is not None and app.readiness_pct >= 100:
        return "ready_to_submit"
    if app.readiness_pct:
        return "in_progress"
    return status


def _program_label(app: Application) -> str:
    program = getattr(app, "program", None)
    return getattr(program, "program_name", None) or "Application"


def _institution_label(app: Application) -> str | None:
    program = getattr(app, "program", None)
    return getattr(program, "institution_name", None)


def _application_route(app_id: UUID, tab: str | None = None) -> str:
    suffix = f"?tab={tab}" if tab else ""
    return f"/s/applications/{app_id}{suffix}"


def _uni_route(intent: str, task_key: str, destination: str | None = None) -> str:
    parts = [
        f"intent={quote(intent)}",
        f"source_task={quote(task_key)}",
        "return_to=%2Fs%2Fspace",
    ]
    if destination:
        parts.append(f"artifact_destination={quote(destination)}")
    return "/s?" + "&".join(parts)


def _provenance(
    source: str,
    label: str,
    *,
    href: str | None = None,
    confidence: int | None = None,
    updated_at: datetime | None = None,
) -> list[MySpaceProvenance]:
    return [
        MySpaceProvenance(
            source=source,
            label=label,
            href=href,
            confidence=confidence,
            updated_at=updated_at,
        )
    ]


class MySpaceService:
    """Server-composed My Space operating model.

    Domain ownership remains with the existing services. This layer only
    reconciles those domains into release-facing priorities, provenance, and
    partial-failure-safe module rows for the My Space overview.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_issues: list[MySpaceProvenance] = []

    async def get_overview(self, user: User) -> MySpaceOverview:
        now = _utcnow()
        profile = await StudentService(self.db)._get_student_profile(user.id)
        student_id = profile.id

        apps = await self._safe("applications", lambda: self._applications(student_id), [])
        saved = await self._safe("saved targets", lambda: self._saved(student_id), [])
        calendar = await self._safe("calendar", lambda: self._calendar(student_id, now), [])
        recs = await self._safe("recommenders", lambda: self._recommenders(student_id), [])
        threads = await self._safe("messages", lambda: self._threads(user.id), [])
        workshop_runs = await self._safe(
            "workshop feedback", lambda: self._workshop_runs(student_id), []
        )
        documents = await self._safe("documents", lambda: self._documents(student_id), [])
        strategy = await self._safe("strategy", lambda: self._strategy(student_id), None)
        major_rows = await self._safe("major evidence", lambda: self._major_rows(student_id), [])
        completeness = await self._safe(
            "profile readiness", lambda: self._completeness(student_id), {}
        )
        match_ready = await self._safe("match readiness", lambda: self._match_ready(student_id), {})
        clarifications = await self._safe(
            "clarifications",
            lambda: IntakeEngineService(self.db).list_clarifications(student_id),
            [],
        )

        tasks = self._build_tasks(
            apps=apps,
            saved=saved,
            calendar=calendar,
            recs=recs,
            threads=threads,
            documents=documents,
            strategy=strategy,
            clarifications=clarifications,
            now=now,
        )
        tasks = await self._apply_task_states(student_id, tasks, now=now)

        display_name = (
            profile.preferred_name
            or " ".join(p for p in (profile.first_name, profile.last_name) if p).strip()
            or None
        )

        return MySpaceOverview(
            generated_at=now,
            student={
                "id": student_id,
                "first_name": profile.first_name,
                "display_name": display_name,
            },
            readiness=self._readiness(
                completeness=completeness,
                match_ready=match_ready,
                apps=apps,
                major_rows=major_rows,
            ),
            tasks=tasks,
            pipeline=self._pipeline(apps=apps, saved=saved),
            evidence_gaps=[
                t for t in tasks if t.category in {"profile", "clarification", "import"}
            ],
            deadlines=self._deadline_items(calendar, now=now),
            waiting_on=self._waiting_on_items(recs=recs, threads=threads, now=now),
            application_portfolio=self._application_items(apps=apps, now=now),
            messages=self._message_items(threads),
            feedback=self._feedback_items(workshop_runs),
            strategy=self._strategy_item(strategy),
            prep_readiness=self._prep_readiness(
                recs=recs, workshop_runs=workshop_runs, documents=documents
            ),
            offers=self._offer_items(apps=apps, now=now),
            saved_targets=self._saved_items(saved),
            import_status=self._import_status(documents=documents, clarifications=clarifications),
            recent_changes=self._recent_changes(
                apps=apps,
                saved=saved,
                documents=documents,
                workshop_runs=workshop_runs,
                now=now,
            ),
            access_issues=self.access_issues,
        )

    async def patch_task_state(
        self,
        user: User,
        task_key: str,
        body: MySpaceTaskPatch,
    ) -> MySpaceTaskStateResponse:
        profile = await StudentService(self.db)._get_student_profile(user.id)
        state = await self.db.scalar(
            select(MySpaceTaskState).where(
                MySpaceTaskState.student_id == profile.id,
                MySpaceTaskState.task_key == task_key,
            )
        )
        if state is None:
            state = MySpaceTaskState(student_id=profile.id, task_key=task_key)
            self.db.add(state)
            await self.db.flush()
        if "dismissed" in body.model_fields_set:
            state.dismissed = body.dismissed
        if "snoozed_until" in body.model_fields_set:
            state.snoozed_until = body.snoozed_until
            if body.snoozed_until is not None and body.snoozed_until <= _utcnow():
                state.snoozed_until = None
        await self.db.flush()
        return MySpaceTaskStateResponse.model_validate(state)

    async def _safe(
        self,
        label: str,
        loader: Callable[[], Awaitable[T]],
        default: T,
    ) -> T:
        try:
            return await loader()
        except Exception:  # noqa: BLE001 - overview stays partially useful
            logger.exception("my-space dependency failed: %s", label)
            self.access_issues.append(
                MySpaceProvenance(
                    source="partial_failure",
                    label=f"{label} unavailable",
                    confidence=0,
                    updated_at=_utcnow(),
                )
            )
            return default

    async def _applications(self, student_id: UUID) -> list[Application]:
        return await ApplicationService(self.db).list_student_applications(student_id)

    async def _saved(self, student_id: UUID):  # noqa: ANN202 - schema lives in saved_list.py
        return await SavedListService(self.db).list_saved_enriched(student_id)

    async def _calendar(self, student_id: UUID, now: datetime) -> list[CalendarItem]:
        return await CalendarService(self.db).get_calendar(
            student_id, now, now + timedelta(days=90)
        )

    async def _recommenders(self, student_id: UUID) -> list[RecommendationRequest]:
        rows = await self.db.scalars(
            select(RecommendationRequest)
            .where(RecommendationRequest.student_id == student_id)
            .order_by(RecommendationRequest.created_at.desc())
        )
        return list(rows.all())

    async def _threads(self, user_id: UUID) -> list[ThreadSummary]:
        return await InboxService(self.db).list_threads(user_id, sort="urgent")

    async def _workshop_runs(self, student_id: UUID) -> list[WorkshopFeedbackRun]:
        rows = await self.db.scalars(
            select(WorkshopFeedbackRun)
            .where(WorkshopFeedbackRun.student_id == student_id)
            .order_by(desc(WorkshopFeedbackRun.created_at))
            .limit(8)
        )
        return list(rows.all())

    async def _documents(self, student_id: UUID) -> list[StudentDocument]:
        rows = await self.db.scalars(
            select(StudentDocument)
            .where(StudentDocument.student_id == student_id)
            .order_by(desc(StudentDocument.uploaded_at))
        )
        return list(rows.all())

    async def _strategy(self, student_id: UUID) -> StudentStrategy | None:
        return await self.db.scalar(
            select(StudentStrategy).where(
                StudentStrategy.student_id == student_id,
                StudentStrategy.status == "active",
            )
        )

    async def _major_rows(self, student_id: UUID) -> list[StudentMajorSpecificSignals]:
        rows = await self.db.scalars(
            select(StudentMajorSpecificSignals).where(
                StudentMajorSpecificSignals.student_id == student_id
            )
        )
        return list(rows.all())

    async def _completeness(self, student_id: UUID) -> dict:
        return await IntakeEngineService(self.db).get_completeness(student_id)

    async def _match_ready(self, student_id: UUID) -> dict:
        return await IntakeEngineService(self.db).get_match_ready(student_id)

    def _readiness(
        self,
        *,
        completeness: dict,
        match_ready: dict,
        apps: list[Application],
        major_rows: list[StudentMajorSpecificSignals],
    ) -> list[MySpaceReadiness]:
        profile_pct = int(completeness.get("overall_profile_completeness_pct") or 0)
        match_missing = int(
            match_ready.get("missing_count") or len(match_ready.get("missing") or [])
        )
        app_readiness = [a.readiness_pct for a in apps if a.readiness_pct is not None]
        apply_pct = round(sum(app_readiness) / len(app_readiness)) if app_readiness else None
        major_conf = (
            round(sum(r.confidence for r in major_rows) / len(major_rows)) if major_rows else None
        )

        return [
            MySpaceReadiness(
                key="profile",
                label="Profile readiness",
                status="ready" if profile_pct >= 80 else "needs_attention",
                pct=profile_pct,
                detail=(
                    f"{profile_pct}% of profile signals are present."
                    if profile_pct
                    else "Start by importing materials or answering Uni's intake questions."
                ),
                route="/s/profile",
                provenance=_provenance(
                    "adaptive_intake",
                    "Profile signal coverage",
                    href="/s/profile?tab=analytics",
                    confidence=85,
                ),
            ),
            MySpaceReadiness(
                key="match",
                label="Match-ready",
                status="ready" if bool(match_ready.get("match_ready")) else "blocked",
                pct=int(match_ready.get("completeness_pct") or profile_pct or 0),
                detail=(
                    "Your core matching inputs are usable."
                    if bool(match_ready.get("match_ready"))
                    else f"{match_missing} required matching signals still need attention."
                ),
                route="/s/explore",
                provenance=_provenance("adaptive_intake", "Match-ready gate", confidence=90),
            ),
            MySpaceReadiness(
                key="apply",
                label="Apply-ready",
                status=(
                    "unknown"
                    if apply_pct is None
                    else "ready"
                    if apply_pct >= 85
                    else "needs_attention"
                ),
                pct=apply_pct,
                detail=(
                    "Start an application to see program-specific readiness."
                    if apply_pct is None
                    else f"Average readiness across active applications is {apply_pct}%."
                ),
                route="/s/applications",
                provenance=_provenance("applications", "Application readiness", confidence=80),
            ),
            MySpaceReadiness(
                key="major_evidence",
                label="Major evidence",
                status=(
                    "unknown"
                    if not major_rows
                    else "ready"
                    if (major_conf or 0) >= 70
                    else "needs_attention"
                ),
                pct=major_conf,
                detail=(
                    "Major-specific evidence has not been mapped yet."
                    if not major_rows
                    else f"{len(major_rows)} major track record(s) mapped."
                ),
                route="/s/prep?tab=prompts",
                provenance=_provenance(
                    "prompt_library", "Major-specific readiness", confidence=major_conf
                ),
            ),
        ]

    def _pipeline(self, *, apps: list[Application], saved: list) -> list[MySpaceMetric]:
        drafts = [a for a in apps if a.status == "draft"]
        submitted = [a for a in apps if a.status in {"submitted", "under_review", "interview"}]
        offers = [
            a
            for a in apps
            if getattr(a, "offer", None) is not None
            or a.decision in {"admitted", "accepted", "conditional_admission"}
        ]
        return [
            MySpaceMetric(key="saved", label="Saved", value=len(saved), route="/s/saved"),
            MySpaceMetric(
                key="drafts",
                label="In progress",
                value=len(drafts),
                route="/s/applications?status=in_progress",
            ),
            MySpaceMetric(
                key="submitted",
                label="Submitted",
                value=len(submitted),
                route="/s/applications?status=submitted",
            ),
            MySpaceMetric(
                key="offers",
                label="Offers",
                value=len(offers),
                route="/s/applications?tab=offers",
                status="ready" if offers else None,
            ),
        ]

    def _build_tasks(
        self,
        *,
        apps: list[Application],
        saved: list,
        calendar: list[CalendarItem],
        recs: list[RecommendationRequest],
        threads: list[ThreadSummary],
        documents: list[StudentDocument],
        strategy: StudentStrategy | None,
        clarifications: list[dict],
        now: datetime,
    ) -> list[MySpaceTask]:
        tasks: list[MySpaceTask] = []

        for item in calendar:
            if item.status in {"completed", "cancelled"}:
                continue
            due_at = item.start_at
            urgency = _urgency_for_due(due_at, now=now)
            if urgency not in {"focus_now", "priority_window"} and item.type != "deposit_deadline":
                continue
            key = f"deadline:{item.id}"
            tasks.append(
                MySpaceTask(
                    key=key,
                    title=item.title,
                    description=item.subtitle or item.institution_name or "Calendar item",
                    owner="student",
                    urgency=urgency,
                    category="deadline",
                    cta_label="Open calendar",
                    cta_route=item.link or "/s/calendar",
                    due_at=due_at,
                    blocker="Due soon" if urgency == "focus_now" else None,
                    provenance=_provenance(
                        "calendar", item.type, href="/s/calendar", confidence=95
                    ),
                )
            )

        for app in apps:
            offer = getattr(app, "offer", None)
            if offer is not None and not getattr(offer, "student_response", None):
                due_at = _due_date_to_datetime(getattr(offer, "response_deadline", None))
                offer_status, offer_description, offer_blocker, offer_urgency = (
                    _offer_decision_state(
                        response=getattr(offer, "student_response", None),
                        status=getattr(offer, "status", None),
                        due_at=due_at,
                        received_externally=bool(getattr(offer, "received_externally", False)),
                        now=now,
                    )
                )
                key = f"offer:{offer.id}:respond"
                tasks.append(
                    MySpaceTask(
                        key=key,
                        title=f"Review offer from {_program_label(app)}",
                        description=offer_description,
                        owner="student",
                        urgency=offer_urgency,
                        category="offer",
                        cta_label="Compare offers",
                        cta_route="/s/applications?tab=offers",
                        due_at=due_at,
                        blocker=offer_blocker,
                        provenance=_provenance(
                            "offer_letters",
                            offer_status,
                            href=_application_route(app.id, "offer"),
                            confidence=90,
                        ),
                    )
                )

            missing = self._missing_items(app)
            if app.status == "draft" and missing:
                key = f"application:{app.id}:missing"
                tasks.append(
                    MySpaceTask(
                        key=key,
                        title=f"Complete {_program_label(app)} application",
                        description=f"Missing: {', '.join(missing[:3])}",
                        owner="student",
                        urgency="priority_window",
                        category="application",
                        cta_label="Open application",
                        cta_route=_application_route(app.id),
                        missing_field=missing[0],
                        blocker="Missing application item",
                        provenance=_provenance(
                            "applications",
                            "Application readiness",
                            href=_application_route(app.id),
                            confidence=80,
                            updated_at=app.updated_at,
                        ),
                    )
                )

        for rec in recs:
            if rec.status not in {"requested", "draft"}:
                continue
            due_at = _due_date_to_datetime(rec.due_date)
            key = f"recommender:{rec.id}"
            requested = rec.status == "requested"
            risk_status, risk_description, risk_blocker = _recommender_risk(due_at, now=now)
            tasks.append(
                MySpaceTask(
                    key=key,
                    title=f"Recommendation from {rec.recommender_name}",
                    description=(
                        risk_description
                        if requested
                        else "Draft a request before this application needs it."
                    ),
                    owner="recommender" if requested else "student",
                    urgency=_urgency_for_due(due_at, now=now) if due_at else "gentle_attention",
                    category="recommender",
                    cta_label="Open recommenders",
                    cta_route="/s/prep?tab=recommenders",
                    due_at=due_at,
                    blocker=risk_blocker if requested else "Request not sent",
                    provenance=_provenance(
                        "recommendation_requests",
                        risk_status if requested else rec.status,
                        href="/s/prep?tab=recommenders",
                        confidence=90,
                        updated_at=rec.updated_at,
                    ),
                )
            )

        for thread in threads:
            if thread.waiting_on == "student" or thread.unread:
                key = f"message:{thread.id}"
                tasks.append(
                    MySpaceTask(
                        key=key,
                        title=thread.subject or "Message needs attention",
                        description=thread.application.institution_name
                        or thread.application.program_name
                        or "Admissions message",
                        owner="student",
                        urgency=_urgency_for_due(thread.due_date, now=now)
                        if thread.due_date
                        else "priority_window",
                        category="message",
                        cta_label="Open message",
                        cta_route=f"/s/messages?thread={thread.id}",
                        due_at=thread.due_date,
                        blocker=thread.action_label,
                        provenance=_provenance(
                            "messages",
                            thread.action_label or "thread",
                            href=f"/s/messages?thread={thread.id}",
                            confidence=90,
                            updated_at=thread.last_message_at,
                        ),
                    )
                )

        for c in clarifications[:5]:
            key = f"clarification:{c['id']}"
            tasks.append(
                MySpaceTask(
                    key=key,
                    title=f"Confirm {c['label']}",
                    description=c.get("question") or "Uni needs this before trusting the signal.",
                    owner="student",
                    urgency="priority_window",
                    category="clarification",
                    cta_label="Clarify in Uni",
                    cta_route=_uni_route("clarification", key, "clarification"),
                    missing_field=c.get("signal_name"),
                    blocker="Low-confidence extracted signal",
                    provenance=_provenance(
                        "adaptive_intake",
                        "Clarification",
                        href="/s/import",
                        confidence=c.get("confidence"),
                    ),
                )
            )

        if strategy is None:
            key = "strategy:create"
            tasks.append(
                MySpaceTask(
                    key=key,
                    title="Create your admissions strategy",
                    description=(
                        "Turn profile signals into a career, degree, academic, financial, "
                        "and geographic plan."
                    ),
                    owner="student",
                    urgency="gentle_attention",
                    category="strategy",
                    cta_label="Draft with Uni",
                    cta_route=_uni_route("strategy", key, "strategy_draft"),
                    blocker="No active strategy",
                    provenance=_provenance("strategy", "No active living document", confidence=80),
                )
            )

        if not documents:
            key = "import:first-material"
            tasks.append(
                MySpaceTask(
                    key=key,
                    title="Import a transcript, resume, or draft",
                    description=(
                        "Imported materials reduce manual entry and create specific "
                        "clarification tasks."
                    ),
                    owner="student",
                    urgency="gentle_attention",
                    category="import",
                    cta_label="Import material",
                    cta_route="/s/import",
                    blocker="No imported materials",
                    provenance=_provenance("documents", "No uploaded materials", confidence=90),
                )
            )

        if not saved and not apps:
            key = "saved:find-targets"
            tasks.append(
                MySpaceTask(
                    key=key,
                    title="Save programs to build your pipeline",
                    description=(
                        "Saved programs become compare rows, deadlines, and application "
                        "planning tasks."
                    ),
                    owner="student",
                    urgency="gentle_attention",
                    category="saved",
                    cta_label="Browse matches",
                    cta_route="/s/explore",
                    provenance=_provenance("saved_lists", "No saved programs", confidence=95),
                    dismissible=False,
                )
            )

        if not tasks:
            key = "my-space:open-uni"
            tasks.append(
                MySpaceTask(
                    key=key,
                    title="Ask Uni what to do next",
                    description=(
                        "Use Uni to inspect your current plan, explain risks, or create "
                        "the next artifact."
                    ),
                    owner="student",
                    urgency="neutral",
                    category="uni",
                    cta_label="Open Uni",
                    cta_route=_uni_route("next_best_action", key),
                    provenance=_provenance("my_space", "No blocking tasks", confidence=70),
                    dismissible=False,
                )
            )
        return tasks

    def _missing_items(self, app: Application) -> list[str]:
        raw = app.missing_items or {}
        items: list[str] = []
        if isinstance(raw, dict):
            value = raw.get("items") or raw.get("missing") or raw.get("fields")
            if isinstance(value, list):
                items = [str(v) for v in value if v]
        if not items and (app.readiness_pct is not None and app.readiness_pct < 100):
            items.append("readiness gap")
        if not items and app.completeness_status in {"incomplete", "pending_verification"}:
            items.append(app.completeness_status.replace("_", " "))
        return items

    async def _apply_task_states(
        self,
        student_id: UUID,
        tasks: list[MySpaceTask],
        *,
        now: datetime,
    ) -> list[MySpaceTask]:
        rows = await self.db.scalars(
            select(MySpaceTaskState).where(MySpaceTaskState.student_id == student_id)
        )
        states = {r.task_key: r for r in rows.all()}
        for task in tasks:
            state = states.get(task.key)
            if state is not None:
                task.dismissed = state.dismissed
                task.snoozed_until = state.snoozed_until
            task.active = not task.dismissed and (
                task.snoozed_until is None or task.snoozed_until <= now
            )
        far = datetime.max.replace(tzinfo=UTC)
        return sorted(
            tasks,
            key=lambda t: (
                0 if t.active else 1,
                URGENCY_RANK.get(t.urgency, 9),
                t.due_at or far,
                t.key,
            ),
        )

    def _deadline_items(
        self, calendar: list[CalendarItem], *, now: datetime
    ) -> list[MySpaceModuleItem]:
        rows: list[MySpaceModuleItem] = []
        for item in calendar:
            if item.status in {"completed", "cancelled"}:
                continue
            rows.append(
                MySpaceModuleItem(
                    key=f"deadline:{item.id}",
                    title=item.title,
                    description=item.subtitle
                    or item.institution_name
                    or item.type.replace("_", " "),
                    route=item.link or "/s/calendar",
                    owner="student",
                    urgency=_urgency_for_due(item.start_at, now=now),
                    status=item.status,
                    due_at=item.start_at,
                    provenance=_provenance(
                        "calendar", item.type, href="/s/calendar", confidence=95
                    ),
                )
            )
        return sorted(rows, key=lambda r: r.due_at or datetime.max.replace(tzinfo=UTC))[:6]

    def _application_items(
        self,
        *,
        apps: list[Application],
        now: datetime,
    ) -> list[MySpaceModuleItem]:
        rows: list[MySpaceModuleItem] = []
        for app in apps:
            status = _application_status_label(app)
            due_at = _due_date_to_datetime(getattr(app.program, "application_deadline", None))
            offer = getattr(app, "offer", None)
            offer_due_at = _due_date_to_datetime(getattr(offer, "response_deadline", None))
            route = (
                _application_route(app.id, "offer")
                if offer is not None
                else _application_route(app.id)
            )
            owner = "student"
            urgency = _urgency_for_due(due_at, now=now)
            missing = self._missing_items(app)
            readiness = app.readiness_pct
            institution = _institution_label(app)
            context = f" at {institution}" if institution else ""

            if offer is not None and not getattr(offer, "student_response", None):
                offer_status, offer_description, _offer_blocker, offer_urgency = (
                    _offer_decision_state(
                        response=getattr(offer, "student_response", None),
                        status=getattr(offer, "status", None),
                        due_at=offer_due_at,
                        received_externally=bool(getattr(offer, "received_externally", False)),
                        now=now,
                    )
                )
                status = f"offer_{offer_status}"
                description = offer_description
                due_at = offer_due_at
                urgency = offer_urgency
            elif app.status == "draft" and missing:
                missing_text = f"Missing {', '.join(missing[:3])}."
                description = (
                    f"{missing_text} {readiness}% ready." if readiness is not None else missing_text
                )
                urgency = _urgency_for_due(due_at, now=now)
                if urgency == "neutral":
                    urgency = "priority_window"
            elif app.status == "draft" and readiness is not None and readiness >= 100:
                description = "Ready to submit. Do a final review before the deadline."
                urgency = _urgency_for_due(due_at, now=now)
                if urgency == "neutral":
                    urgency = "priority_window"
            elif app.status == "submitted":
                description = f"Submitted{context}; admissions office owns the next review step."
                owner = "institution"
                urgency = "neutral"
            elif app.status == "under_review":
                description = f"Under review{context}; watch messages for follow-up requests."
                owner = "institution"
                urgency = "gentle_attention"
            elif app.status == "interview":
                description = f"Interview stage{context}; keep prep and scheduling visible."
                urgency = "priority_window"
            elif app.status == "decision_made":
                decision = (
                    getattr(app, "decision_state", None) or app.decision or "decision received"
                )
                description = f"Decision: {str(decision).replace('_', ' ')}."
                urgency = (
                    "gentle_attention"
                    if decision in {"waitlisted", "conditional_admission"}
                    else "neutral"
                )
                owner = "student" if decision in {"waitlisted", "accepted"} else "institution"
            else:
                description = f"{status.replace('_', ' ').title()}{context}."

            rows.append(
                MySpaceModuleItem(
                    key=f"application:{app.id}",
                    title=_program_label(app),
                    description=description,
                    route=route,
                    owner=owner,
                    urgency=urgency,
                    status=status,
                    due_at=due_at,
                    provenance=_provenance(
                        "applications",
                        status,
                        href=route,
                        confidence=85 if readiness is not None else 75,
                        updated_at=app.updated_at,
                    ),
                )
            )
        far = datetime.max.replace(tzinfo=UTC)
        return sorted(
            rows,
            key=lambda r: (
                URGENCY_RANK.get(r.urgency, 9),
                r.due_at or far,
                r.title,
            ),
        )[:6]

    def _waiting_on_items(
        self,
        *,
        recs: list[RecommendationRequest],
        threads: list[ThreadSummary],
        now: datetime,
    ) -> list[MySpaceModuleItem]:
        rows: list[MySpaceModuleItem] = []
        for rec in recs:
            if rec.status == "requested":
                due_at = _due_date_to_datetime(rec.due_date)
                risk_status, risk_description, _risk_blocker = _recommender_risk(due_at, now=now)
                rows.append(
                    MySpaceModuleItem(
                        key=f"recommender:{rec.id}",
                        title=f"{rec.recommender_name} recommendation",
                        description=risk_description,
                        route="/s/prep?tab=recommenders",
                        owner="recommender",
                        urgency=_urgency_for_due(due_at, now=now) if due_at else "gentle_attention",
                        status=risk_status,
                        due_at=due_at,
                        provenance=_provenance(
                            "recommendation_requests", risk_status, confidence=90
                        ),
                    )
                )
        for thread in threads:
            if thread.waiting_on == "school":
                rows.append(
                    MySpaceModuleItem(
                        key=f"thread:{thread.id}",
                        title=thread.subject or "Waiting on admissions",
                        description=thread.application.institution_name
                        or thread.application.program_name
                        or "Admissions office",
                        route=f"/s/messages?thread={thread.id}",
                        owner="institution",
                        urgency="gentle_attention",
                        status=thread.action_label,
                        due_at=thread.due_date,
                        provenance=_provenance(
                            "messages", "Thread waiting on school", confidence=85
                        ),
                    )
                )
        return sorted(rows, key=lambda r: r.due_at or datetime.max.replace(tzinfo=UTC))[:5]

    def _message_items(self, threads: list[ThreadSummary]) -> list[MySpaceModuleItem]:
        return [
            MySpaceModuleItem(
                key=f"message:{t.id}",
                title=t.subject or "Admissions message",
                description=t.application.institution_name
                or t.application.program_name
                or "Message thread",
                route=f"/s/messages?thread={t.id}",
                owner="student" if t.waiting_on == "student" else "institution",
                urgency="priority_window" if t.unread or t.waiting_on == "student" else "neutral",
                status=t.action_label or ("unread" if t.unread else t.waiting_on),
                due_at=t.due_date,
                provenance=_provenance(
                    "messages",
                    t.action_label or "thread",
                    confidence=85,
                    updated_at=t.last_message_at,
                ),
            )
            for t in threads[:5]
        ]

    def _feedback_items(self, runs: list[WorkshopFeedbackRun]) -> list[MySpaceModuleItem]:
        labels = {"essay": "Essay", "interview": "Interview", "test": "Test"}
        return [
            MySpaceModuleItem(
                key=f"feedback:{r.id}",
                title=f"{labels.get(r.domain, r.domain.title())} feedback",
                description=r.readiness_summary or "Review the latest coaching notes.",
                route="/s/prep?tab=workshops",
                owner="system",
                urgency="neutral",
                status="stub" if r.is_stub else "reviewed",
                due_at=r.created_at,
                provenance=_provenance(
                    "workshop_feedback",
                    r.mode,
                    confidence=65 if r.is_stub else 85,
                    updated_at=r.created_at,
                ),
            )
            for r in runs[:4]
        ]

    def _strategy_item(self, strategy: StudentStrategy | None) -> MySpaceModuleItem | None:
        if strategy is None:
            return None
        description = strategy.narrative or "Your active admissions strategy is ready to refine."
        return MySpaceModuleItem(
            key=f"strategy:{strategy.id}",
            title=strategy.career_target or "Admissions strategy",
            description=description[:220],
            route="/s/profile?tab=strategy",
            owner="student",
            urgency="neutral",
            status=strategy.status,
            due_at=strategy.updated_at,
            provenance=_provenance(
                "strategy",
                "Active strategy",
                confidence=60 if strategy.is_stub else 85,
                updated_at=strategy.updated_at,
            ),
        )

    def _prep_readiness(
        self,
        *,
        recs: list[RecommendationRequest],
        workshop_runs: list[WorkshopFeedbackRun],
        documents: list[StudentDocument],
    ) -> list[MySpaceReadiness]:
        rec_requested = any(r.status in {"requested", "received"} for r in recs)
        essay_feedback = any(r.domain == "essay" for r in workshop_runs)
        interview_feedback = any(r.domain == "interview" for r in workshop_runs)
        resume_doc = any(d.document_type in {"resume", "cv"} for d in documents)
        ready_count = sum([rec_requested, essay_feedback, interview_feedback, resume_doc])
        pct = round(ready_count / 4 * 100)
        return [
            MySpaceReadiness(
                key="prep",
                label="Prep readiness",
                status="ready" if pct >= 75 else "needs_attention",
                pct=pct,
                detail=f"{ready_count}/4 prep lanes have usable evidence.",
                route="/s/prep",
                provenance=_provenance("prep", "Workshops, documents, recommenders", confidence=80),
            ),
            MySpaceReadiness(
                key="interview",
                label="Interview-ready",
                status="ready" if interview_feedback else "needs_attention",
                pct=100 if interview_feedback else 0,
                detail=(
                    "Interview practice feedback is available."
                    if interview_feedback
                    else "Run interview practice before live interviews appear."
                ),
                route="/s/prep?tab=interviews",
                provenance=_provenance("workshop_feedback", "Interview feedback", confidence=80),
            ),
        ]

    def _offer_items(self, *, apps: list[Application], now: datetime) -> list[MySpaceModuleItem]:
        rows: list[MySpaceModuleItem] = []
        for app in apps:
            offer = getattr(app, "offer", None)
            if offer is None:
                continue
            due_at = _due_date_to_datetime(offer.response_deadline)
            amount = offer.scholarship_amount or offer.financial_package_total
            amount_text = f" Aid: ${amount:,}." if amount else ""
            offer_status, offer_description, _offer_blocker, offer_urgency = _offer_decision_state(
                response=offer.student_response,
                status=offer.status,
                due_at=due_at,
                received_externally=bool(offer.received_externally),
                now=now,
            )
            rows.append(
                MySpaceModuleItem(
                    key=f"offer:{offer.id}",
                    title=_program_label(app),
                    description=f"{offer_description}{amount_text}",
                    route="/s/applications?tab=offers",
                    owner="student",
                    urgency=offer_urgency,
                    status=offer_status,
                    due_at=due_at,
                    provenance=_provenance(
                        "offer_letters",
                        offer_status,
                        confidence=90,
                        updated_at=offer.updated_at,
                    ),
                )
            )
        return sorted(rows, key=lambda r: r.due_at or datetime.max.replace(tzinfo=UTC))[:4]

    def _saved_items(self, saved: list) -> list[MySpaceModuleItem]:
        return [
            MySpaceModuleItem(
                key=f"saved:{row.program_id}",
                title=row.program_name or "Saved program",
                description=row.institution_name or row.status,
                route=f"/s/programs/{row.program_id}",
                owner="student",
                urgency="neutral",
                status=row.priority,
                due_at=row.added_at,
                provenance=_provenance(
                    "saved_lists",
                    row.band_label or row.status,
                    confidence=round(row.confidence_score)
                    if row.confidence_score is not None
                    else None,
                    updated_at=row.added_at,
                ),
            )
            for row in saved[:4]
        ]

    def _import_status(
        self,
        *,
        documents: list[StudentDocument],
        clarifications: list[dict],
    ) -> MySpaceModuleItem:
        if documents:
            latest = documents[0]
            return MySpaceModuleItem(
                key="import:status",
                title=f"{len(documents)} imported material(s)",
                description=(
                    f"{len(clarifications)} clarification(s) need review."
                    if clarifications
                    else f"Latest import: {latest.file_name}"
                ),
                route="/s/import",
                owner="student",
                urgency="priority_window" if clarifications else "neutral",
                status="needs_review" if clarifications else "ready",
                due_at=latest.uploaded_at,
                provenance=_provenance(
                    "documents",
                    latest.document_type,
                    confidence=80,
                    updated_at=latest.uploaded_at,
                ),
            )
        return MySpaceModuleItem(
            key="import:status",
            title="No materials imported",
            description=(
                "Upload a transcript, resume, essay draft, or offer letter to reduce manual entry."
            ),
            route="/s/import",
            owner="student",
            urgency="gentle_attention",
            status="empty",
            provenance=_provenance("documents", "No uploaded materials", confidence=90),
        )

    def _recent_changes(
        self,
        *,
        apps: list[Application],
        saved: list,
        documents: list[StudentDocument],
        workshop_runs: list[WorkshopFeedbackRun],
        now: datetime,
    ) -> list[MySpaceModuleItem]:
        rows: list[MySpaceModuleItem] = []
        for app in apps:
            offer = getattr(app, "offer", None)
            if offer is None:
                continue
            due_at = _due_date_to_datetime(getattr(offer, "response_deadline", None))
            offer_status, offer_description, _offer_blocker, offer_urgency = _offer_decision_state(
                response=getattr(offer, "student_response", None),
                status=getattr(offer, "status", None),
                due_at=due_at,
                received_externally=bool(getattr(offer, "received_externally", False)),
                now=now,
            )
            route = _application_route(app.id, "offer")
            rows.append(
                MySpaceModuleItem(
                    key=f"recent:offer:{offer.id}",
                    title=f"Offer from {_program_label(app)}",
                    description=offer_description,
                    route=route,
                    owner="student",
                    urgency=offer_urgency,
                    status=offer_status,
                    due_at=getattr(offer, "updated_at", None) or due_at,
                    provenance=_provenance(
                        "offer_letters",
                        "Offer updated",
                        href=route,
                        confidence=90,
                        updated_at=getattr(offer, "updated_at", None),
                    ),
                )
            )
        for app in apps[:4]:
            rows.append(
                MySpaceModuleItem(
                    key=f"recent:app:{app.id}",
                    title=_program_label(app),
                    description=f"Application status: {app.status or 'draft'}",
                    route=_application_route(app.id),
                    status=app.status,
                    due_at=app.updated_at,
                    provenance=_provenance(
                        "applications", "Application updated", updated_at=app.updated_at
                    ),
                )
            )
        for row in saved[:3]:
            rows.append(
                MySpaceModuleItem(
                    key=f"recent:saved:{row.program_id}",
                    title=row.program_name or "Saved program",
                    description=(
                        "Saved target"
                        f"{f' at {row.institution_name}' if row.institution_name else ''}"
                    ),
                    route="/s/saved",
                    status=row.priority,
                    due_at=row.added_at,
                    provenance=_provenance("saved_lists", "Saved program", updated_at=row.added_at),
                )
            )
        for doc in documents[:3]:
            rows.append(
                MySpaceModuleItem(
                    key=f"recent:doc:{doc.id}",
                    title=doc.file_name,
                    description=f"Imported {doc.document_type}",
                    route="/s/import",
                    status=doc.document_type,
                    due_at=doc.uploaded_at,
                    provenance=_provenance(
                        "documents", "Material imported", updated_at=doc.uploaded_at
                    ),
                )
            )
        for run in workshop_runs[:3]:
            rows.append(
                MySpaceModuleItem(
                    key=f"recent:feedback:{run.id}",
                    title=f"{run.domain.title()} feedback",
                    description=run.readiness_summary or "Feedback run completed.",
                    route="/s/prep?tab=workshops",
                    status=run.mode,
                    due_at=run.created_at,
                    provenance=_provenance(
                        "workshop_feedback",
                        "Feedback run",
                        updated_at=run.created_at,
                    ),
                )
            )
        return sorted(
            rows,
            key=lambda r: r.due_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )[:6]
