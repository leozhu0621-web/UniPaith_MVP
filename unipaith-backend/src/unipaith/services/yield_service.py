"""Spec 35 §4 — Yield analytics (institution dashboard).

Aggregate-on-read over the admitted pool (mirrors ``attribution_service``):
yield rate, the admitted→intent→deposit→enrolled funnel tail with drop-off,
melt, time-to-confirm, waitlist conversion, predicted-vs-target class size, and
yield-by-cohort routed through the fairness lens (46 §6). Plus a ranked
next-best-action list. Everything computes deterministically; the AI agents
(behind ``ai_yield_intelligence_v2_enabled``) only *refine* the action copy, and
any failure falls back to the deterministic ranking (never a 5xx).
"""

from __future__ import annotations

import statistics
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.yield_intelligence import (
    get_next_best_action_agent,
    get_yield_risk_scorer,
)
from unipaith.config import settings
from unipaith.models.application import Application, EnrollmentRecord, OfferLetter
from unipaith.models.institution import IntakeRound, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.utils.calendar_dates import business_today

_ADMITTED_DECISIONS = ("admitted", "accepted", "conditional_admission")
_CONFIRMED_STATES = {"intent_confirmed", "deposit_recorded", "enrollment_confirmed", "enrolled"}
_DEPOSITED_STATES = {"deposit_recorded", "enrollment_confirmed", "enrolled"}
# Disparity threshold (percentage points) above which a cohort gap is flagged
# for the fairness/bias dashboard (46 §6). Warning, not alarm.
_DISPARITY_WARN_PP = 0.15
_MIN_COHORT_N = 5  # don't flag tiny groups as disparities (noise)


