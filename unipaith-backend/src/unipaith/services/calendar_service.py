"""Spec 16 · Calendar — aggregation + persistence service.

One unified admissions timeline assembled live from every time-sensitive
source (applications, interviews, event RSVPs, offers, recommendation
requests) plus the student's own reminders and work blocks. Each item gets a
stable composite id (``<type>:<source_uuid>``) so a PATCH can route back to
the right place — student-created rows mutate ``student_calendar`` directly,
while derived items get a per-student overlay row in ``calendar_item_states``
(mark-complete / notes / attach-confirmation) without touching source tables.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, Interview, OfferLetter
from unipaith.models.engagement import CalendarItemState, StudentCalendar
from unipaith.models.institution import Event, EventRSVP, Institution, Program
from unipaith.models.student import RecommendationRequest
from unipaith.schemas.calendar import (
    CalendarItem,
    CalendarItemPatch,
    ReminderCreate,
    WorkBlockCreate,
)

# Item types whose passing-without-completion is "overdue" (Spec 16 §7/§11).
# Appointments (interviews, events, portfolio/audition) are not "overdue" when
# past — only commitments you complete are. Work blocks are self-imposed, so
# they are not flagged red either.
_OVERDUE_ELIGIBLE = {
    "submission_deadline",
    "document_deadline",
    "recommendation_deadline",
    "interview_submission_deadline",
    "deposit_deadline",
    "reminder",
}

# Spec 33 §2 interview types map onto the calendar's live-vs-window split.
# portfolio_review / third_party_platform are scheduled (live); recorded_async /
# technical_assessment submit within a window.
_LIVE_INTERVIEW_KINDS = {
    "video",
    "phone",
    "in_person",
    "live",
    "on_campus",
    "portfolio_review",
    "third_party_platform",
}
_RECORDED_INTERVIEW_KINDS = {
    "recorded",
    "async",
    "asynchronous",
    "video_submission",
    "recorded_async",
    "technical_assessment",
}

_CAMPUS_EVENT_KINDS = {"campus_visit", "visit", "campus_tour", "tour", "open_house", "open-house"}
_INFO_EVENT_KINDS = {
    "info_session",
    "information_session",
    "webinar",
    "virtual_info",
    "virtual_information",
    "online_info",
}
_PORTFOLIO_EVENT_KINDS = {"portfolio_review", "portfolio"}
_AUDITION_EVENT_KINDS = {"audition", "tryout"}

# Interview statuses that map to our four canonical CalendarItem statuses.
_CANCELLED_INTERVIEW = {"cancelled", "canceled", "declined", "withdrawn"}
_COMPLETED_INTERVIEW = {"completed", "done"}


def _aware(dt: datetime) -> datetime:
    """Coerce a possibly-naive datetime to a UTC-aware one for comparison."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _eod(d: date) -> datetime:
    """A bare date deadline → end-of-day UTC (Spec 16 §13: store UTC, render local)."""
    return datetime.combine(d, time(23, 59, 0), tzinfo=UTC)


class CalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Read ───────────────────────────────────────────────────────────────

    async def get_calendar(
        self,
        student_id: UUID,
        from_dt: datetime | None = None,
        to_dt: datetime | None = None,
    ) -> list[CalendarItem]:
        now = datetime.now(UTC)
        items: list[dict] = []

        # Map program_id -> application_id so recommendation requests can
        # deep-link to the right application workspace.
        app_by_program: dict[UUID, UUID] = {}

        # 1) Applications → submission deadlines -----------------------------
        rows = await self.db.execute(
            select(Application, Program, Institution)
            .join(Program, Application.program_id == Program.id)
            .join(Institution, Program.institution_id == Institution.id)
            .where(Application.student_id == student_id)
        )
        for app, program, inst in rows.all():
            app_by_program[app.program_id] = app.id
            already_submitted = app.status in {"submitted", "under_review", "decided"} or bool(
                app.submitted_at
            )
            if program.application_deadline:
                base_status = "completed" if already_submitted else "scheduled"
                items.append(
                    {
                        "id": f"submission_deadline:{app.id}",
                        "type": "submission_deadline",
                        "title": f"{program.program_name} — application due",
                        "start_at": _eod(program.application_deadline),
                        "application_id": app.id,
                        "status": base_status,
                        "subtitle": inst.name,
                        "institution_name": inst.name,
                        "link": f"/s/applications/{app.id}",
                    }
                )

        # 2) Interviews ------------------------------------------------------
        rows = await self.db.execute(
            select(Interview, Application, Program, Institution)
            .join(Application, Interview.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .join(Institution, Program.institution_id == Institution.id)
            .where(Application.student_id == student_id)
        )
        for iv, app, program, inst in rows.all():
            kind = (iv.interview_type or "").lower()
            is_recorded = kind in _RECORDED_INTERVIEW_KINDS
            start = iv.confirmed_time
            if start is None and iv.proposed_times:
                start = _parse_first_time(iv.proposed_times)
            # Async interviews (recorded_async / technical_assessment) carry only
            # a submission window — anchor the calendar item on its deadline.
            if start is None and iv.async_window_end is not None:
                start = iv.async_window_end
            if start is None:
                continue
            item_type = "interview_recorded_window" if is_recorded else "interview_live"
            link_or_loc = iv.location_or_link or ""
            meeting_link = link_or_loc if link_or_loc.startswith("http") else None
            location = None if meeting_link else (link_or_loc or None)
            status = _interview_status(iv.status)
            label = "Interview window" if is_recorded else "Interview"
            end_at = _aware(start) + timedelta(minutes=iv.duration_minutes or 30)
            if is_recorded and iv.async_window_end is not None:
                end_at = _aware(iv.async_window_end)
            raw_status = (iv.status or "").lower()
            proposed = iv.proposed_times if isinstance(iv.proposed_times, list) else []
            items.append(
                {
                    "id": f"{item_type}:{iv.id}",
                    "type": item_type,
                    "title": f"{label} — {program.program_name}",
                    "start_at": _aware(start),
                    "end_at": end_at,
                    "location": location,
                    "meeting_link": meeting_link,
                    "application_id": app.id,
                    "status": status,
                    "subtitle": inst.name,
                    "institution_name": inst.name,
                    "link": f"/s/applications/{app.id}?tab=interviews",
                    "interview_id": iv.id,
                    "proposed_times": proposed,
                    "can_confirm": raw_status == "proposed",
                    "can_decline": raw_status == "proposed",
                    "can_reschedule": raw_status in {"proposed", "confirmed"},
                    "interview_status": raw_status,
                }
            )

        # 3) Event RSVPs → campus visits / info sessions ---------------------
        rows = await self.db.execute(
            select(EventRSVP, Event, Institution)
            .join(Event, EventRSVP.event_id == Event.id)
            .join(Institution, Event.institution_id == Institution.id)
            .where(EventRSVP.student_id == student_id)
        )
        for rsvp, event, inst in rows.all():
            if (rsvp.rsvp_status or "").lower() in {"cancelled", "canceled"}:
                continue
            items.append(
                {
                    "id": f"event:{rsvp.id}",
                    "type": _event_type(event.event_type),
                    "title": event.event_name,
                    "start_at": _aware(event.start_time),
                    "end_at": _aware(event.end_time) if event.end_time else None,
                    "location": event.location,
                    "status": "scheduled",
                    "subtitle": inst.name,
                    "institution_name": inst.name,
                    "link": f"/school/{inst.id}?tab=events",
                }
            )

        # 4) Offers → deposit / response deadlines ---------------------------
        rows = await self.db.execute(
            select(OfferLetter, Application, Program, Institution)
            .join(Application, OfferLetter.application_id == Application.id)
            .join(Program, Application.program_id == Program.id)
            .join(Institution, Program.institution_id == Institution.id)
            .where(Application.student_id == student_id)
        )
        for offer, app, program, inst in rows.all():
            if not offer.response_deadline:
                continue
            responded = bool(offer.student_response) and offer.student_response not in {
                "pending",
                "none",
            }
            items.append(
                {
                    "id": f"deposit_deadline:{offer.id}",
                    "type": "deposit_deadline",
                    "title": f"Respond to offer — {program.program_name}",
                    "start_at": _eod(offer.response_deadline),
                    "application_id": app.id,
                    "status": "completed" if responded else "scheduled",
                    "subtitle": inst.name,
                    "institution_name": inst.name,
                    "link": f"/s/applications/{app.id}",
                }
            )

        # 5) Recommendation requests → recommendation deadlines --------------
        rows = await self.db.execute(
            select(RecommendationRequest).where(
                RecommendationRequest.student_id == student_id,
                RecommendationRequest.due_date.is_not(None),
            )
        )
        for rec in rows.scalars().all():
            app_id = app_by_program.get(rec.target_program_id) if rec.target_program_id else None
            done = (rec.status or "").lower() in {"submitted", "received", "completed", "done"}
            link = (
                f"/s/applications/{app_id}?tab=recommenders"
                if app_id
                else "/s/profile?tab=recommenders"
            )
            items.append(
                {
                    "id": f"recommendation_deadline:{rec.id}",
                    "type": "recommendation_deadline",
                    "title": f"Recommendation due — {rec.recommender_name}",
                    "start_at": _eod(rec.due_date),
                    "application_id": app_id,
                    "status": "completed" if done else "scheduled",
                    "subtitle": rec.recommender_title or "Recommender",
                    "recommender_name": rec.recommender_name,
                    "link": link,
                }
            )

        # 6) Student-created reminders + work blocks -------------------------
        rows = await self.db.execute(
            select(StudentCalendar).where(StudentCalendar.student_id == student_id)
        )
        for entry in rows.scalars().all():
            etype = (
                entry.entry_type if entry.entry_type in {"reminder", "work_block"} else "reminder"
            )
            items.append(
                {
                    "id": f"{etype}:{entry.id}",
                    "type": etype,
                    "title": entry.title,
                    "start_at": _aware(entry.start_time),
                    "end_at": _aware(entry.end_time) if entry.end_time else None,
                    "location": entry.location,
                    "meeting_link": entry.meeting_link,
                    "application_id": entry.application_id,
                    "status": entry.status or "scheduled",
                    "notes": entry.description,
                    "reminder_settings": entry.reminder_settings,
                    "subtitle": _humanize(entry.category) if entry.category else None,
                    "link": (
                        f"/s/applications/{entry.application_id}" if entry.application_id else None
                    ),
                    "editable": True,
                }
            )

        # 7) Overlay per-student derived-item state (mark complete / notes) --
        states = await self.db.execute(
            select(CalendarItemState).where(CalendarItemState.student_id == student_id)
        )
        state_by_key = {s.item_key: s for s in states.scalars().all()}

        result: list[CalendarItem] = []
        for d in items:
            st = state_by_key.get(d["id"])
            if st is not None:
                if st.status:
                    d["status"] = st.status
                if st.notes is not None:
                    d["notes"] = st.notes
                if st.confirmation_url is not None:
                    d["confirmation_url"] = st.confirmation_url

            # Overdue computation (Spec 16 §11): past AND not completed/cancelled.
            if (
                d["type"] in _OVERDUE_ELIGIBLE
                and d["status"] not in {"completed", "cancelled"}
                and _aware(d["start_at"]) < now
            ):
                d["status"] = "overdue"

            # Range filter on start_at.
            if from_dt and _aware(d["start_at"]) < _aware(from_dt):
                continue
            if to_dt and _aware(d["start_at"]) > _aware(to_dt):
                continue

            result.append(CalendarItem(**d))

        result.sort(key=lambda i: i.start_at)
        return result

    # ── Create ─────────────────────────────────────────────────────────────

    async def create_reminder(self, student_id: UUID, body: ReminderCreate) -> CalendarItem:
        entry = StudentCalendar(
            student_id=student_id,
            entry_type="reminder",
            title=body.title,
            description=body.notes,
            start_time=_aware(body.start_at),
            reminder_at=_aware(body.start_at),
            status="scheduled",
            application_id=body.application_id,
            reminder_settings=body.reminder_settings.model_dump()
            if body.reminder_settings
            else None,
        )
        self.db.add(entry)
        await self.db.flush()
        return await self._one(student_id, f"reminder:{entry.id}")

    async def create_work_block(self, student_id: UUID, body: WorkBlockCreate) -> CalendarItem:
        start = _aware(body.start_at)
        end = _aware(body.end_at) if body.end_at else None
        if end is None:
            end = start + timedelta(minutes=body.duration_minutes or 60)
        entry = StudentCalendar(
            student_id=student_id,
            entry_type="work_block",
            title=body.title,
            description=body.notes,
            start_time=start,
            end_time=end,
            status="scheduled",
            category=body.category,
            application_id=body.application_id,
        )
        self.db.add(entry)
        await self.db.flush()
        return await self._one(student_id, f"work_block:{entry.id}")

    # ── Update ─────────────────────────────────────────────────────────────

    async def patch_item(
        self, student_id: UUID, item_id: str, body: CalendarItemPatch
    ) -> CalendarItem | None:
        prefix, _, raw = item_id.rpartition(":")
        if prefix in {"reminder", "work_block"}:
            await self._patch_student_entry(student_id, raw, body)
        else:
            await self._patch_derived(student_id, item_id, body)
        await self.db.flush()
        return await self._one(student_id, item_id)

    async def _patch_student_entry(
        self, student_id: UUID, raw_id: str, body: CalendarItemPatch
    ) -> None:
        try:
            entry_id = UUID(raw_id)
        except ValueError:
            return
        row = await self.db.execute(
            select(StudentCalendar).where(
                StudentCalendar.id == entry_id,
                StudentCalendar.student_id == student_id,
            )
        )
        entry = row.scalar_one_or_none()
        if entry is None:
            return
        if body.status is not None:
            entry.status = body.status
        if body.notes is not None:
            entry.description = body.notes
        if body.title is not None:
            entry.title = body.title
        if body.start_at is not None:
            entry.start_time = _aware(body.start_at)
        if body.end_at is not None:
            entry.end_time = _aware(body.end_at)

    async def _patch_derived(
        self, student_id: UUID, item_key: str, body: CalendarItemPatch
    ) -> None:
        row = await self.db.execute(
            select(CalendarItemState).where(
                CalendarItemState.student_id == student_id,
                CalendarItemState.item_key == item_key,
            )
        )
        state = row.scalar_one_or_none()
        if state is None:
            state = CalendarItemState(student_id=student_id, item_key=item_key)
            self.db.add(state)
        if body.status is not None:
            state.status = body.status
            state.completed_at = datetime.now(UTC) if body.status == "completed" else None
        if body.notes is not None:
            state.notes = body.notes
        if body.confirmation_url is not None:
            state.confirmation_url = body.confirmation_url

    # ── helpers ─────────────────────────────────────────────────────────────

    async def _one(self, student_id: UUID, item_id: str) -> CalendarItem | None:
        """Re-fetch a single item by id from the full aggregation (small N)."""
        for it in await self.get_calendar(student_id):
            if it.id == item_id:
                return it
        return None


def _parse_first_time(proposed: object) -> datetime | None:
    seq = proposed if isinstance(proposed, list) else None
    if not seq:
        return None
    first = seq[0]
    if isinstance(first, datetime):
        return first
    if isinstance(first, str):
        try:
            return datetime.fromisoformat(first.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _interview_status(raw: str | None) -> str:
    s = (raw or "").lower()
    if s in _CANCELLED_INTERVIEW:
        return "cancelled"
    if s in _COMPLETED_INTERVIEW:
        return "completed"
    return "scheduled"


def _event_type(raw: str | None) -> str:
    s = (raw or "").lower()
    if s in _CAMPUS_EVENT_KINDS:
        return "campus_visit"
    if s in _PORTFOLIO_EVENT_KINDS:
        return "portfolio_review"
    if s in _AUDITION_EVENT_KINDS:
        return "audition"
    return "info_session"


def _humanize(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()
