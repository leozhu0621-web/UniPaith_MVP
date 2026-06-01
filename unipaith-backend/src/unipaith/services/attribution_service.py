"""Spec 28 — Attribution & Funnel Analytics service.

Reads aggregate from the event-sourced ``attribution_events`` store (§8). The
store is fed by ``record`` (wired best-effort into the existing engagement /
campaign / application action sites) and ``backfill_institution`` (derives events
idempotently from the durable domain tables so the funnel is meaningful on
day-one data). Overview KPIs + operational outreach metrics still read directly
from the domain tables (applications / offers / campaign_recipients / event_rsvps).
"""

from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, OfferLetter
from unipaith.models.attribution import AttributionEvent
from unipaith.models.engagement import (
    SavedList,
    SavedListItem,
    StudentCompareItem,
    StudentEngagementSignal,
)
from unipaith.models.institution import (
    Campaign,
    CampaignAction,
    CampaignRecipient,
    Event,
    EventRSVP,
    Inquiry,
    InstitutionPost,
    Program,
    Promotion,
)
from unipaith.schemas.analytics import (
    AppliedFilters,
    AttributionReport,
    CampaignMetricRow,
    DropOffAlert,
    EventMetricRow,
    FunnelReport,
    FunnelStageItem,
    KpiMetric,
    NamedCount,
    OverviewReport,
    PeriodCount,
    SubFunnel,
    TopContentRow,
    TopSource,
)

logger = logging.getLogger(__name__)

# A stage-to-stage conversion drop at/above this fraction surfaces a §4 alert.
_DROP_OFF_THRESHOLD = 0.5

# Campaign lifecycle states that mean "has been sent" (Spec 25). The legacy
# get_analytics used the never-set status "sent"; these are the real values.
_SENT_CAMPAIGN_STATES = ("active", "completed")

# Combined funnel (§4): stage key, label, the attribution actions it counts.
_COMBINED_STAGES: list[tuple[str, str, tuple[str, ...]]] = [
    ("impressions", "Impressions", ("impression", "view")),
    ("clicks", "Clicks", ("click",)),
    ("saves", "Saves", ("save",)),
    ("apps_started", "Apps started", ("apply_started",)),
    ("submitted", "Submitted", ("submitted",)),
    ("accepted", "Accepted", ("decision_outcome",)),  # restricted to admitted
]

# Sub-funnels (§3).
_DISCOVERY_STAGES: list[tuple[str, str, tuple[str, ...]]] = [
    ("impression", "Impression", ("impression",)),
    ("view", "View", ("view",)),
    ("click", "Click", ("click",)),
    ("save", "Save", ("save",)),
    ("compare", "Compare", ("compare",)),
    ("request_info", "Request info", ("request_info",)),
]
_EVENT_STAGES: list[tuple[str, str, tuple[str, ...]]] = [
    ("rsvp", "RSVP", ("rsvp",)),
    ("attendance", "Attendance", ("attendance",)),
    ("post_event", "Post-event engagement", ("click", "request_info", "apply_started")),
]
_APPLICATION_STAGES: list[tuple[str, str, tuple[str, ...]]] = [
    ("apply_started", "Apply started", ("apply_started",)),
    ("submitted", "Submitted", ("submitted",)),
    ("decision", "Decision", ("decision_outcome",)),
]


class AttributionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ write

    async def record(
        self,
        *,
        institution_id: UUID,
        source_kind: str,
        action: str,
        student_id: UUID | None = None,
        source_id: UUID | None = None,
        program_id: UUID | None = None,
        campaign_id: UUID | None = None,
        intake_round_id: UUID | None = None,
        segment_id: UUID | None = None,
        occurred_at: datetime | None = None,
        meta: dict | None = None,
        dedupe_key: str | None = None,
    ) -> None:
        """Record one attribution event. Best-effort — a failure here must never
        break the host action, so the insert runs inside a SAVEPOINT that rolls
        back in isolation, leaving the outer transaction usable.
        """
        try:
            async with self.db.begin_nested():
                self.db.add(
                    AttributionEvent(
                        institution_id=institution_id,
                        student_id=student_id,
                        source_kind=source_kind,
                        source_id=source_id,
                        action=action,
                        program_id=program_id,
                        campaign_id=campaign_id,
                        intake_round_id=intake_round_id,
                        segment_id=segment_id,
                        occurred_at=occurred_at or datetime.now(UTC),
                        meta=meta,
                        dedupe_key=dedupe_key,
                    )
                )
        except Exception:  # pragma: no cover - defensive, never surfaced
            logger.warning("attribution.record failed (swallowed)", exc_info=True)

    # --------------------------------------------------------------- backfill

    async def backfill_institution(self, institution_id: UUID) -> int:
        """Idempotently derive attribution events from the durable domain tables.

        Safe to call repeatedly: every derived row carries a stable ``dedupe_key``
        and is inserted with ``ON CONFLICT DO NOTHING``.
        """
        rows: list[dict] = []

        def add(dedupe_key: str, **kw) -> None:
            # Uniform key set across every row — a multi-row ``values()`` insert
            # derives its column list from the FIRST row, so a row missing e.g.
            # ``meta`` would silently drop that column for the whole batch.
            rows.append(
                {
                    "id": uuid.uuid4(),
                    "institution_id": institution_id,
                    "student_id": kw.get("student_id"),
                    "source_kind": kw["source_kind"],
                    "source_id": kw.get("source_id"),
                    "action": kw["action"],
                    "campaign_id": kw.get("campaign_id"),
                    "program_id": kw.get("program_id"),
                    "intake_round_id": kw.get("intake_round_id"),
                    "segment_id": kw.get("segment_id"),
                    "occurred_at": kw.get("occurred_at") or datetime.now(UTC),
                    "meta": kw.get("meta"),
                    "dedupe_key": dedupe_key,
                }
            )

        # 1. Applications → apply_started / submitted / decision_outcome
        app_rows = await self.db.execute(
            select(
                Application.id,
                Application.program_id,
                Application.student_id,
                Application.status,
                Application.submitted_at,
                Application.decision,
                Application.decision_at,
                Application.created_at,
            )
            .join(Program, Application.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        for a in app_rows.all():
            add(
                f"app_started:{a.id}",
                student_id=a.student_id,
                source_kind="program_page",
                source_id=a.program_id,
                action="apply_started",
                program_id=a.program_id,
                occurred_at=a.created_at,
            )
            if a.submitted_at is not None:
                add(
                    f"app_submitted:{a.id}",
                    student_id=a.student_id,
                    source_kind="program_page",
                    source_id=a.program_id,
                    action="submitted",
                    program_id=a.program_id,
                    occurred_at=a.submitted_at,
                )
            if a.decision:
                add(
                    f"app_decision:{a.id}",
                    student_id=a.student_id,
                    source_kind="program_page",
                    source_id=a.program_id,
                    action="decision_outcome",
                    program_id=a.program_id,
                    occurred_at=a.decision_at or a.created_at,
                    meta={"decision": a.decision},
                )

        # 2. Event RSVPs → rsvp / attendance
        rsvp_rows = await self.db.execute(
            select(
                EventRSVP.id,
                EventRSVP.event_id,
                EventRSVP.student_id,
                EventRSVP.registered_at,
                EventRSVP.attended_at,
                EventRSVP.attendance_status,
                Event.program_id,
            )
            .join(Event, EventRSVP.event_id == Event.id)
            .where(Event.institution_id == institution_id)
        )
        for r in rsvp_rows.all():
            add(
                f"rsvp:{r.id}",
                student_id=r.student_id,
                source_kind="event",
                source_id=r.event_id,
                action="rsvp",
                program_id=r.program_id,
                occurred_at=r.registered_at,
            )
            if r.attendance_status == "attended" or r.attended_at is not None:
                add(
                    f"attendance:{r.id}",
                    student_id=r.student_id,
                    source_kind="event",
                    source_id=r.event_id,
                    action="attendance",
                    program_id=r.program_id,
                    occurred_at=r.attended_at or r.registered_at,
                )

        # 3. Saved programs → save
        save_rows = await self.db.execute(
            select(
                SavedListItem.id,
                SavedListItem.program_id,
                SavedListItem.added_at,
                SavedList.student_id,
            )
            .join(SavedList, SavedListItem.list_id == SavedList.id)
            .join(Program, SavedListItem.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        for s in save_rows.all():
            add(
                f"save:{s.id}",
                student_id=s.student_id,
                source_kind="program_page",
                source_id=s.program_id,
                action="save",
                program_id=s.program_id,
                occurred_at=s.added_at,
            )

        # 4. Compare tray → compare
        cmp_rows = await self.db.execute(
            select(
                StudentCompareItem.id,
                StudentCompareItem.program_id,
                StudentCompareItem.student_id,
                StudentCompareItem.created_at,
            )
            .join(Program, StudentCompareItem.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        for c in cmp_rows.all():
            add(
                f"compare:{c.id}",
                student_id=c.student_id,
                source_kind="program_page",
                source_id=c.program_id,
                action="compare",
                program_id=c.program_id,
                occurred_at=c.created_at,
            )

        # 5. Inquiries → request_info
        inq_rows = await self.db.execute(
            select(
                Inquiry.id,
                Inquiry.program_id,
                Inquiry.student_id,
                Inquiry.campaign_id,
                Inquiry.created_at,
            ).where(Inquiry.institution_id == institution_id)
        )
        for q in inq_rows.all():
            add(
                f"inquiry:{q.id}",
                student_id=q.student_id,
                source_kind="program_page" if q.program_id else "institution_page",
                source_id=q.program_id or institution_id,
                action="request_info",
                program_id=q.program_id,
                campaign_id=q.campaign_id,
                occurred_at=q.created_at,
            )

        # 6. Program-view signals → view
        sig_rows = await self.db.execute(
            select(
                StudentEngagementSignal.id,
                StudentEngagementSignal.program_id,
                StudentEngagementSignal.student_id,
                StudentEngagementSignal.created_at,
            )
            .join(Program, StudentEngagementSignal.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                StudentEngagementSignal.signal_type == "viewed_program",
            )
        )
        for v in sig_rows.all():
            add(
                f"signal:{v.id}",
                student_id=v.student_id,
                source_kind="program_page",
                source_id=v.program_id,
                action="view",
                program_id=v.program_id,
                occurred_at=v.created_at,
            )

        # 7. Campaign actions → mapped action, source_kind=campaign
        act_map = {
            "view": "view",
            "click": "click",
            "save": "save",
            "rsvp": "rsvp",
            "request_info": "request_info",
            "apply": "apply_started",
            "apply_started": "apply_started",
            "apply_submitted": "submitted",
            "decision": "decision_outcome",
        }
        ca_rows = await self.db.execute(
            select(
                CampaignAction.id,
                CampaignAction.campaign_id,
                CampaignAction.student_id,
                CampaignAction.action_type,
                CampaignAction.created_at,
                Campaign.program_id,
            )
            .join(Campaign, CampaignAction.campaign_id == Campaign.id)
            .where(Campaign.institution_id == institution_id)
        )
        for ca in ca_rows.all():
            mapped = act_map.get(ca.action_type)
            if not mapped:
                continue
            add(
                f"campaign_action:{ca.id}",
                student_id=ca.student_id,
                source_kind="campaign",
                source_id=ca.campaign_id,
                action=mapped,
                program_id=ca.program_id,
                campaign_id=ca.campaign_id,
                occurred_at=ca.created_at,
            )

        if not rows:
            return 0
        stmt = (
            pg_insert(AttributionEvent)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["dedupe_key"])
        )
        await self.db.execute(stmt)
        await self.db.flush()
        return len(rows)

    async def _ensure_backfilled(self, institution_id: UUID) -> None:
        # Backfill is idempotent (stable dedupe_key + ON CONFLICT DO NOTHING), so
        # we derive from the durable domain tables on every read — the funnel
        # stays fresh without having to live-wire every action site, and live
        # post/event/promotion engagement (which has no backfillable source) is
        # captured separately by ``record`` from the tracking endpoint.
        await self.backfill_institution(institution_id)

    # ------------------------------------------------------------ filter prep

    def _resolve_window(
        self, time_window: str, range_from: datetime | None, range_to: datetime | None
    ) -> tuple[datetime | None, datetime | None, datetime | None, datetime | None]:
        """Return (start, end, prior_start, prior_end). All-time → all Nones."""
        now = datetime.now(UTC)
        if range_from or range_to:
            start = range_from
            end = range_to or now
            if start:
                length = end - start
                return start, end, start - length, start
            return None, end, None, None
        if time_window == "yoy":
            start = now - timedelta(days=365)
            return start, now, now - timedelta(days=730), start
        days = {"7d": 7, "30d": 30, "90d": 90}.get(time_window)
        if days is None:
            return None, None, None, None
        start = now - timedelta(days=days)
        return start, now, now - timedelta(days=2 * days), start

    async def _segment_students(
        self, institution_id: UUID, segment_id: UUID | None
    ) -> list[UUID] | None:
        """Resolve a segment to its student-id set, or None when not filtering."""
        if not segment_id:
            return None
        from unipaith.services.institution_service import InstitutionService

        try:
            return await InstitutionService(self.db).resolve_segment_members(
                institution_id, segment_id
            )
        except Exception:
            logger.warning("segment resolution failed", exc_info=True)
            return []

    def _event_conditions(
        self,
        institution_id: UUID,
        flt: AppliedFilters,
        start: datetime | None,
        end: datetime | None,
        student_ids: list[UUID] | None,
    ) -> list:
        conds = [AttributionEvent.institution_id == institution_id]
        if start is not None:
            conds.append(AttributionEvent.occurred_at >= start)
        if end is not None:
            conds.append(AttributionEvent.occurred_at < end)
        if flt.program_id:
            conds.append(AttributionEvent.program_id == flt.program_id)
        if flt.intake_id:
            conds.append(AttributionEvent.intake_round_id == flt.intake_id)
        if flt.campaign_id:
            conds.append(AttributionEvent.campaign_id == flt.campaign_id)
        if flt.source_kind:
            conds.append(AttributionEvent.source_kind == flt.source_kind)
        if flt.source_id:
            conds.append(AttributionEvent.source_id == flt.source_id)
        if student_ids is not None:
            conds.append(AttributionEvent.student_id.in_(student_ids))
        return conds

    async def _count(
        self,
        base_conds: list,
        actions: tuple[str, ...],
        *,
        source_kind: str | None = None,
        admitted_only: bool = False,
    ) -> int:
        conds = [*base_conds, AttributionEvent.action.in_(actions)]
        if source_kind:
            conds.append(AttributionEvent.source_kind == source_kind)
        if admitted_only:
            conds.append(AttributionEvent.meta["decision"].astext == "admitted")
        return await self.db.scalar(select(func.count()).where(*conds)) or 0

    # ------------------------------------------------------------------ funnel

    async def get_funnel(self, institution_id: UUID, flt: AppliedFilters) -> FunnelReport:
        await self._ensure_backfilled(institution_id)
        start, end, _, _ = self._resolve_window(flt.time_window, flt.range_from, flt.range_to)
        student_ids = await self._segment_students(institution_id, flt.segment_id)
        base = self._event_conditions(institution_id, flt, start, end, student_ids)

        total_events = await self.db.scalar(select(func.count()).where(*base)) or 0

        # Combined funnel + drop-off alerts
        stages: list[FunnelStageItem] = []
        prev: int | None = None
        for key, label, actions in _COMBINED_STAGES:
            count = await self._count(base, actions, admitted_only=(key == "accepted"))
            conv = (count / prev) if (prev not in (None, 0)) else None
            stages.append(
                FunnelStageItem(stage=key, label=label, count=count, conversion_from_prev=conv)
            )
            prev = count

        drop_offs: list[DropOffAlert] = []
        for i in range(1, len(stages)):
            a, b = stages[i - 1], stages[i]
            if a.count > 0:
                drop = (a.count - b.count) / a.count
                if drop >= _DROP_OFF_THRESHOLD:
                    drop_offs.append(
                        DropOffAlert(
                            from_stage=a.label,
                            to_stage=b.label,
                            drop_pct=round(drop, 4),
                            hint=(
                                f"Biggest drop: {a.label} → {b.label} "
                                f"({round(drop * 100)}% drop). Investigate where "
                                "students stall."
                            ),
                        )
                    )
        drop_offs.sort(key=lambda d: d.drop_pct, reverse=True)

        # Sub-funnels
        sub_funnels: list[SubFunnel] = []
        for sf_key, sf_label, sf_stages in (
            ("discovery", "Discovery", _DISCOVERY_STAGES),
            ("event", "Event", _EVENT_STAGES),
            ("application", "Application", _APPLICATION_STAGES),
        ):
            items: list[FunnelStageItem] = []
            sprev: int | None = None
            for key, label, actions in sf_stages:
                sk = "event" if sf_key == "event" else None
                count = await self._count(base, actions, source_kind=sk)
                conv = (count / sprev) if (sprev not in (None, 0)) else None
                items.append(
                    FunnelStageItem(stage=key, label=label, count=count, conversion_from_prev=conv)
                )
                sprev = count
            sub_funnels.append(SubFunnel(key=sf_key, label=sf_label, stages=items))

        top_clicks = await self._top_sources(base, "click")
        top_apply = await self._top_sources(base, "apply_started")

        return FunnelReport(
            filter=flt,
            stages=stages,
            sub_funnels=sub_funnels,
            top_sources_by_clicks=top_clicks,
            top_sources_by_apply_started=top_apply,
            drop_off_alerts=drop_offs,
            total_events=total_events,
            has_data=total_events > 0,
            generated_at=datetime.now(UTC),
        )

    async def _top_sources(self, base_conds: list, action: str) -> list[TopSource]:
        rows = await self.db.execute(
            select(
                AttributionEvent.source_kind,
                AttributionEvent.source_id,
                func.count().label("c"),
            )
            .where(*base_conds, AttributionEvent.action == action)
            .group_by(AttributionEvent.source_kind, AttributionEvent.source_id)
            .order_by(func.count().desc())
            .limit(5)
        )
        out: list[TopSource] = []
        for source_kind, source_id, c in rows.all():
            out.append(
                TopSource(
                    source_id=source_id,
                    source_kind=source_kind,
                    label=await self._source_label(source_kind, source_id),
                    action_count=c,
                )
            )
        return out

    async def _source_label(self, source_kind: str, source_id: UUID | None) -> str:
        if source_id is None:
            return source_kind.replace("_", " ").title()
        lookup = {
            "post": (InstitutionPost, InstitutionPost.title),
            "event": (Event, Event.event_name),
            "promotion": (Promotion, Promotion.title),
            "program_page": (Program, Program.program_name),
            "campaign": (Campaign, Campaign.campaign_name),
        }
        pair = lookup.get(source_kind)
        if pair:
            model, col = pair
            name = await self.db.scalar(select(col).where(model.id == source_id))
            if name:
                return name
        return source_kind.replace("_", " ").title()

    # ---------------------------------------------------------------- overview

    async def get_overview(self, institution_id: UUID, flt: AppliedFilters) -> OverviewReport:
        await self._ensure_backfilled(institution_id)
        start, end, p_start, p_end = self._resolve_window(
            flt.time_window, flt.range_from, flt.range_to
        )
        student_ids = await self._segment_students(institution_id, flt.segment_id)

        cur = await self._overview_kpis(institution_id, flt, student_ids, start, end)
        if p_start is None and p_end is None:
            # No prior window (all-time / open-ended range) → no comparison, so the
            # KPI cards read "No prior-period comparison" rather than a bogus +0%.
            prior = {"total": None, "acceptance": None, "avg_match": None, "yield": None}
        else:
            prior = await self._overview_kpis(institution_id, flt, student_ids, p_start, p_end)

        def kpi(field: str, unit: str) -> KpiMetric:
            v = cur[field]
            pv = prior[field]
            delta = None
            if v is not None and pv not in (None, 0):
                delta = round((v - pv) / pv, 4)
            return KpiMetric(value=v, prior=pv, delta_pct=delta, unit=unit)

        breakdowns = await self._overview_breakdowns(institution_id, flt, student_ids, start, end)

        return OverviewReport(
            filter=flt,
            total_applications=kpi("total", "count"),
            acceptance_rate=kpi("acceptance", "percent"),
            avg_match_score=kpi("avg_match", "score"),
            yield_rate=kpi("yield", "percent"),
            apps_by_status=breakdowns["apps_by_status"],
            apps_by_program=breakdowns["apps_by_program"],
            apps_over_time=breakdowns["apps_over_time"],
            decisions_breakdown=breakdowns["decisions_breakdown"],
            has_data=cur["total"] > 0,
            generated_at=datetime.now(UTC),
        )

    def _app_conditions(
        self,
        institution_id: UUID,
        flt: AppliedFilters,
        student_ids: list[UUID] | None,
        start: datetime | None,
        end: datetime | None,
    ) -> list:
        conds = [Program.institution_id == institution_id, Application.status != "draft"]
        if flt.program_id:
            conds.append(Application.program_id == flt.program_id)
        if student_ids is not None:
            conds.append(Application.student_id.in_(student_ids))
        if start is not None:
            conds.append(Application.created_at >= start)
        if end is not None:
            conds.append(Application.created_at < end)
        return conds

    async def _overview_kpis(
        self,
        institution_id: UUID,
        flt: AppliedFilters,
        student_ids: list[UUID] | None,
        start: datetime | None,
        end: datetime | None,
    ) -> dict:
        conds = self._app_conditions(institution_id, flt, student_ids, start, end)

        total = (
            await self.db.scalar(
                select(func.count())
                .select_from(Application)
                .join(Program, Application.program_id == Program.id)
                .where(*conds)
            )
            or 0
        )

        decisions = await self.db.execute(
            select(Application.decision, func.count())
            .join(Program, Application.program_id == Program.id)
            .where(*conds, Application.decision.isnot(None))
            .group_by(Application.decision)
        )
        dmap = {row[0]: row[1] for row in decisions.all()}
        decided = sum(dmap.values())
        acceptance = (dmap.get("admitted", 0) / decided) if decided > 0 else None

        avg_raw = await self.db.scalar(
            select(func.avg(Application.match_score))
            .join(Program, Application.program_id == Program.id)
            .where(*conds, Application.match_score.isnot(None))
        )
        avg_match = float(avg_raw) if avg_raw is not None else None

        yield_conds = [Program.institution_id == institution_id]
        if flt.program_id:
            yield_conds.append(Application.program_id == flt.program_id)
        if student_ids is not None:
            yield_conds.append(Application.student_id.in_(student_ids))
        if start is not None:
            yield_conds.append(OfferLetter.created_at >= start)
        if end is not None:
            yield_conds.append(OfferLetter.created_at < end)
        yrow = (
            await self.db.execute(
                select(
                    func.count().label("total_offers"),
                    func.count()
                    .filter(OfferLetter.student_response == "accepted")
                    .label("accepted"),
                )
                .select_from(OfferLetter)
                .join(Application, OfferLetter.application_id == Application.id)
                .join(Program, Application.program_id == Program.id)
                .where(*yield_conds)
            )
        ).one()
        yield_rate = (yrow.accepted / yrow.total_offers) if yrow.total_offers > 0 else None

        return {
            "total": total,
            "acceptance": acceptance,
            "avg_match": avg_match,
            "yield": yield_rate,
        }

    async def _overview_breakdowns(
        self,
        institution_id: UUID,
        flt: AppliedFilters,
        student_ids: list[UUID] | None,
        start: datetime | None,
        end: datetime | None,
    ) -> dict:
        conds = self._app_conditions(institution_id, flt, student_ids, start, end)

        status_rows = await self.db.execute(
            select(Application.status, func.count())
            .join(Program, Application.program_id == Program.id)
            .where(*conds)
            .group_by(Application.status)
        )
        apps_by_status = {row[0]: row[1] for row in status_rows.all() if row[0]}

        prog_rows = await self.db.execute(
            select(Program.program_name, func.count())
            .select_from(Application)
            .join(Program, Application.program_id == Program.id)
            .where(*conds)
            .group_by(Program.program_name)
            .order_by(func.count().desc())
            .limit(12)
        )
        apps_by_program = [NamedCount(label=row[0], count=row[1]) for row in prog_rows.all()]

        month_rows = await self.db.execute(
            select(func.to_char(Application.submitted_at, "YYYY-MM").label("m"), func.count())
            .join(Program, Application.program_id == Program.id)
            .where(*conds, Application.submitted_at.isnot(None))
            .group_by("m")
            .order_by("m")
        )
        apps_over_time = [PeriodCount(period=row[0], count=row[1]) for row in month_rows.all()]

        dec_rows = await self.db.execute(
            select(Application.decision, func.count())
            .join(Program, Application.program_id == Program.id)
            .where(*conds, Application.decision.isnot(None))
            .group_by(Application.decision)
        )
        decisions_breakdown = {row[0]: row[1] for row in dec_rows.all()}

        return {
            "apps_by_status": apps_by_status,
            "apps_by_program": apps_by_program,
            "apps_over_time": apps_over_time,
            "decisions_breakdown": decisions_breakdown,
        }

    # ------------------------------------------------------------- attribution

    async def get_attribution(self, institution_id: UUID, flt: AppliedFilters) -> AttributionReport:
        await self._ensure_backfilled(institution_id)
        start, end, _, _ = self._resolve_window(flt.time_window, flt.range_from, flt.range_to)
        student_ids = await self._segment_students(institution_id, flt.segment_id)
        base = self._event_conditions(institution_id, flt, start, end, student_ids)

        campaigns = await self._campaign_metrics(institution_id, flt, start, end)
        events = await self._event_metrics(institution_id, flt, start, end)
        top_clicks = await self._top_content(base, "click")
        top_apply = await self._top_content(base, "apply_started")

        has_data = bool(campaigns or events or top_clicks or top_apply)
        return AttributionReport(
            filter=flt,
            campaigns=campaigns,
            events=events,
            top_content_by_clicks=top_clicks,
            top_content_by_apply_started=top_apply,
            has_data=has_data,
            generated_at=datetime.now(UTC),
        )

    async def _campaign_metrics(
        self,
        institution_id: UUID,
        flt: AppliedFilters,
        start: datetime | None,
        end: datetime | None,
    ) -> list[CampaignMetricRow]:
        conds = [
            Campaign.institution_id == institution_id,
            Campaign.status.in_(_SENT_CAMPAIGN_STATES),
        ]
        if flt.campaign_id:
            conds.append(Campaign.id == flt.campaign_id)
        if flt.program_id:
            conds.append(Campaign.program_id == flt.program_id)
        if start is not None:
            conds.append(Campaign.sent_at >= start)
        if end is not None:
            conds.append(Campaign.sent_at < end)
        camps = (await self.db.execute(select(Campaign).where(*conds))).scalars().all()

        out: list[CampaignMetricRow] = []
        for c in camps:
            m = (
                await self.db.execute(
                    select(
                        func.count().label("total"),
                        func.count()
                        .filter(CampaignRecipient.delivered_at.isnot(None))
                        .label("delivered"),
                        func.count()
                        .filter(CampaignRecipient.opened_at.isnot(None))
                        .label("opened"),
                        func.count()
                        .filter(CampaignRecipient.clicked_at.isnot(None))
                        .label("clicked"),
                    ).where(CampaignRecipient.campaign_id == c.id)
                )
            ).one()
            apps = (
                await self.db.scalar(
                    select(func.count(func.distinct(Application.id)))
                    .select_from(Application)
                    .join(
                        CampaignRecipient,
                        CampaignRecipient.student_id == Application.student_id,
                    )
                    .where(
                        CampaignRecipient.campaign_id == c.id,
                        Application.status != "draft",
                    )
                )
                or 0
            )
            channels = c.channels or []
            # Open tracking is not implemented (no pixel / SES webhook) — report
            # honestly rather than a fake 0%.
            out.append(
                CampaignMetricRow(
                    campaign_id=c.id,
                    campaign_name=c.campaign_name,
                    channels=channels,
                    status=c.status,
                    send_volume=m.total,
                    delivered=m.delivered,
                    delivery_rate=(m.delivered / m.total) if m.total else None,
                    opened=m.opened,
                    open_rate=(m.opened / m.delivered) if (m.opened and m.delivered) else None,
                    open_supported=False,
                    clicked=m.clicked,
                    click_rate=(m.clicked / m.delivered) if m.delivered else None,
                    applications_started=apps,
                )
            )
        return out

    async def _event_metrics(
        self,
        institution_id: UUID,
        flt: AppliedFilters,
        start: datetime | None,
        end: datetime | None,
    ) -> list[EventMetricRow]:
        conds = [Event.institution_id == institution_id]
        if flt.program_id:
            conds.append(Event.program_id == flt.program_id)
        if start is not None:
            conds.append(Event.start_time >= start)
        if end is not None:
            conds.append(Event.start_time < end)
        events = (await self.db.execute(select(Event).where(*conds))).scalars().all()

        out: list[EventMetricRow] = []
        for e in events:
            rsvps = (
                await self.db.scalar(
                    select(func.count()).select_from(EventRSVP).where(EventRSVP.event_id == e.id)
                )
                or 0
            )
            attended = (
                await self.db.scalar(
                    select(func.count())
                    .select_from(EventRSVP)
                    .where(
                        EventRSVP.event_id == e.id,
                        (EventRSVP.attendance_status == "attended")
                        | (EventRSVP.attended_at.isnot(None)),
                    )
                )
                or 0
            )
            apps_after = (
                await self.db.scalar(
                    select(func.count(func.distinct(Application.id)))
                    .select_from(Application)
                    .join(EventRSVP, EventRSVP.student_id == Application.student_id)
                    .where(EventRSVP.event_id == e.id, Application.status != "draft")
                )
                or 0
            )
            out.append(
                EventMetricRow(
                    event_id=e.id,
                    event_name=e.event_name,
                    rsvps=rsvps,
                    attended=attended,
                    attendance_rate=(attended / rsvps) if rsvps else None,
                    applications_after=apps_after,
                )
            )
        return out

    async def _top_content(self, base_conds: list, action: str) -> list[TopContentRow]:
        rows = await self.db.execute(
            select(
                AttributionEvent.source_kind,
                AttributionEvent.source_id,
                func.count().label("c"),
            )
            .where(
                *base_conds,
                AttributionEvent.action == action,
                AttributionEvent.source_kind.in_(("post", "event", "promotion", "program_page")),
            )
            .group_by(AttributionEvent.source_kind, AttributionEvent.source_id)
            .order_by(func.count().desc())
            .limit(8)
        )
        out: list[TopContentRow] = []
        for source_kind, source_id, c in rows.all():
            title = await self._source_label(source_kind, source_id)
            out.append(
                TopContentRow(
                    source_id=source_id,
                    source_kind=source_kind,
                    title=title,
                    clicks=c if action == "click" else 0,
                    apply_started=c if action == "apply_started" else 0,
                )
            )
        return out

    # --------------------------------------------------------------- csv export

    async def export_csv(self, institution_id: UUID, kind: str, flt: AppliedFilters) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        if kind == "funnel":
            report = await self.get_funnel(institution_id, flt)
            writer.writerow(["stage", "count", "conversion_from_prev"])
            for s in report.stages:
                writer.writerow(
                    [
                        s.label,
                        s.count,
                        "" if s.conversion_from_prev is None else round(s.conversion_from_prev, 4),
                    ]
                )
        elif kind == "attribution":
            report = await self.get_attribution(institution_id, flt)
            writer.writerow(
                [
                    "type",
                    "name",
                    "send_volume_or_rsvps",
                    "delivered_or_attended",
                    "clicked",
                    "applications",
                ]
            )
            for c in report.campaigns:
                writer.writerow(
                    [
                        "campaign",
                        c.campaign_name,
                        c.send_volume,
                        c.delivered,
                        c.clicked,
                        c.applications_started,
                    ]
                )
            for e in report.events:
                writer.writerow(
                    ["event", e.event_name, e.rsvps, e.attended, "", e.applications_after]
                )
        else:  # overview
            report = await self.get_overview(institution_id, flt)
            writer.writerow(["metric", "value", "prior", "delta_pct"])
            for label, k in (
                ("Total applications", report.total_applications),
                ("Acceptance rate", report.acceptance_rate),
                ("Avg match score", report.avg_match_score),
                ("Yield rate", report.yield_rate),
            ):
                writer.writerow(
                    [
                        label,
                        "" if k.value is None else k.value,
                        "" if k.prior is None else k.prior,
                        "" if k.delta_pct is None else k.delta_pct,
                    ]
                )
        return buf.getvalue()