class YieldService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_yield(
        self,
        institution_id: UUID,
        *,
        program_id: UUID | None = None,
        intake_id: UUID | None = None,
    ) -> dict:
        # intake_id scopes by its program (applications aren't intake-keyed in MVP).
        if intake_id is not None and program_id is None:
            ir = await self.db.get(IntakeRound, intake_id)
            if ir is not None:
                program_id = ir.program_id

        rows = await self._fetch_admitted(institution_id, program_id)
        if not rows:
            return self._empty(institution_id, program_id)

        admits, enr_by_app, offer_by_app, profile_by_student = rows
        today = business_today()

        # ── Core counts (the funnel tail) ──
        admitted = len(admits)
        intent = deposited = enrolled = confirmed_intent = 0
        confirm_times: list[int] = []
        scorer_input: list[dict] = []
        unconfirmed_at_risk = 0
        soonest_deadline: int | None = None

        match_by = await self._match_fitness(admits)

        for app in admits:
            enr = enr_by_app.get(app.id)
            offer = offer_by_app.get(app.id)
            state = enr.state if enr else "accepted"
            if state in _CONFIRMED_STATES:
                confirmed_intent += 1
                intent += 1
            if (enr and enr.deposit_status in ("paid", "waived")) or state in _DEPOSITED_STATES:
                deposited += 1
            if state == "enrolled":
                enrolled += 1
            # time-to-confirm: decision → intent_confirmed
            if enr and enr.intent_confirmed_at and app.decision_at:
                confirm_times.append(max((enr.intent_confirmed_at - app.decision_at).days, 0))

            days_remaining = None
            if offer and offer.response_deadline:
                days_remaining = (offer.response_deadline - today).days
            offer_resp = offer.student_response if offer else None
            # at-risk unconfirmed = no enrollment confirmation + unanswered/near-deadline
            if state not in _CONFIRMED_STATES and offer_resp != "declined":
                if days_remaining is not None and days_remaining <= 14:
                    unconfirmed_at_risk += 1
                    if days_remaining >= 0:
                        soonest_deadline = (
                            days_remaining
                            if soonest_deadline is None
                            else min(soonest_deadline, days_remaining)
                        )
            scorer_input.append(
                {
                    "application_id": str(app.id),
                    "student_id": str(app.student_id),
                    "student_name": getattr(app, "student_name", None),
                    "state": state,
                    "offer_response": offer_resp,
                    "deposit_status": enr.deposit_status if enr else "none",
                    "days_remaining": days_remaining,
                    "scholarship_amount": (offer.scholarship_amount if offer else None),
                    "fitness": match_by.get(app.id),
                }
            )

        # ── Rates ──
        yield_rate = round(enrolled / admitted, 4) if admitted else 0.0
        melt = max(confirmed_intent - enrolled, 0)
        melt_rate = round(melt / confirmed_intent, 4) if confirmed_intent else 0.0

        # ── Per-admit risk + predicted class size ──
        risk = get_yield_risk_scorer().score(scorer_input)
        predicted = round(risk["expected_confirmations"])
        target = await self._target_class_size(institution_id, program_id)

        # ── Waitlist conversion ──
        waitlist_conversion, waitlist_count, seats_open = await self._waitlist_stats(
            institution_id, program_id, target, confirmed_intent
        )

        # ── Cohort fairness lens ──
        cohorts = self._yield_by_cohort(admits, enr_by_app, profile_by_student)

        snapshot = {
            "admitted": admitted,
            "intent_confirmed": intent,
            "deposited": deposited,
            "enrolled": enrolled,
            "unconfirmed_at_risk": unconfirmed_at_risk,
            "soonest_deadline_days": soonest_deadline,
            "seats_open": seats_open,
            "waitlist_count": waitlist_count,
            "target_class_size": target,
        }
        actions = await self._next_best_actions(snapshot)

        return {
            "scope": {
                "institution_id": str(institution_id),
                "program_id": str(program_id) if program_id else None,
                "intake_id": str(intake_id) if intake_id else None,
            },
            "admitted": admitted,
            "intent_confirmed": intent,
            "deposited": deposited,
            "enrolled": enrolled,
            "yield_rate": yield_rate,
            "melt": melt,
            "melt_rate": melt_rate,
            "waitlist_conversion": waitlist_conversion,
            "predicted_final_class_size": predicted,
            "target_class_size": target,
            "funnel": self._funnel(admitted, intent, deposited, enrolled),
            "time_to_confirm": self._time_to_confirm(confirm_times),
            "waitlist_count": waitlist_count,
            "seats_open": seats_open,
            "at_risk": risk["at_risk"][:25],
            "at_risk_count": len(risk["at_risk"]),
            "cohorts": cohorts,
            "next_best_actions": actions,
        }

    # ── Data fetch ───────────────────────────────────────────────────────────

    async def _fetch_admitted(self, institution_id: UUID, program_id: UUID | None) -> tuple | None:
        stmt = (
            select(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.decision.in_(_ADMITTED_DECISIONS),
            )
        )
        if program_id is not None:
            stmt = stmt.where(Application.program_id == program_id)
        admits = list((await self.db.execute(stmt)).scalars().all())
        if not admits:
            return None
        from unipaith.services.application_service import ApplicationService

        await ApplicationService(self.db)._attach_student_names(admits)
        app_ids = [a.id for a in admits]
        student_ids = list({a.student_id for a in admits})

        enr_rows = await self.db.execute(
            select(EnrollmentRecord).where(EnrollmentRecord.application_id.in_(app_ids))
        )
        enr_by_app = {e.application_id: e for e in enr_rows.scalars().all()}
        offer_rows = await self.db.execute(
            select(OfferLetter).where(OfferLetter.application_id.in_(app_ids))
        )
        offer_by_app = {o.application_id: o for o in offer_rows.scalars().all()}
        prof_rows = await self.db.execute(
            select(StudentProfile).where(StudentProfile.id.in_(student_ids))
        )
        profile_by_student = {p.id: p for p in prof_rows.scalars().all()}
        return admits, enr_by_app, offer_by_app, profile_by_student

    async def _match_fitness(self, admits: list[Application]) -> dict[UUID, float | None]:
        pairs = {(a.student_id, a.program_id): a.id for a in admits}
        if not pairs:
            return {}
        student_ids = list({a.student_id for a in admits})
        program_ids = list({a.program_id for a in admits})
        rows = await self.db.execute(
            select(MatchResult).where(
                MatchResult.student_id.in_(student_ids),
                MatchResult.program_id.in_(program_ids),
            )
        )
        out: dict[UUID, float | None] = {}
        for m in rows.scalars().all():
            app_id = pairs.get((m.student_id, m.program_id))
            if app_id is not None:
                score = m.fitness_score if m.fitness_score is not None else m.match_score
                out[app_id] = float(score) if score is not None else None
        return out

    # ── Derived blocks ───────────────────────────────────────────────────────

    @staticmethod
    def _funnel(admitted: int, intent: int, deposited: int, enrolled: int) -> list[dict]:
        steps = [
            ("Admitted", admitted),
            ("Confirmed intent", intent),
            ("Deposited", deposited),
            ("Enrolled", enrolled),
        ]
        out: list[dict] = []
        prev = None
        for label, count in steps:
            drop = None
            if prev is not None and prev > 0:
                drop = round((prev - count) / prev, 4)
            out.append(
                {
                    "step": label,
                    "count": count,
                    "pct_of_admitted": round(count / admitted, 4) if admitted else 0.0,
                    "drop_off": drop,
                }
            )
            prev = count
        return out

    @staticmethod
    def _time_to_confirm(days: list[int]) -> dict:
        if not days:
            return {"count": 0, "avg_days": None, "median_days": None, "buckets": []}
        buckets = {"0-3d": 0, "4-7d": 0, "8-14d": 0, "15d+": 0}
        for d in days:
            if d <= 3:
                buckets["0-3d"] += 1
            elif d <= 7:
                buckets["4-7d"] += 1
            elif d <= 14:
                buckets["8-14d"] += 1
            else:
                buckets["15d+"] += 1
        return {
            "count": len(days),
            "avg_days": round(statistics.mean(days), 1),
            "median_days": round(statistics.median(days), 1),
            "buckets": [{"label": k, "count": v} for k, v in buckets.items()],
        }

    def _yield_by_cohort(
        self,
        admits: list[Application],
        enr_by_app: dict,
        profiles: dict,
    ) -> list[dict]:
        """Yield rate per cohort group across protected-ish dimensions, with a
        disparity flag for the fairness/bias dashboard (46 §6). Surfaced for
        awareness — never drives selection."""
        dims = [
            ("residency", "residency_status_for_tuition", "Residency"),
            ("gender", "gender_identity", "Gender identity"),
            ("nationality", "nationality", "Nationality"),
        ]
        out: list[dict] = []
        for key, attr, label in dims:
            groups: dict[str, dict] = {}
            for app in admits:
                prof = profiles.get(app.student_id)
                val = (getattr(prof, attr, None) if prof else None) or "Not reported"
                g = groups.setdefault(str(val), {"admitted": 0, "enrolled": 0})
                g["admitted"] += 1
                enr = enr_by_app.get(app.id)
                if enr and enr.state == "enrolled":
                    g["enrolled"] += 1
            rendered = [
                {
                    "group": name,
                    "admitted": v["admitted"],
                    "enrolled": v["enrolled"],
                    "yield_rate": round(v["enrolled"] / v["admitted"], 4) if v["admitted"] else 0.0,
                }
                for name, v in groups.items()
            ]
            rendered.sort(key=lambda r: r["group"])
            # Disparity = max−min yield among groups that are large enough to matter.
            sizable = [r for r in rendered if r["admitted"] >= _MIN_COHORT_N]
            disparity = None
            flag = False
            if len(sizable) >= 2:
                rates = [r["yield_rate"] for r in sizable]
                disparity = round(max(rates) - min(rates), 4)
                flag = disparity >= _DISPARITY_WARN_PP
            out.append(
                {
                    "dimension": key,
                    "label": label,
                    "groups": rendered,
                    "disparity": disparity,
                    "fairness_concern": flag,
                }
            )
        return out

    async def _waitlist_stats(
        self,
        institution_id: UUID,
        program_id: UUID | None,
        target: int | None,
        confirmed: int,
    ) -> tuple[float | None, int, int | None]:
        # Current waitlist size.
        wl_stmt = (
            select(Application)
            .join(Program, Application.program_id == Program.id)
            .where(Program.institution_id == institution_id, Application.decision == "waitlisted")
        )
        if program_id is not None:
            wl_stmt = wl_stmt.where(Application.program_id == program_id)
        waitlist_count = len(list((await self.db.execute(wl_stmt)).scalars().all()))

        # Conversion: of applicants who were ever waitlisted, how many ended up
        # confirmed/enrolled (after being offered a place).
        ever_stmt = (
            select(Application, EnrollmentRecord)
            .join(Program, Application.program_id == Program.id)
            .outerjoin(EnrollmentRecord, EnrollmentRecord.application_id == Application.id)
            .where(
                Program.institution_id == institution_id,
                Application.waitlisted_at.is_not(None),
            )
        )
        if program_id is not None:
            ever_stmt = ever_stmt.where(Application.program_id == program_id)
        ever = (await self.db.execute(ever_stmt)).all()
        offered = [a for a, _e in ever if a.decision in _ADMITTED_DECISIONS]
        converted = sum(1 for _a, e in ever if e is not None and e.state in _CONFIRMED_STATES)
        conversion = round(converted / len(offered), 4) if offered else None

        seats_open = None
        if target is not None:
            seats_open = max(target - confirmed, 0)
        return conversion, waitlist_count, seats_open

    async def _target_class_size(self, institution_id: UUID, program_id: UUID | None) -> int | None:
        stmt = (
            select(IntakeRound)
            .join(Program, IntakeRound.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        if program_id is not None:
            stmt = stmt.where(IntakeRound.program_id == program_id)
        rounds = (await self.db.execute(stmt)).scalars().all()
        caps = [r.capacity for r in rounds if r.capacity]
        return sum(caps) if caps else None

    # ── Next-best-action (deterministic + optional LLM refine) ────────────────

    def _deterministic_actions(self, s: dict) -> list[dict]:
        actions: list[dict] = []
        at_risk = s.get("unconfirmed_at_risk", 0)
        days = s.get("soonest_deadline_days")
        if at_risk:
            when = (
                f" — deadline in {days} day{'s' if days != 1 else ''}"
                if isinstance(days, int)
                else ""
            )
            actions.append(
                {
                    "kind": "nudge_unconfirmed",
                    "label": (
                        f"{at_risk} admit{'s' if at_risk != 1 else ''} haven't "
                        f"confirmed{when}. Send a nudge."
                    ),
                    "rationale": (
                        "A timely reminder before the deadline is the highest-leverage yield move."
                    ),
                    "count": at_risk,
                }
            )
        seats = s.get("seats_open")
        if seats and s.get("waitlist_count"):
            n = min(seats, s["waitlist_count"])
            actions.append(
                {
                    "kind": "release_waitlist",
                    "label": (
                        f"{seats} seat{'s' if seats != 1 else ''} open with "
                        f"{s['waitlist_count']} on the waitlist. Offer to next."
                    ),
                    "rationale": (
                        "Open seats and a ranked waitlist mean you can fill the class now."
                    ),
                    "count": n,
                }
            )
        if s.get("intent_confirmed", 0) > s.get("deposited", 0):
            gap = s["intent_confirmed"] - s["deposited"]
            actions.append(
                {
                    "kind": "follow_up_deposit",
                    "label": (
                        f"{gap} confirmed admit{'s' if gap != 1 else ''} haven't "
                        "recorded a deposit. Follow up."
                    ),
                    "rationale": (
                        "Deposits are the firmest signal a confirmed student will actually arrive."
                    ),
                    "count": gap,
                }
            )
        if not s.get("target_class_size"):
            actions.append(
                {
                    "kind": "set_target",
                    "label": "Set a target class size to track yield against your goal.",
                    "rationale": (
                        "Without a target, predicted-vs-goal and seats-open can't be computed."
                    ),
                    "count": None,
                }
            )
        if not actions:
            actions.append(
                {
                    "kind": "monitor",
                    "label": "Yield is on track — keep monitoring confirmations.",
                    "rationale": "No deadlines are close and no seats are open.",
                    "count": None,
                }
            )
        return actions

    async def _next_best_actions(self, snapshot: dict) -> list[dict]:
        deterministic = self._deterministic_actions(snapshot)
        if not settings.ai_yield_intelligence_v2_enabled:
            return deterministic
        try:
            refined = await get_next_best_action_agent().rank(snapshot, db=self.db)
        except Exception:  # noqa: BLE001 — never let the agent break the dashboard
            refined = None
        return refined or deterministic

    # ── Empty / pre-decisions state (§7) ──────────────────────────────────────

    def _empty(self, institution_id: UUID, program_id: UUID | None) -> dict:
        return {
            "scope": {
                "institution_id": str(institution_id),
                "program_id": str(program_id) if program_id else None,
                "intake_id": None,
            },
            "admitted": 0,
            "intent_confirmed": 0,
            "deposited": 0,
            "enrolled": 0,
            "yield_rate": 0.0,
            "melt": 0,
            "melt_rate": 0.0,
            "waitlist_conversion": None,
            "predicted_final_class_size": 0,
            "target_class_size": None,
            "funnel": [],
            "time_to_confirm": {"count": 0, "avg_days": None, "median_days": None, "buckets": []},
            "waitlist_count": 0,
            "seats_open": None,
            "at_risk": [],
            "at_risk_count": 0,
            "cohorts": [],
            "next_best_actions": [],
            "empty": True,
        }
