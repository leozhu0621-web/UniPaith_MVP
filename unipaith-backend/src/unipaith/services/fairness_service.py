"""Spec 46 §6 — Fairness auto-halt engine.

Deterministic disparate-impact computation + the two-consecutive-week auto-halt.
No LLM, no AI agent — pure math over `match_results` joined to student
demographics. Mirrors the aggregate-on-read pattern of `yield_service` /
`attribution_service`: the current week is computed lazily on read, historical
weeks are computed once (by the scheduled job, the ops endpoint, or a test) and
upserted idempotently.

The mechanism (§6.2):

    Every Monday 00:00 UTC, for each (program × intake × protected_attribute):
      compute DI for the prior week
      if Δ > threshold:
        record a high-severity signal
        if the previous week also breached:
          set programs.matching_halted = true  (auto_halt)
          notify institution admin + ops

Disparate-impact ratio is the canonical 4/5ths form: DI = (lowest group positive
rate) / (highest group positive rate), Δ = |1 - DI|. A positive outcome is
"recommended-by-match" = fitness_score ≥ RECOMMEND_CUTOFF. Below MIN_SAMPLE
scored applicants in the cohort, the reading is flagged "insufficient sample"
(never "fair/unfair"), per §6.1.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.fairness import FairnessOverride, FairnessSignal
from unipaith.models.institution import IntakeRound, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentDataConsent, StudentProfile

logger = logging.getLogger(__name__)

# §6.1 — a positive outcome is "recommended by match".
RECOMMEND_CUTOFF = Decimal("0.60")
# §6.1 — minimum scored applicants per cohort/week for a meaningful DI.
MIN_SAMPLE = 50
# §6 default threshold (per-program tunable, §9 range 0.05–0.40).
DEFAULT_THRESHOLD = Decimal("0.20")
# §9 — override expiry default 1 week, max 4 weeks.
DEFAULT_OVERRIDE_WEEKS = 1
MAX_OVERRIDE_WEEKS = 4
THRESHOLD_MIN = Decimal("0.05")
THRESHOLD_MAX = Decimal("0.40")

# The protected attributes computed from data the platform actually holds.
# race/disability/veteran are tracked in the schema but emitted only where the
# institution collects them (not modeled in MVP) — so they surface as
# "insufficient sample" rather than a false fair/unfair reading.
COMPUTED_ATTRIBUTES = ("gender", "first_gen", "international", "nationality_region")

# Domestic set for the international heuristic (US-default platform; tunable per
# institution in a later phase). A student counts as international when their
# nationality is set and not domestic.
_DOMESTIC = {"united states", "united states of america", "usa", "us", "u.s.", "u.s.a."}

# Coarse nationality → region map for the nationality_region attribute. Default
# bucket is "other" so every value lands somewhere.
_REGION_BY_COUNTRY = {
    "united states": "north_america",
    "canada": "north_america",
    "mexico": "north_america",
    "united kingdom": "europe",
    "england": "europe",
    "france": "europe",
    "germany": "europe",
    "spain": "europe",
    "italy": "europe",
    "netherlands": "europe",
    "ireland": "europe",
    "china": "east_asia",
    "japan": "east_asia",
    "south korea": "east_asia",
    "korea": "east_asia",
    "taiwan": "east_asia",
    "hong kong": "east_asia",
    "india": "south_asia",
    "pakistan": "south_asia",
    "bangladesh": "south_asia",
    "sri lanka": "south_asia",
    "nepal": "south_asia",
    "nigeria": "africa",
    "kenya": "africa",
    "ghana": "africa",
    "south africa": "africa",
    "egypt": "middle_east",
    "saudi arabia": "middle_east",
    "united arab emirates": "middle_east",
    "turkey": "middle_east",
    "iran": "middle_east",
    "brazil": "south_america",
    "argentina": "south_america",
    "colombia": "south_america",
    "chile": "south_america",
    "australia": "oceania",
    "new zealand": "oceania",
}


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _region(nationality: str | None) -> str | None:
    if not nationality:
        return None
    return _REGION_BY_COUNTRY.get(nationality.strip().lower(), "other")


def _is_international(nationality: str | None) -> bool | None:
    if not nationality:
        return None
    return nationality.strip().lower() not in _DOMESTIC


def _attribute_value(attr: str, profile_gender, nationality, first_gen) -> str | None:
    """Resolve one student's value for a protected attribute (None = unknown)."""
    if attr == "gender":
        return profile_gender or None
    if attr == "first_gen":
        if first_gen is None:
            return None
        return "first_gen" if first_gen else "continuing_gen"
    if attr == "international":
        intl = _is_international(nationality)
        if intl is None:
            return None
        return "international" if intl else "domestic"
    if attr == "nationality_region":
        return _region(nationality)
    return None


