"""Connect feed service — Spec 20 §4 (Updates) + §7 (data shape).

Builds the reverse-chronological / relevance-ranked Updates feed from the
institutions a student follows. Item kinds (Spec 20 §4.3 / §7):

- ``post``           — a published institution post.
- ``deadline``       — system-generated from a saved/applied program's
                       ``application_deadline`` (Spec 20 §4.3).
- ``program_change`` — a saved/applied program edited *after* the student
                       engaged with it; **never suppressed by mute** (§4.3).

Mute (Spec 20 §2) suppresses ``post`` and ``deadline`` items from that
institution; ``program_change`` is always shown. Events live in their own tab
(``ConnectEventService``), not the Updates feed.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.application import Application
from unipaith.models.engagement import SavedList, SavedListItem
from unipaith.models.institution import Event, EventRSVP, Institution, InstitutionPost, Program
from unipaith.services.follow_service import FollowService

# Reveal a meeting link to RSVP'd students this many hours before start (Spec 20 §5).
_MEETING_LINK_REVEAL_HOURS = 24

logger = logging.getLogger(__name__)

# How far ahead a deadline must be to still surface as a feed reminder.
_DEADLINE_WINDOW_DAYS = 120


class ConnectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.follows = FollowService(db)

    async def build_updates_feed(
        self, student_id: UUID, *, rank: str = "recent", limit: int = 50
    ) -> dict:
        """Assemble the Updates feed.

        ``rank`` is ``recent`` (reverse-chronological, pinned floated within an
        institution) or ``relevant`` (relevance heuristic; optionally refined by
        the ConnectFeedRanker agent). Returns ``{items, followed_count, muted_count}``.
        """
        followed_all = await self.follows.followed_institution_ids(student_id, include_muted=True)
        muted = await self.follows.muted_institution_ids(student_id)
        visible_insts = followed_all - muted

        items: list[dict] = []
        if followed_all:
            inst_names = await self._institution_names(followed_all)
            items += await self._post_items(visible_insts, inst_names)
            engagement = await self._engagement(student_id)
            items += self._deadline_items(engagement, visible_insts, inst_names)
            items += self._program_change_items(engagement, inst_names, muted)

        if rank == "relevant":
            engagement = locals().get("engagement") or await self._engagement(student_id)
            items = self._order_relevant(items, engagement)
            items = await self._maybe_ai_rerank(items, engagement, student_id)
        else:
            items = self._order_recent(items)

        return {
            "items": items[:limit],
            "followed_count": len(followed_all),
            "muted_count": len(muted),
        }

    # ------------------------------------------------------------------
    # Events tab (Spec 20 §5)
    # ------------------------------------------------------------------

    async def build_events(
        self, student_id: UUID, *, scope: str = "upcoming", limit: int = 50
    ) -> dict:
        """Events from followed institutions (Spec 20 §5).

        ``scope`` ∈ {upcoming, past, mine}. Each event carries the student's
        ``rsvp_state`` (none|rsvp|waitlist|attended), confirmed ``going_count``,
        ``waitlist_count``, ``spots_left``, a ``recommended`` nudge for events on
        saved/applied programs, and a ``meeting_link`` revealed only to RSVP'd
        students near start time.
        """
        now = datetime.now(UTC)
        rsvp_rows = await self.db.execute(
            select(EventRSVP.event_id, EventRSVP.rsvp_status, EventRSVP.attended_at).where(
                EventRSVP.student_id == student_id
            )
        )
        rsvp_map: dict[UUID, str] = {}
        for eid, st, attended_at in rsvp_rows.all():
            if attended_at:
                rsvp_map[eid] = "attended"
            elif st == "waitlisted":
                rsvp_map[eid] = "waitlist"
            elif st == "registered":
                rsvp_map[eid] = "rsvp"

        base = select(Event, Institution.name).join(
            Institution, Institution.id == Event.institution_id
        )
        if scope == "mine":
            if not rsvp_map:
                return {"events": [], "scope": scope}
            query = base.where(Event.id.in_(list(rsvp_map.keys()))).order_by(
                Event.start_time.desc()
            )
        else:
            visible = await self.follows.followed_institution_ids(student_id, include_muted=False)
            if not visible:
                return {"events": [], "scope": scope}
            query = base.where(Event.institution_id.in_(visible), Event.status != "cancelled")
            if scope == "past":
                query = query.where(Event.start_time < now).order_by(Event.start_time.desc())
            else:
                query = query.where(Event.start_time >= now).order_by(Event.start_time.asc())
        rows = (await self.db.execute(query.limit(limit))).all()

        event_ids = [ev.id for ev, _ in rows]
        waitlist_counts: dict[UUID, int] = {}
        if event_ids:
            wl = await self.db.execute(
                select(EventRSVP.event_id, func.count())
                .where(
                    EventRSVP.event_id.in_(event_ids),
                    EventRSVP.rsvp_status == "waitlisted",
                )
                .group_by(EventRSVP.event_id)
            )
            waitlist_counts = {eid: int(c or 0) for eid, c in wl.all()}

        engaged_progs = await self._engaged_program_ids(student_id) if scope != "past" else set()

        events: list[dict] = []
        for ev, inst_name in rows:
            state = rsvp_map.get(ev.id, "none")
            reveals_at = ev.start_time - timedelta(hours=_MEETING_LINK_REVEAL_HOURS)
            reveal = state in ("rsvp", "attended") and now >= reveals_at
            spots_left = (
                max(0, ev.capacity - (ev.rsvp_count or 0)) if ev.capacity is not None else None
            )
            events.append(
                {
                    "id": str(ev.id),
                    "institution_id": str(ev.institution_id),
                    "institution_name": inst_name,
                    "program_id": str(ev.program_id) if ev.program_id else None,
                    "event_name": ev.event_name,
                    "event_type": ev.event_type,
                    "description": ev.description,
                    "location": ev.location,
                    "start_time": ev.start_time.isoformat(),
                    "end_time": ev.end_time.isoformat() if ev.end_time else None,
                    "capacity": ev.capacity,
                    "going_count": ev.rsvp_count or 0,
                    "waitlist_count": waitlist_counts.get(ev.id, 0),
                    "spots_left": spots_left,
                    "at_capacity": spots_left == 0 if spots_left is not None else False,
                    "rsvp_state": state,
                    "recommended": (
                        state == "none"
                        and scope == "upcoming"
                        and ev.program_id is not None
                        and ev.program_id in engaged_progs
                    ),
                    "meeting_link": ev.meeting_link if reveal else None,
                    "meeting_link_reveals_at": reveals_at.isoformat()
                    if (ev.meeting_link and state in ("rsvp", "attended"))
                    else None,
                }
            )

        if scope == "upcoming":
            events = await self._maybe_ai_recommend(events, student_id)
        return {"events": events, "scope": scope}

    async def _engaged_program_ids(self, student_id: UUID) -> set[UUID]:
        saved = await self.db.execute(
            select(SavedListItem.program_id)
            .join(SavedList, SavedList.id == SavedListItem.list_id)
            .where(SavedList.student_id == student_id)
        )
        applied = await self.db.execute(
            select(Application.program_id).where(Application.student_id == student_id)
        )
        return {r[0] for r in saved.all()} | {r[0] for r in applied.all()}

    async def _maybe_ai_recommend(self, events: list[dict], student_id: UUID) -> list[dict]:
        """Optionally let EventRecommender (Spec 20 §8) refine which upcoming
        events are nudged. Flag-gated; falls back to the deterministic
        ``recommended`` flag on any failure."""
        if not settings.ai_connect_ranker_v2_enabled or len(events) < 2:
            return events
        from unipaith.ai.event_recommender import get_event_recommender

        candidates = [e for e in events if e["rsvp_state"] == "none"]
        if not candidates:
            return events
        rec_ids = await get_event_recommender().recommend(
            events=candidates, student_id=student_id, db=self.db
        )
        if rec_ids is None:
            return events
        rec_set = set(rec_ids)
        for e in events:
            if e["rsvp_state"] == "none":
                e["recommended"] = e["id"] in rec_set
        return events

    # ------------------------------------------------------------------
    # Item builders
    # ------------------------------------------------------------------

    async def _post_items(
        self, visible_insts: set[UUID], inst_names: dict[UUID, str]
    ) -> list[dict]:
        if not visible_insts:
            return []
        rows = await self.db.execute(
            select(InstitutionPost)
            .where(
                InstitutionPost.institution_id.in_(visible_insts),
                InstitutionPost.status == "published",
            )
            .order_by(InstitutionPost.published_at.desc().nullslast())
            .limit(200)
        )
        posts = list(rows.scalars().all())
        # Resolve tagged-program names in one pass.
        prog_ids = {
            self._first_program_id(p.tagged_program_ids)
            for p in posts
            if self._first_program_id(p.tagged_program_ids)
        }
        prog_names = await self._program_names(prog_ids) if prog_ids else {}

        out: list[dict] = []
        for p in posts:
            prog_id = self._first_program_id(p.tagged_program_ids)
            when = p.published_at or p.created_at
            out.append(
                {
                    "kind": "post",
                    "id": f"post:{p.id}",
                    "date": when.isoformat(),
                    "institution_id": str(p.institution_id),
                    "institution_name": inst_names.get(p.institution_id, "Institution"),
                    "program_id": str(prog_id) if prog_id else None,
                    "program_name": prog_names.get(prog_id) if prog_id else None,
                    "pinned": bool(p.pinned),
                    "muted": False,
                    "title": p.title,
                    "body": p.body,
                    "media_urls": self._media_list(p.media_urls),
                    # Spec 27 §2.4 — prefer the post's authored CTAs; fall back to
                    # program-derived defaults for legacy posts that have none.
                    "ctas": (
                        p.ctas if isinstance(p.ctas, list) and p.ctas else self._post_ctas(prog_id)
                    ),
                    "post_id": str(p.id),
                }
            )
        return out

    def _deadline_items(
        self, engagement: dict[UUID, dict], visible_insts: set[UUID], inst_names: dict[UUID, str]
    ) -> list[dict]:
        today = datetime.now(UTC).date()
        horizon = today + timedelta(days=_DEADLINE_WINDOW_DAYS)
        out: list[dict] = []
        for prog_id, e in engagement.items():
            dl: date | None = e["application_deadline"]
            inst_id = e["institution_id"]
            if dl is None or inst_id not in visible_insts:
                continue
            if dl < today or dl > horizon:
                continue
            days_until = (dl - today).days
            out.append(
                {
                    "kind": "deadline",
                    "id": f"deadline:{prog_id}",
                    # Sort deadlines by urgency mapped onto the recency axis:
                    # a sooner deadline reads as "newer/more urgent".
                    "date": datetime.combine(dl, datetime.min.time(), tzinfo=UTC).isoformat(),
                    "institution_id": str(inst_id),
                    "institution_name": inst_names.get(inst_id, "Institution"),
                    "program_id": str(prog_id),
                    "program_name": e["program_name"],
                    "muted": False,
                    "deadline": dl.isoformat(),
                    "days_until": days_until,
                    "ctas": self._post_ctas(prog_id),
                }
            )
        return out

    def _program_change_items(
        self, engagement: dict[UUID, dict], inst_names: dict[UUID, str], muted_insts: set[UUID]
    ) -> list[dict]:
        """A program edited after the student engaged with it (Spec 20 §4.3).

        Never suppressed by mute — these are high-priority for an applicant.
        """
        out: list[dict] = []
        for prog_id, e in engagement.items():
            updated: datetime | None = e["program_updated_at"]
            engaged: datetime | None = e["engaged_at"]
            if updated is None or engaged is None:
                continue
            if updated <= engaged:
                continue
            inst_id = e["institution_id"]
            out.append(
                {
                    "kind": "program_change",
                    "id": f"program_change:{prog_id}",
                    "date": updated.isoformat(),
                    "institution_id": str(inst_id),
                    "institution_name": inst_names.get(inst_id, "Institution"),
                    "program_id": str(prog_id),
                    "program_name": e["program_name"],
                    # Shown even when the institution is muted (§4.3).
                    "muted": inst_id in muted_insts,
                    "change_summary": "This program changed a requirement",
                    "ctas": self._post_ctas(prog_id),
                }
            )
        return out

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    @staticmethod
    def _order_recent(items: list[dict]) -> list[dict]:
        """Reverse-chronological, with pinned posts floated to ride with their
        institution's freshest activity (Spec 20 §4.2 — pinned at the top of
        *their institution's* items, not the whole feed)."""
        inst_latest: dict[str, str] = {}
        for it in items:
            iid = it["institution_id"]
            if it["date"] > inst_latest.get(iid, ""):
                inst_latest[iid] = it["date"]

        def key(it: dict):
            pinned = bool(it.get("pinned"))
            base = inst_latest[it["institution_id"]] if pinned else it["date"]
            return (base, 1 if pinned else 0, it["date"])

        return sorted(items, key=key, reverse=True)

    @staticmethod
    def _order_relevant(items: list[dict], engagement: dict[UUID, dict]) -> list[dict]:
        """Deterministic relevance heuristic (Spec 20 §4.2 / §8 fallback):
        program_change > approaching deadline > posts from applied/saved
        institutions > everything else, recency as tiebreaker."""
        applied_insts = {e["institution_id"] for e in engagement.values() if e["applied"]}
        saved_insts = {e["institution_id"] for e in engagement.values()}

        def weight(it: dict) -> int:
            kind = it["kind"]
            if kind == "program_change":
                return 1000
            if kind == "deadline":
                # Sooner deadline = higher weight (cap at 120-day window).
                return 900 - min(it.get("days_until", 120), 120)
            # post
            try:
                iid = UUID(it["institution_id"])
            except (ValueError, KeyError):
                iid = None
            if iid in applied_insts:
                return 400 + (100 if it.get("pinned") else 0)
            if iid in saved_insts:
                return 300 + (100 if it.get("pinned") else 0)
            return 100 + (100 if it.get("pinned") else 0)

        return sorted(items, key=lambda it: (weight(it), it["date"]), reverse=True)

    async def _maybe_ai_rerank(
        self, items: list[dict], engagement: dict[UUID, dict], student_id: UUID
    ) -> list[dict]:
        """Optionally refine the relevance order with the ConnectFeedRanker
        agent (Spec 20 §8). Flag-gated; on any failure the deterministic order
        is kept unchanged (Spec 20 §9)."""
        if not settings.ai_connect_ranker_v2_enabled or len(items) < 2:
            return items
        from unipaith.ai.connect_ranker import get_connect_ranker

        applied = [e["program_name"] for e in engagement.values() if e["applied"]]
        saved = [e["program_name"] for e in engagement.values() if not e["applied"]]
        ranked_ids = await get_connect_ranker().rank(
            items=items,
            applied_programs=applied,
            saved_programs=saved,
            student_id=student_id,
            db=self.db,
        )
        if not ranked_ids:
            return items
        order = {id_: i for i, id_ in enumerate(ranked_ids)}
        # Stable sort: agent-ranked items in its order, unranked keep their
        # deterministic position at the end.
        return sorted(items, key=lambda it: order.get(it["id"], len(order) + 1))

    # ------------------------------------------------------------------
    # Data loading helpers
    # ------------------------------------------------------------------

    async def _engagement(self, student_id: UUID) -> dict[UUID, dict]:
        """Per saved/applied program: institution, name, deadline, the
        program's ``updated_at``, the earliest engagement timestamp, and whether
        an application exists. Keyed by program_id."""
        out: dict[UUID, dict] = {}

        saved = await self.db.execute(
            select(
                Program.id,
                Program.institution_id,
                Program.program_name,
                Program.application_deadline,
                Program.updated_at,
                SavedListItem.added_at,
            )
            .join(SavedListItem, SavedListItem.program_id == Program.id)
            .join(SavedList, SavedList.id == SavedListItem.list_id)
            .where(SavedList.student_id == student_id)
        )
        for pid, inst_id, name, dl, updated, added_at in saved.all():
            out[pid] = {
                "institution_id": inst_id,
                "program_name": name,
                "application_deadline": dl,
                "program_updated_at": updated,
                "engaged_at": added_at,
                "applied": False,
            }

        applied = await self.db.execute(
            select(
                Program.id,
                Program.institution_id,
                Program.program_name,
                Program.application_deadline,
                Program.updated_at,
                Application.created_at,
            )
            .join(Application, Application.program_id == Program.id)
            .where(Application.student_id == student_id)
        )
        for pid, inst_id, name, dl, updated, created_at in applied.all():
            entry = out.get(pid)
            if entry is None:
                out[pid] = {
                    "institution_id": inst_id,
                    "program_name": name,
                    "application_deadline": dl,
                    "program_updated_at": updated,
                    "engaged_at": created_at,
                    "applied": True,
                }
            else:
                entry["applied"] = True
                # Earliest engagement wins for change detection.
                if entry["engaged_at"] is None or (created_at and created_at < entry["engaged_at"]):
                    entry["engaged_at"] = created_at
        return out

    async def _institution_names(self, ids: set[UUID]) -> dict[UUID, str]:
        if not ids:
            return {}
        rows = await self.db.execute(
            select(Institution.id, Institution.name).where(Institution.id.in_(ids))
        )
        return {r[0]: r[1] for r in rows.all()}

    async def _program_names(self, ids: set[UUID]) -> dict[UUID, str]:
        ids = {i for i in ids if i}
        if not ids:
            return {}
        rows = await self.db.execute(
            select(Program.id, Program.program_name).where(Program.id.in_(ids))
        )
        return {r[0]: r[1] for r in rows.all()}

    @staticmethod
    def _first_program_id(tagged: object) -> UUID | None:
        if not tagged or not isinstance(tagged, list):
            return None
        for raw in tagged:
            try:
                return UUID(str(raw))
            except (ValueError, TypeError):
                continue
        return None

    @staticmethod
    def _media_list(media: object) -> list:
        if isinstance(media, list):
            return media
        return []

    @staticmethod
    def _post_ctas(program_id: UUID | None) -> list[dict]:
        """Synthesize the CTAs a post carries (Spec 20 §4.1 / 27 §2.4). The
        post model has no explicit ctas column yet, so we derive sensible ones
        from the tagged program."""
        if program_id is None:
            return []
        return [
            {"type": "view_program", "label": "View program", "target": str(program_id)},
            {
                "type": "add_to_calendar",
                "label": "Add deadline to calendar",
                "target": str(program_id),
            },
        ]
