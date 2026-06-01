"""Spec 31 §9 — admissions-intake dashboard intelligence.

Three institution-facing, mostly rule-based signals that power the executive
dashboard (`/i/dashboard`):

- ``generate_digest`` — the plain-English daily digest. A Sonnet narrator
  (``ai.intelligence_digest``) writes it from a pre-computed, non-PII stat
  block when ``ai_intelligence_digest_v2_enabled`` is on; otherwise (and on any
  agent failure) a deterministic rule-based narrator runs. Never 5xxes.
- ``yield_risks`` — admitted applicants who haven't responded (continuous,
  rule-based).
- ``fairness_signal`` — applicant-pool / admit-rate skew on a protected
  attribute (spec 31 §11, G-D4 / G-I5). Advisory; reuses the same protected
  attributes + skew threshold as the segment-preview fairness check.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.application import Application, IntegritySignal
from unipaith.models.attribution import AttributionEvent
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile

logger = logging.getLogger(__name__)

# Reuse the same protected attributes + skew threshold the segment-preview
# fairness check uses (services/segment_service.py), so "fairness" means the
# same thing across the institution surface.
_PROTECTED_ATTRS = ("nationality", "gender_identity")
_FAIRNESS_MIN_POOL = 20
_FAIRNESS_SKEW_THRESHOLD = 0.70
# An admit-rate gap this large between the top protected group and the rest is
# surfaced as a fairness watch-point (advisory only — never an auto-halt).
_ADMIT_RATE_GAP = 0.20

# Student-side outcome values that mean "responded" (no longer at yield risk).
_RESPONDED = ("accepted_by_student", "declined_by_student", "withdrawn")
# Statuses that count as an active competing application elsewhere.
_INACTIVE = ("draft", "rejected", "withdrawn")


class DashboardIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Intelligence digest
    # ------------------------------------------------------------------

    async def generate_digest(self, institution_id: UUID) -> dict[str, Any]:
        inst = await self.db.get(Institution, institution_id)
        inst_name = (inst.name if inst else None) or "your institution"
        stats = await self._digest_stats(institution_id)

        digest_text: str | None = None
        if settings.ai_intelligence_digest_v2_enabled:
            try:
                from unipaith.ai.intelligence_digest import get_intelligence_digest_agent

                result = await get_intelligence_digest_agent().narrate(
                    {**stats, "institution": inst_name}, db=self.db
                )
                if result is not None:
                    digest_text = result.digest
            except Exception:  # noqa: BLE001 — digest must never 5xx
                logger.exception("intelligence digest agent failed; using fallback")

        source = "llm"
        if not digest_text:
            digest_text = self._rule_based_digest(stats)
            source = "rule_based"

        return {
            "institution_id": str(institution_id),
            "institution_name": inst_name,
            "digest": digest_text,
            "stats": {
                k: v
                for k, v in stats.items()
                if isinstance(v, (int, float))  # FE type: Record<string, number>
            },
            "top_source": stats.get("top_source"),
            "source": source,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def _digest_stats(self, institution_id: UUID) -> dict[str, Any]:
        """Compute a small, non-PII stat block. Every figure is best-effort and
        omitted (left None / 0) rather than guessed when data is thin."""
        now = datetime.now(UTC)
        wk = now - timedelta(days=7)
        prev_wk = now - timedelta(days=14)
        stats: dict[str, Any] = {}

        # New applications in the last 7 days (submitted, not draft).
        new_apps = await self.db.execute(
            select(func.count())
            .select_from(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.status != "draft",
                Application.created_at >= wk,
            )
        )
        stats["new_apps_7d"] = int(new_apps.scalar_one() or 0)

        # Average match (fitness) of the applicant pool, 0–100.
        avg_fit = await self._avg_fitness(institution_id)
        if avg_fit is not None:
            stats["avg_match"] = round(avg_fit * 100)

        # Week-over-week match-quality movement (percent change of mean fitness).
        cur = await self._avg_fitness(institution_id, since=wk, until=now)
        prev = await self._avg_fitness(institution_id, since=prev_wk, until=wk)
        if cur is not None and prev not in (None, 0):
            stats["match_quality_wow_pct"] = round((cur - prev) / prev * 100)

        # Top application source over the last 7 days (by attribution volume).
        top = await self._top_source(institution_id, since=wk)
        if top:
            stats["top_source"] = top[0]
            stats["top_source_apps"] = top[1]

        # Open integrity signals + admitted-no-response count (context only).
        integ = await self.db.execute(
            select(func.count())
            .select_from(IntegritySignal)
            .where(
                IntegritySignal.institution_id == institution_id,
                IntegritySignal.status == "open",
            )
        )
        stats["integrity_open"] = int(integ.scalar_one() or 0)
        stats["admitted_no_response"] = await self._admitted_no_response_count(institution_id)
        return stats

    async def _avg_fitness(
        self,
        institution_id: UUID,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> float | None:
        stmt = (
            select(func.avg(MatchResult.fitness_score))
            .select_from(MatchResult)
            .join(Program, MatchResult.program_id == Program.id)
            .where(Program.institution_id == institution_id)
        )
        if since is not None:
            stmt = stmt.where(MatchResult.computed_at >= since)
        if until is not None:
            stmt = stmt.where(MatchResult.computed_at < until)
        val = (await self.db.execute(stmt)).scalar_one_or_none()
        return float(val) if val is not None else None

    async def _top_source(self, institution_id: UUID, *, since: datetime) -> tuple[str, int] | None:
        """Top application source by attribution volume in the window. Prefers
        application-type actions; falls back to all engagement if none."""
        for action_filter in (Application, None):  # sentinel: first pass = apply-ish
            stmt = (
                select(AttributionEvent.source_kind, func.count().label("n"))
                .where(
                    AttributionEvent.institution_id == institution_id,
                    AttributionEvent.occurred_at >= since,
                )
                .group_by(AttributionEvent.source_kind)
                .order_by(func.count().desc())
                .limit(1)
            )
            if action_filter is Application:
                stmt = stmt.where(AttributionEvent.action.ilike("%appl%"))
            row = (await self.db.execute(stmt)).first()
            if row and row[0]:
                return (self._humanize(row[0]), int(row[1]))
        return None

    @staticmethod
    def _humanize(token: str) -> str:
        return token.replace("_", " ").title()

    def _rule_based_digest(self, stats: dict[str, Any]) -> str:
        """Deterministic narrator — the always-available fallback."""
        parts: list[str] = []
        wow = stats.get("match_quality_wow_pct")
        if wow is not None and wow != 0:
            direction = "up" if wow > 0 else "down"
            parts.append(
                f"Match quality is {direction} {abs(wow)}% this week versus last, "
                "shaping the fit of the applicants arriving now."
            )
        elif stats.get("avg_match"):
            parts.append(f"The applicant pool is averaging a {stats['avg_match']} match score.")

        new_apps = stats.get("new_apps_7d") or 0
        top_source = stats.get("top_source")
        top_apps = stats.get("top_source_apps")
        if top_source and top_apps:
            tail = f" of the {new_apps} new applications" if new_apps else ""
            parts.append(
                f"{top_source} was the largest source over the past week, "
                f"generating {top_apps}{tail}."
            )
        elif new_apps:
            parts.append(f"{new_apps} new applications arrived over the past week.")

        integ = stats.get("integrity_open") or 0
        if integ:
            parts.append(
                f"{integ} integrity {'signal' if integ == 1 else 'signals'} remain open for review."
            )
        if not parts:
            return (
                "No new activity to report yet. As applications, matches, and "
                "campaign traffic come in, this digest will summarize the week."
            )
        return " ".join(parts)

    # ------------------------------------------------------------------
    # Yield-risk alerts
    # ------------------------------------------------------------------

    async def _admitted_no_response_count(self, institution_id: UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.decision == "admitted",
                Application.student_decision.is_(None),
            )
        )
        return int((await self.db.execute(stmt)).scalar_one() or 0)

    async def yield_risks(self, institution_id: UUID) -> dict[str, Any]:
        """Admitted applicants who have not yet responded — ranked by risk."""
        now = datetime.now(UTC)
        rows = await self.db.execute(
            select(Application)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.decision == "admitted",
                Application.student_decision.is_(None),
            )
        )
        admitted = list(rows.scalars().all())

        alerts: list[dict[str, Any]] = []
        for app in admitted:
            competing = await self._competing_count(app)
            decided = app.decision_at or app.updated_at
            days_waiting = (now - decided).days if decided else 0
            if competing >= 2 or days_waiting >= 10:
                risk = "high"
            elif competing >= 1 or days_waiting >= 5:
                risk = "medium"
            else:
                risk = "low"
            reason_bits = []
            if days_waiting > 0:
                reason_bits.append(f"admitted {days_waiting}d ago, no response")
            else:
                reason_bits.append("admitted, no response yet")
            if competing:
                reason_bits.append(
                    f"{competing} competing application{'s' if competing != 1 else ''}"
                )
            alerts.append(
                {
                    "application_id": str(app.id),
                    "student_id": str(app.student_id),
                    "program_id": str(app.program_id),
                    "risk_level": risk,
                    "competing_programs": competing,
                    "reason": "; ".join(reason_bits),
                    "days_waiting": days_waiting,
                }
            )

        # Most urgent first: high → medium → low, then longest-waiting.
        order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda a: (order[a["risk_level"]], -a["days_waiting"]))
        return {
            "institution_id": str(institution_id),
            "alerts": alerts,
            "generated_at": now.isoformat(),
        }

    async def _competing_count(self, app: Application) -> int:
        """Other active applications by the same student (any institution)."""
        stmt = (
            select(func.count())
            .select_from(Application)
            .where(
                Application.student_id == app.student_id,
                Application.id != app.id,
                Application.status.not_in(_INACTIVE),
                Application.student_decision.is_distinct_from("declined_by_student"),
                Application.student_decision.is_distinct_from("withdrawn"),
            )
        )
        return int((await self.db.execute(stmt)).scalar_one() or 0)

    # ------------------------------------------------------------------
    # Fairness signal (spec 31 §11 — G-D4 / G-I5)
    # ------------------------------------------------------------------

    async def fairness_signal(self, institution_id: UUID) -> dict[str, Any]:
        """Advisory fairness watch-point over the applicant pool.

        Warns when (a) the applicant pool skews heavily on a protected attribute,
        or (b) the admit rate differs markedly across a protected attribute's
        groups. Returns ``status`` ∈ {ok, warning, insufficient_data}.
        """
        # Pull (protected-attr value, decision) for every non-draft applicant.
        base = (
            select(StudentProfile, Application.decision)
            .join(Application, Application.student_id == StudentProfile.id)
            .join(Program, Application.program_id == Program.id)
            .where(
                Program.institution_id == institution_id,
                Application.status != "draft",
            )
        )
        rows = (await self.db.execute(base)).all()
        pool = len(rows)
        if pool < _FAIRNESS_MIN_POOL:
            return {
                "status": "insufficient_data",
                "message": "Not enough applicants yet to assess representation.",
                "pool": pool,
            }

        for attr in _PROTECTED_ATTRS:
            groups: dict[str, dict[str, int]] = {}
            for profile, decision in rows:
                key = getattr(profile, attr, None) or "Unknown"
                if key == "Unknown":
                    continue
                g = groups.setdefault(key, {"total": 0, "admitted": 0, "decided": 0})
                g["total"] += 1
                if decision:
                    g["decided"] += 1
                    if decision == "admitted":
                        g["admitted"] += 1
            known_total = sum(g["total"] for g in groups.values())
            if known_total < _FAIRNESS_MIN_POOL:
                continue

            label = attr.replace("_", " ")
            top_key, top_grp = max(groups.items(), key=lambda kv: kv[1]["total"])

            # (a) pool composition skew
            if top_grp["total"] / known_total >= _FAIRNESS_SKEW_THRESHOLD:
                pct = round(100 * top_grp["total"] / known_total)
                return {
                    "status": "warning",
                    "dimension": label,
                    "message": (
                        f"Applicant pool skews heavily on {label} "
                        f"({pct}% {top_key}). Review sourcing for representation."
                    ),
                    "pool": pool,
                }

            # (b) admit-rate gap between the largest group and everyone else
            rates = {
                k: (g["admitted"] / g["decided"]) for k, g in groups.items() if g["decided"] >= 5
            }
            if len(rates) >= 2:
                hi_k, hi = max(rates.items(), key=lambda kv: kv[1])
                lo_k, lo = min(rates.items(), key=lambda kv: kv[1])
                if hi - lo >= _ADMIT_RATE_GAP:
                    return {
                        "status": "warning",
                        "dimension": label,
                        "message": (
                            f"Admit rate varies by {label}: "
                            f"{round(hi * 100)}% ({hi_k}) vs {round(lo * 100)}% "
                            f"({lo_k}). Worth a fairness review."
                        ),
                        "pool": pool,
                    }

        return {
            "status": "ok",
            "message": "No representation skew detected in the applicant pool.",
            "pool": pool,
        }