class FairnessService:
    """Per-cohort disparate-impact governance + auto-halt (§6)."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._tracked_cache: dict[UUID, set[str]] = {}

    async def _tracked_attributes(self, institution_id: UUID) -> list[str]:
        """The computable attributes the institution opts to track (§9). An
        institution can disable an attribute it doesn't collect."""
        if institution_id not in self._tracked_cache:
            from unipaith.models.institution import Institution
            from unipaith.services.data_governance import resolve_governance

            inst = await self.db.get(Institution, institution_id)
            gov = resolve_governance(inst.data_governance if inst else None)
            self._tracked_cache[institution_id] = set(gov.get("protected_attributes_tracked", []))
        tracked = self._tracked_cache[institution_id]
        return [a for a in COMPUTED_ATTRIBUTES if a in tracked]

    # ── public: compute ──────────────────────────────────────────────────────

    async def run_weekly_compute(
        self,
        *,
        institution_id: UUID | None = None,
        program_id: UUID | None = None,
        as_of: date | None = None,
    ) -> list[FairnessSignal]:
        """Compute the fairness signals for the week containing ``as_of`` (default
        today). The scheduled Monday job, the ops endpoint, and the status read
        all funnel through here. Idempotent — re-running a week updates in place.
        """
        week_start = _monday(as_of or datetime.now(UTC).date())
        return await self.compute_for_week(
            week_start, institution_id=institution_id, program_id=program_id
        )

    async def compute_for_week(
        self,
        week_start: date,
        *,
        institution_id: UUID | None = None,
        program_id: UUID | None = None,
    ) -> list[FairnessSignal]:
        programs = await self._programs_in_scope(
            institution_id=institution_id, program_id=program_id
        )
        window_start = datetime(week_start.year, week_start.month, week_start.day, tzinfo=UTC)
        window_end = window_start + timedelta(days=7)
        out: list[FairnessSignal] = []
        for program in programs:
            out.extend(
                await self._compute_program_week(program, week_start, window_start, window_end)
            )
        await self.db.flush()
        return out

    async def _compute_program_week(
        self, program: Program, week_start: date, window_start: datetime, window_end: datetime
    ) -> list[FairnessSignal]:
        # Expire a stale override before evaluating, so expiry re-arms the halt.
        await self._expire_override_if_due(program)

        rows = (
            await self.db.execute(
                select(
                    MatchResult.fitness_score,
                    StudentProfile.gender_identity,
                    StudentProfile.nationality,
                    StudentDataConsent.first_generation_status,
                )
                .join(StudentProfile, StudentProfile.id == MatchResult.student_id)
                .join(
                    StudentDataConsent,
                    StudentDataConsent.student_id == MatchResult.student_id,
                    isouter=True,
                )
                .where(
                    MatchResult.program_id == program.id,
                    MatchResult.computed_at >= window_start,
                    MatchResult.computed_at < window_end,
                )
            )
        ).all()

        cohort_size = len(rows)
        threshold = Decimal(str(program.fairness_threshold or DEFAULT_THRESHOLD))
        intake_id = await self._active_intake_id(program.id)
        attributes = await self._tracked_attributes(program.institution_id)
        signals: list[FairnessSignal] = []
        triggered_auto_halt = False

        for attr in attributes:
            groups: dict[str, list[bool]] = {}
            for fitness, gender, nationality, first_gen in rows:
                val = _attribute_value(attr, gender, nationality, first_gen)
                if val is None:
                    continue
                positive = Decimal(str(fitness)) >= RECOMMEND_CUTOFF
                groups.setdefault(val, []).append(positive)

            di, delta = self._di_delta(groups)
            computable = sum(len(v) for v in groups.values())
            sample_sufficient = cohort_size >= MIN_SAMPLE and len(groups) >= 2 and computable >= 2

            breached = bool(sample_sufficient and delta is not None and delta > threshold)
            prior_breached = breached and await self._prior_week_breached(
                program.id, attr, week_start, threshold
            )

            if not sample_sufficient or delta is None:
                severity = "info"
            elif prior_breached and not program.fairness_override_active:
                severity = "auto_halt"
                triggered_auto_halt = True
            elif breached and program.fairness_override_active:
                severity = "override_active"
            elif breached:
                severity = "high"
            elif delta > (threshold * Decimal("0.75")):
                severity = "warning"
            else:
                severity = "info"

            note = None
            if not sample_sufficient:
                note = f"Insufficient sample ({cohort_size} scored, {len(groups)} group(s))."
            elif severity == "auto_halt":
                note = "Δ exceeded threshold for two consecutive weeks — matching halted."
            elif severity == "override_active":
                note = "Δ over threshold but an institution override is active."

            signal = await self._upsert_signal(
                program_id=program.id,
                intake_round_id=intake_id,
                week_start=week_start,
                protected_attribute=attr,
                cohort_size=cohort_size,
                di_ratio=di,
                delta=delta,
                severity=severity,
                sample_sufficient=sample_sufficient,
                notes=note,
            )
            signals.append(signal)

        if (
            triggered_auto_halt
            and settings.fairness_autohalt_v2_enabled
            and not program.matching_halted
        ):
            program.matching_halted = True
            await self.db.flush()
            await self._on_auto_halt(program, week_start)

        return signals

    # ── DI math ──────────────────────────────────────────────────────────────

    @staticmethod
    def _di_delta(groups: dict[str, list[bool]]) -> tuple[float | None, float | None]:
        """Canonical 4/5ths disparate-impact ratio + Δ.

        DI = lowest group positive-rate / highest group positive-rate (≤ 1).
        Δ = |1 - DI| = 1 - DI. None when fewer than two groups exist.
        """
        rates = {g: (sum(v) / len(v)) for g, v in groups.items() if v}
        if len(rates) < 2:
            return None, None
        p_max = max(rates.values())
        p_min = min(rates.values())
        if p_max == 0:
            di = 1.0  # everyone rejected equally — no disparate impact
        else:
            di = p_min / p_max
        delta = abs(1.0 - di)
        return round(di, 4), round(delta, 4)

    async def _prior_week_breached(
        self, program_id: UUID, attr: str, week_start: date, threshold: Decimal
    ) -> bool:
        prior = week_start - timedelta(days=7)
        row = (
            await self.db.execute(
                select(FairnessSignal).where(
                    FairnessSignal.program_id == program_id,
                    FairnessSignal.protected_attribute == attr,
                    FairnessSignal.week_start == prior,
                )
            )
        ).scalar_one_or_none()
        if row is None or row.delta is None or not row.sample_sufficient:
            return False
        return Decimal(str(row.delta)) > threshold

    async def _upsert_signal(self, **kw) -> FairnessSignal:
        existing = (
            await self.db.execute(
                select(FairnessSignal).where(
                    FairnessSignal.program_id == kw["program_id"],
                    FairnessSignal.protected_attribute == kw["protected_attribute"],
                    FairnessSignal.week_start == kw["week_start"],
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = FairnessSignal(**kw)
            self.db.add(existing)
        else:
            for k, v in kw.items():
                setattr(existing, k, v)
        await self.db.flush()
        return existing

    # ── halt + override ──────────────────────────────────────────────────────

    async def _expire_override_if_due(self, program: Program) -> None:
        if (
            program.fairness_override_active
            and program.override_expires_at is not None
            and program.override_expires_at <= datetime.now(UTC)
        ):
            program.fairness_override_active = False
            program.override_expires_at = None
            await self.db.flush()

    async def _on_auto_halt(self, program: Program, week_start: date) -> None:
        """Audit + notify the institution admin when a cohort auto-halts."""
        from unipaith.services.audit_service import AuditService
        from unipaith.services.notification_service import NotificationService

        try:
            await AuditService(self.db).log(
                institution_id=program.institution_id,
                actor_user_id=None,
                actor_role="system",
                action="fairness_auto_halt",
                category="fairness_signal",
                entity_type="program",
                entity_id=str(program.id),
                new_value={"matching_halted": True, "week_start": week_start.isoformat()},
                description=(
                    f"Matching auto-halted for '{program.program_name}': disparate-impact Δ "
                    "exceeded threshold for two consecutive weeks."
                ),
            )
        except Exception as exc:  # noqa: BLE001 — audit must not break compute
            logger.warning("fairness audit failed for program=%s: %s", program.id, exc)

        try:
            from unipaith.models.institution import Institution

            admin_user_id = (
                await self.db.execute(
                    select(Institution.admin_user_id).where(
                        Institution.id == program.institution_id
                    )
                )
            ).scalar_one_or_none()
            if admin_user_id:
                await NotificationService(self.db).notify(
                    user_id=admin_user_id,
                    notification_type="fairness_auto_halt",
                    title="Matching halted — fairness threshold",
                    body=(
                        f"'{program.program_name}' stopped scoring new applicants: "
                        "disparate-impact exceeded the threshold for two consecutive "
                        "weeks. Review the signal and, if warranted, request an override."
                    ),
                    action_url="/i/admissions?tab=fairness",
                    metadata={"program_id": str(program.id)},
                )
        except Exception as exc:  # noqa: BLE001 — notify is best-effort
            logger.warning("fairness notify failed for program=%s: %s", program.id, exc)

    async def request_override(
        self,
        *,
        institution_id: UUID,
        signal_id: UUID,
        admin_user_id: UUID,
        rationale: str,
        expires_weeks: int | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> FairnessOverride:
        """§6.3 — lift a halt with a written rationale (≥100 chars). Sets
        matching_halted=false, fairness_override_active=true, and an expiry."""
        from unipaith.core.exceptions import BadRequestException, NotFoundException

        rationale = (rationale or "").strip()
        if len(rationale) < 100:
            raise BadRequestException(
                "An override rationale must be at least 100 characters (§6.3)."
            )
        signal = await self.db.get(FairnessSignal, signal_id)
        if signal is None:
            raise NotFoundException("Fairness signal not found")
        program = await self.db.get(Program, signal.program_id)
        if program is None or program.institution_id != institution_id:
            raise NotFoundException("Fairness signal not found")

        if expires_weeks is None:
            # Fall back to the institution's configured default (§9).
            from unipaith.models.institution import Institution
            from unipaith.services.data_governance import resolve_governance

            inst = await self.db.get(Institution, institution_id)
            gov = resolve_governance(inst.data_governance if inst else None)
            expires_weeks = gov.get("override_expiry_weeks_default", DEFAULT_OVERRIDE_WEEKS)

        weeks = max(1, min(MAX_OVERRIDE_WEEKS, expires_weeks or DEFAULT_OVERRIDE_WEEKS))
        expires_at = datetime.now(UTC) + timedelta(weeks=weeks)

        override = FairnessOverride(
            fairness_signal_id=signal.id,
            institution_admin_id=admin_user_id,
            rationale=rationale,
            override_expires_at=expires_at,
        )
        self.db.add(override)
        program.matching_halted = False
        program.fairness_override_active = True
        program.override_expires_at = expires_at
        signal.severity = "override_active"
        await self.db.flush()

        from unipaith.services.audit_service import AuditService

        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=admin_user_id,
            actor_role="institution_admin",
            action="fairness_override",
            category="fairness_signal_override",
            entity_type="program",
            entity_id=str(program.id),
            reason=rationale,
            new_value={
                "signal_id": str(signal.id),
                "override_expires_at": expires_at.isoformat(),
                "protected_attribute": signal.protected_attribute,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return override

    async def set_threshold(
        self,
        *,
        institution_id: UUID,
        program_id: UUID,
        threshold: Decimal,
        admin_user_id: UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Program:
        from unipaith.core.exceptions import BadRequestException, NotFoundException

        if not (THRESHOLD_MIN <= threshold <= THRESHOLD_MAX):
            raise BadRequestException("Fairness threshold must be between 0.05 and 0.40 (§9).")
        program = await self.db.get(Program, program_id)
        if program is None or program.institution_id != institution_id:
            raise NotFoundException("Program not found")
        old = program.fairness_threshold
        program.fairness_threshold = threshold
        await self.db.flush()

        from unipaith.services.audit_service import AuditService

        await AuditService(self.db).log(
            institution_id=institution_id,
            actor_user_id=admin_user_id,
            actor_role="institution_admin",
            action="fairness_threshold_change",
            category="config_change",
            entity_type="program",
            entity_id=str(program.id),
            old_value={"fairness_threshold": str(old)},
            new_value={"fairness_threshold": str(threshold)},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return program

    # ── reads ────────────────────────────────────────────────────────────────

    async def get_status(self, institution_id: UUID) -> dict:
        """Per-program halt status + 4-week DI trend + latest signals + overrides.

        Lazily computes the current week so the dashboard/heatmap always reflects
        fresh data (aggregate-on-read).
        """
        await self.run_weekly_compute(institution_id=institution_id)

        programs = await self._programs_in_scope(institution_id=institution_id)
        today = datetime.now(UTC).date()
        weeks = [_monday(today) - timedelta(days=7 * i) for i in range(3, -1, -1)]

        program_blocks: list[dict] = []
        any_halted = False
        any_warning = False
        for program in programs:
            sigs = (
                (
                    await self.db.execute(
                        select(FairnessSignal)
                        .where(
                            FairnessSignal.program_id == program.id,
                            FairnessSignal.week_start.in_(weeks),
                        )
                        .order_by(FairnessSignal.week_start.asc())
                    )
                )
                .scalars()
                .all()
            )
            by_attr: dict[str, dict[str, float | None]] = {}
            trend: dict[str, float] = {w.isoformat(): 0.0 for w in weeks}
            latest_severity = "info"
            for s in sigs:
                by_attr.setdefault(s.protected_attribute, {})[s.week_start.isoformat()] = (
                    float(s.delta) if s.delta is not None else None
                )
                if s.delta is not None:
                    trend[s.week_start.isoformat()] = max(
                        trend[s.week_start.isoformat()], float(s.delta)
                    )
                if _severity_rank(s.severity) > _severity_rank(latest_severity):
                    latest_severity = s.severity

            if program.matching_halted:
                status = "halted"
                any_halted = True
            elif latest_severity in ("high", "warning") or program.fairness_override_active:
                status = "warning"
                any_warning = True
            else:
                status = "ok"

            program_blocks.append(
                {
                    "program_id": str(program.id),
                    "program_name": program.program_name,
                    "matching_halted": program.matching_halted,
                    "fairness_override_active": program.fairness_override_active,
                    "override_expires_at": program.override_expires_at.isoformat()
                    if program.override_expires_at
                    else None,
                    "fairness_threshold": float(program.fairness_threshold or DEFAULT_THRESHOLD),
                    "status": status,
                    "trend": [
                        {"week_start": w.isoformat(), "delta": round(trend[w.isoformat()], 4)}
                        for w in weeks
                    ],
                    "attributes": by_attr,
                }
            )

        overall = "halted" if any_halted else ("warning" if any_warning else "ok")
        return {
            "overall_status": overall,
            "threshold_default": float(DEFAULT_THRESHOLD),
            "min_sample": MIN_SAMPLE,
            "weeks": [w.isoformat() for w in weeks],
            "programs": program_blocks,
        }

    async def list_signals(
        self, institution_id: UUID, *, program_id: UUID | None = None, limit: int = 200
    ) -> list[dict]:
        prog_ids = [p.id for p in await self._programs_in_scope(institution_id=institution_id)]
        if program_id is not None:
            prog_ids = [pid for pid in prog_ids if pid == program_id]
        if not prog_ids:
            return []
        rows = (
            (
                await self.db.execute(
                    select(FairnessSignal)
                    .where(FairnessSignal.program_id.in_(prog_ids))
                    .order_by(FairnessSignal.week_start.desc(), FairnessSignal.created_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )
        return [_signal_dict(s) for s in rows]

    async def list_overrides(
        self, institution_id: UUID, *, program_id: UUID | None = None
    ) -> list[dict]:
        prog_ids = [p.id for p in await self._programs_in_scope(institution_id=institution_id)]
        if program_id is not None:
            prog_ids = [pid for pid in prog_ids if pid == program_id]
        if not prog_ids:
            return []
        rows = (
            await self.db.execute(
                select(FairnessOverride, FairnessSignal, Program.program_name)
                .join(FairnessSignal, FairnessSignal.id == FairnessOverride.fairness_signal_id)
                .join(Program, Program.id == FairnessSignal.program_id)
                .where(FairnessSignal.program_id.in_(prog_ids))
                .order_by(FairnessOverride.created_at.desc())
            )
        ).all()
        out = []
        for ov, sig, prog_name in rows:
            out.append(
                {
                    "id": str(ov.id),
                    "program_id": str(sig.program_id),
                    "program_name": prog_name,
                    "protected_attribute": sig.protected_attribute,
                    "rationale": ov.rationale,
                    "override_expires_at": ov.override_expires_at.isoformat(),
                    "revoked_at": ov.revoked_at.isoformat() if ov.revoked_at else None,
                    "active": ov.revoked_at is None and ov.override_expires_at > datetime.now(UTC),
                    "created_at": ov.created_at.isoformat(),
                }
            )
        return out

    async def halted_program_ids(self) -> set[UUID]:
        """Program ids whose matching is currently halted (no live override).

        Used by the match-scoring gate. A program with an active, unexpired
        override is NOT halted.
        """
        now = datetime.now(UTC)
        rows = (
            (
                await self.db.execute(
                    select(Program.id).where(
                        Program.matching_halted.is_(True),
                        or_(
                            Program.fairness_override_active.is_(False),
                            and_(
                                Program.fairness_override_active.is_(True),
                                Program.override_expires_at.is_(None),
                            ),
                            Program.override_expires_at <= now,
                        ),
                    )
                )
            )
            .scalars()
            .all()
        )
        return set(rows)

    # ── helpers ──────────────────────────────────────────────────────────────

    async def _programs_in_scope(
        self, *, institution_id: UUID | None = None, program_id: UUID | None = None
    ) -> list[Program]:
        stmt = select(Program)
        if program_id is not None:
            stmt = stmt.where(Program.id == program_id)
        elif institution_id is not None:
            stmt = stmt.where(Program.institution_id == institution_id)
        return list((await self.db.execute(stmt)).scalars().all())

    async def _active_intake_id(self, program_id: UUID) -> UUID | None:
        return (
            await self.db.execute(
                select(IntakeRound.id)
                .where(IntakeRound.program_id == program_id, IntakeRound.is_active.is_(True))
                .order_by(IntakeRound.sort_order.asc())
                .limit(1)
            )
        ).scalar_one_or_none()


_SEVERITY_ORDER = {"info": 0, "warning": 1, "high": 2, "override_active": 3, "auto_halt": 4}


def _severity_rank(s: str) -> int:
    return _SEVERITY_ORDER.get(s, 0)


def _signal_dict(s: FairnessSignal) -> dict:
    return {
        "id": str(s.id),
        "program_id": str(s.program_id),
        "week_start": s.week_start.isoformat(),
        "protected_attribute": s.protected_attribute,
        "cohort_size": s.cohort_size,
        "di_ratio": float(s.di_ratio) if s.di_ratio is not None else None,
        "delta": float(s.delta) if s.delta is not None else None,
        "severity": s.severity,
        "sample_sufficient": s.sample_sufficient,
        "notes": s.notes,
        "created_at": s.created_at.isoformat(),
    }
