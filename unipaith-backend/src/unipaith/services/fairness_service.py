"""Spec 46 §6 — Fairness governance: disparate-impact compute + auto-halt.

The contractual commitment (Landing_MVP, verbatim):

    "If disparate-impact Δ exceeds 0.20 for two consecutive weeks, the model stops
     scoring new applicants for that cohort."

This service computes the weekly disparate-impact reading per (program × week ×
protected attribute), persists ``FairnessSignal`` rows, flips
``programs.matching_halted`` on the second consecutive breach, and runs the
admin override workflow (§6.3). It is deterministic statistics — **no LLM agent**.

The DI math is exposed as pure module-level functions so it is trivially
unit-testable without a DB. ``FairnessService`` is the DB-bound orchestrator.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.fairness import FairnessOverride, FairnessSignal
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.workflow import Notification

logger = logging.getLogger(__name__)

# ── Tunable constants (Spec 46 §6.1) ─────────────────────────────────────────
# "Recommended-by-match" = the binary positive outcome DI is computed over.
# 0.65 aligns with the "target or better" cutoff in match_banding's
# fitness-only fallback (Spec 09 §6).
RECOMMEND_THRESHOLD = Decimal("0.65")
# §6.1 — minimum scored applicants per cohort-week to compute a meaningful DI.
SAMPLE_FLOOR = 50
# Default per-program Δ ceiling (§6.2). Overridable per program (§9, 0.05–0.40).
DEFAULT_THRESHOLD = Decimal("0.20")
# A reading within this margin *below* the threshold is surfaced as a warning.
WARN_MARGIN = Decimal("0.05")
# Override window (§6.3): default 1 week, max 4.
OVERRIDE_DEFAULT_WEEKS = 1
OVERRIDE_MAX_WEEKS = 4
# §6.3 — a written rationale is required to override a halt.
MIN_RATIONALE_CHARS = 100
# DI ratio is clamped to fit Numeric(6,4) and avoid absurd values when a
# reference group has a zero positive rate.
_DI_CAP = Decimal("9.9999")

# Attributes we actually compute. race/disability are in the schema enum for
# completeness but are only computable where the institution collects them
# (no column today) — so we emit no signal for them rather than noise.
COMPUTED_ATTRIBUTES = ("gender", "first_gen", "international", "veteran", "nationality_region")
# For binary protected attributes, the protected (minority) subgroup label.
_BINARY_MINORITY = {
    "first_gen": "first_gen",
    "veteran": "veteran",
    "international": "international",
}

_DOMESTIC_RESIDENCY = {
    "in_state",
    "out_of_state",
    "resident",
    "domestic",
    "us_citizen",
    "permanent_resident",
    "citizen",
}
_INTL_RESIDENCY = {"international", "non_resident_alien", "foreign", "nonresident"}
_DOMESTIC_NATIONALITY = {"united states", "usa", "us", "u.s.", "u.s.a.", "american"}


def week_start_of(d: date) -> date:
    """The Monday (week start) of the week containing ``d`` (§6.2 cohort week)."""
    return d - timedelta(days=d.weekday())


def _q4(value: float | Decimal) -> Decimal:
    """Quantize to 4 decimal places for Numeric(6,4) storage."""
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def disparate_impact(minority_rate: float, majority_rate: float) -> float:
    """DI = P(positive | minority) / P(positive | majority), clamped to [0, 9.9999].

    When the majority positive rate is 0: returns 1.0 if neither group has any
    positives (no disparity), else the clamped cap (a reverse disparity that
    still trips the Δ threshold).
    """
    if majority_rate <= 0:
        return 1.0 if minority_rate <= 0 else float(_DI_CAP)
    di = minority_rate / majority_rate
    return min(di, float(_DI_CAP))


def severity_for(delta: float | None, threshold: float, *, sample_sufficient: bool) -> str:
    """Map a Δ reading to the §6.5 severity ladder (excluding auto_halt, which is
    a cross-week escalation decided by the service)."""
    if not sample_sufficient or delta is None:
        return "info"
    if delta > threshold:
        return "high"
    if delta >= threshold - float(WARN_MARGIN):
        return "warning"
    return "info"


@dataclass
class _AttrReading:
    attribute: str
    cohort_size: int
    di_ratio: float | None
    delta: float | None
    sample_sufficient: bool
    severity: str
    detail: dict
    notes: str | None


def _international_label(profile_row) -> str | None:
    """Best-effort international/domestic classification (MVP heuristic).

    Prefers an explicit residency-for-tuition status; falls back to nationality
    vs a US-domestic baseline. Returns None when nothing is known.
    """
    res = (profile_row.residency_status_for_tuition or "").strip().lower()
    if res in _DOMESTIC_RESIDENCY:
        return "domestic"
    if res in _INTL_RESIDENCY:
        return "international"
    nat = (profile_row.nationality or "").strip().lower()
    if not nat:
        return None
    return "domestic" if nat in _DOMESTIC_NATIONALITY else "international"


def _attribute_values(row) -> dict[str, str | None]:
    """Extract each protected-attribute category value from a joined row."""
    gender = (row.gender_identity or "").strip() or None
    nationality = (row.nationality or "").strip() or None
    fg = row.first_generation_status
    vet = row.veteran_status
    return {
        "gender": gender,
        "nationality_region": nationality,
        "first_gen": ("first_gen" if fg is True else "not_first_gen" if fg is False else None),
        "veteran": ("veteran" if vet is True else "non_veteran" if vet is False else None),
        "international": _international_label(row),
    }


def _reading_for_attribute(
    attr: str, groups: dict[str, list[int]], threshold: float
) -> _AttrReading:
    """Compute the DI reading for one attribute from ``{label: [n, positives]}``."""
    cohort_size = sum(n for n, _ in groups.values())
    if cohort_size < SAMPLE_FLOOR:
        return _AttrReading(
            attribute=attr,
            cohort_size=cohort_size,
            di_ratio=None,
            delta=None,
            sample_sufficient=False,
            severity="info",
            detail={"threshold": threshold, "reason": "insufficient_sample"},
            notes=f"insufficient sample (n={cohort_size} < {SAMPLE_FLOOR})",
        )

    # Split into minority (protected) vs majority (reference).
    if attr in _BINARY_MINORITY:
        min_label = _BINARY_MINORITY[attr]
        min_n, min_pos = groups.get(min_label, [0, 0])
        maj_n = sum(n for lbl, (n, _) in groups.items() if lbl != min_label)
        maj_pos = sum(p for lbl, (_, p) in groups.items() if lbl != min_label)
        maj_label = "reference"
    else:
        # Multi-class: majority = modal group, minority = the aggregate rest.
        maj_label = max(groups, key=lambda lbl: groups[lbl][0])
        maj_n, maj_pos = groups[maj_label]
        min_n = sum(n for lbl, (n, _) in groups.items() if lbl != maj_label)
        min_pos = sum(p for lbl, (_, p) in groups.items() if lbl != maj_label)
        min_label = "other"

    if min_n == 0 or maj_n == 0:
        return _AttrReading(
            attribute=attr,
            cohort_size=cohort_size,
            di_ratio=None,
            delta=None,
            sample_sufficient=False,
            severity="info",
            detail={"threshold": threshold, "reason": "single_group_cohort"},
            notes="single-group cohort — no comparison group",
        )

    min_rate = min_pos / min_n
    maj_rate = maj_pos / maj_n
    di = disparate_impact(min_rate, maj_rate)
    delta = abs(1.0 - di)
    severity = severity_for(delta, threshold, sample_sufficient=True)
    return _AttrReading(
        attribute=attr,
        cohort_size=cohort_size,
        di_ratio=di,
        delta=delta,
        sample_sufficient=True,
        severity=severity,
        detail={
            "threshold": threshold,
            "minority_label": min_label,
            "majority_label": maj_label,
            "minority_n": min_n,
            "majority_n": maj_n,
            "minority_rate": round(min_rate, 4),
            "majority_rate": round(maj_rate, 4),
        },
        notes=None,
    )


class FairnessService:
    """DB-bound orchestrator for the fairness auto-halt commitment."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    # ── core compute ─────────────────────────────────────────────────────────

    async def compute_week(
        self,
        program_id: UUID,
        week_start: date,
        *,
        actor_user_id: UUID | None = None,
        do_halt: bool = True,
    ) -> list[FairnessSignal]:
        """Compute + persist DI signals for one (program, week) across all
        computed attributes; flip the halt on a second consecutive breach.

        Idempotent: re-running upserts the signal rows for the week.
        """
        program = await self.db.get(Program, program_id)
        if program is None:
            return []
        threshold = float(program.fairness_threshold or DEFAULT_THRESHOLD)

        # Lapse an expired override before deciding anything this week.
        await self._lapse_expired_override(program)

        week_start_dt = datetime.combine(week_start, time.min, tzinfo=UTC)
        week_end_dt = week_start_dt + timedelta(days=7)

        rows = (
            await self.db.execute(
                select(
                    MatchResult.fitness_score,
                    StudentProfile.gender_identity,
                    StudentProfile.nationality,
                    StudentProfile.residency_status_for_tuition,
                    StudentDataConsent.first_generation_status,
                    StudentDataConsent.veteran_status,
                )
                .join(StudentProfile, MatchResult.student_id == StudentProfile.id)
                .outerjoin(StudentDataConsent, StudentDataConsent.student_id == StudentProfile.id)
                .where(
                    MatchResult.program_id == program_id,
                    MatchResult.computed_at >= week_start_dt,
                    MatchResult.computed_at < week_end_dt,
                )
            )
        ).all()

        # Aggregate {attribute: {category: [n, positives]}}.
        agg: dict[str, dict[str, list[int]]] = {a: {} for a in COMPUTED_ATTRIBUTES}
        for row in rows:
            positive = 1 if (row.fitness_score or Decimal(0)) >= RECOMMEND_THRESHOLD else 0
            for attr, value in _attribute_values(row).items():
                if value is None:
                    continue
                bucket = agg[attr].setdefault(value, [0, 0])
                bucket[0] += 1
                bucket[1] += positive

        out: list[FairnessSignal] = []
        for attr in COMPUTED_ATTRIBUTES:
            groups = agg[attr]
            if not groups:
                continue  # nothing collected for this attribute this week
            reading = _reading_for_attribute(attr, groups, threshold)
            signal = await self._upsert_signal(program_id, week_start, reading)
            out.append(signal)

            if do_halt and reading.severity == "high" and not self._override_active(program):
                if await self._prior_week_breached(program_id, week_start, attr):
                    await self._trigger_halt(program, signal, attr, actor_user_id)

        await self.db.flush()
        return out

    async def run_weekly_compute(
        self,
        *,
        as_of: date | None = None,
        program_id: UUID | None = None,
        institution_id: UUID | None = None,
        weeks_back: int = 4,
    ) -> int:
        """Driver: compute the last ``weeks_back`` completed weeks (oldest→newest,
        so the consecutive-breach check sees prior-week signals) for the target
        programs. Returns the number of (program, week) computations run.

        A real Monday-00:00-UTC scheduler would call this with weeks_back=2; the
        on-demand recompute endpoint uses the default to backfill trend data.
        """
        anchor = week_start_of(as_of or self._now().date())
        weeks = [anchor - timedelta(days=7 * i) for i in range(weeks_back - 1, -1, -1)]

        program_ids = await self._target_program_ids(program_id, institution_id)
        count = 0
        for pid in program_ids:
            for ws in weeks:
                await self.compute_week(pid, ws)
                count += 1
        return count

    # ── override workflow (§6.3) ─────────────────────────────────────────────

    async def apply_override(
        self,
        program_id: UUID,
        *,
        admin_user_id: UUID,
        rationale: str,
        weeks: int = OVERRIDE_DEFAULT_WEEKS,
        signal_id: UUID | None = None,
    ) -> FairnessOverride:
        """Resume scoring for a halted program. Requires a written rationale
        (≥100 chars). Sets an expiry (default 1 week, max 4) and audit-logs."""
        rationale = (rationale or "").strip()
        if len(rationale) < MIN_RATIONALE_CHARS:
            raise ValueError(
                f"Override rationale must be at least {MIN_RATIONALE_CHARS} characters."
            )
        weeks = max(1, min(int(weeks), OVERRIDE_MAX_WEEKS))
        program = await self.db.get(Program, program_id)
        if program is None:
            raise ValueError("Program not found")

        expires_at = self._now() + timedelta(days=7 * weeks)
        program.matching_halted = False
        program.fairness_override_active = True
        program.fairness_override_expires_at = expires_at

        override = FairnessOverride(
            fairness_signal_id=signal_id,
            program_id=program_id,
            institution_admin_id=admin_user_id,
            rationale=rationale,
            override_expires_at=expires_at,
        )
        self.db.add(override)
        await self.db.flush()

        await self._audit(
            program,
            actor_user_id=admin_user_id,
            action="fairness_override_apply",
            reason=rationale,
            new_value={
                "program_id": str(program_id),
                "expires_at": expires_at.isoformat(),
                "weeks": weeks,
            },
        )
        return override

    async def revoke_override(self, program_id: UUID, *, admin_user_id: UUID) -> None:
        """Cancel an active override and re-halt the program."""
        program = await self.db.get(Program, program_id)
        if program is None:
            raise ValueError("Program not found")
        active = (
            (
                await self.db.execute(
                    select(FairnessOverride)
                    .where(
                        FairnessOverride.program_id == program_id,
                        FairnessOverride.revoked_at.is_(None),
                    )
                    .order_by(FairnessOverride.created_at.desc())
                )
            )
            .scalars()
            .first()
        )
        if active is not None:
            active.revoked_at = self._now()
        program.fairness_override_active = False
        program.fairness_override_expires_at = None
        program.matching_halted = True
        await self.db.flush()
        await self._audit(
            program,
            actor_user_id=admin_user_id,
            action="fairness_override_revoke",
            reason="Override revoked; scoring re-halted.",
            new_value={"program_id": str(program_id)},
        )

    async def set_threshold(
        self, program_id: UUID, *, threshold: float, admin_user_id: UUID
    ) -> Program:
        """Set the per-program Δ ceiling (§9, range 0.05–0.40), audit-logged."""
        if not (0.05 <= threshold <= 0.40):
            raise ValueError("Fairness threshold must be between 0.05 and 0.40.")
        program = await self.db.get(Program, program_id)
        if program is None:
            raise ValueError("Program not found")
        old = float(program.fairness_threshold or DEFAULT_THRESHOLD)
        program.fairness_threshold = _q_threshold(threshold)
        await self.db.flush()
        await self._audit(
            program,
            actor_user_id=admin_user_id,
            action="fairness_threshold_change",
            reason=f"Threshold changed {old:.2f} → {threshold:.2f}",
            old_value={"threshold": old},
            new_value={"threshold": threshold},
        )
        return program

    # ── dashboard reads ──────────────────────────────────────────────────────

    async def get_overview(self, institution_id: UUID) -> dict:
        """Compact panel payload (§6.4): status + halted programs + latest signals."""
        programs = await self._institution_programs(institution_id)
        prog_by_id = {p.id: p for p in programs}
        halted = [self._program_brief(p) for p in programs if p.matching_halted]

        signals = await self._recent_signals(list(prog_by_id.keys()), limit=8)
        any_high = any(s.severity in ("high", "auto_halt") for s in signals)
        any_warn = any(s.severity == "warning" for s in signals)
        if halted:
            status = "red"
        elif any_high:
            status = "red"
        elif any_warn:
            status = "yellow"
        else:
            status = "green"

        return {
            "status": status,
            "halted_count": len(halted),
            "halted_programs": halted,
            "program_count": len(programs),
            "latest_signals": [self._signal_dict(s, prog_by_id) for s in signals],
        }

    async def get_cohorts(self, institution_id: UUID) -> dict:
        """Full-page payload (§6.4): per program×attribute 4-week trend + halt +
        override history + threshold."""
        programs = await self._institution_programs(institution_id)
        prog_by_id = {p.id: p for p in programs}
        if not programs:
            return {"programs": [], "overrides": []}

        signals = await self._recent_signals(list(prog_by_id.keys()), limit=2000)
        # Group: program -> attribute -> [signals oldest→newest]
        by_prog: dict[UUID, dict[str, list]] = {}
        for s in sorted(signals, key=lambda x: x.week_start):
            by_prog.setdefault(s.program_id, {}).setdefault(s.protected_attribute, []).append(s)

        program_blocks = []
        for p in programs:
            attrs = by_prog.get(p.id, {})
            program_blocks.append(
                {
                    **self._program_brief(p),
                    "fairness_threshold": float(p.fairness_threshold or DEFAULT_THRESHOLD),
                    "override_expires_at": (
                        p.fairness_override_expires_at.isoformat()
                        if p.fairness_override_expires_at
                        else None
                    ),
                    "attributes": [
                        {
                            "attribute": attr,
                            "series": [self._signal_dict(s, prog_by_id) for s in series],
                            "latest": self._signal_dict(series[-1], prog_by_id) if series else None,
                        }
                        for attr, series in sorted(attrs.items())
                    ],
                }
            )

        overrides = await self._override_history(list(prog_by_id.keys()))
        return {
            "programs": program_blocks,
            "overrides": [self._override_dict(o, prog_by_id) for o in overrides],
        }

    # ── internals ─────────────────────────────────────────────────────────────

    async def _upsert_signal(
        self, program_id: UUID, week_start: date, reading: _AttrReading
    ) -> FairnessSignal:
        existing = (
            (
                await self.db.execute(
                    select(FairnessSignal).where(
                        FairnessSignal.program_id == program_id,
                        FairnessSignal.week_start == week_start,
                        FairnessSignal.protected_attribute == reading.attribute,
                    )
                )
            )
            .scalars()
            .first()
        )

        di = _q4(reading.di_ratio) if reading.di_ratio is not None else None
        delta = _q4(reading.delta) if reading.delta is not None else None

        if existing is None:
            signal = FairnessSignal(
                program_id=program_id,
                week_start=week_start,
                protected_attribute=reading.attribute,
                cohort_size=reading.cohort_size,
                di_ratio=di,
                delta=delta,
                severity=reading.severity,
                sample_sufficient=reading.sample_sufficient,
                notes=reading.notes,
                detail=reading.detail,
            )
            self.db.add(signal)
        else:
            existing.cohort_size = reading.cohort_size
            existing.di_ratio = di
            existing.delta = delta
            # Don't downgrade an auto_halt that already escalated this week.
            if existing.severity != "auto_halt":
                existing.severity = reading.severity
            existing.sample_sufficient = reading.sample_sufficient
            existing.notes = reading.notes
            existing.detail = reading.detail
            signal = existing
        await self.db.flush()
        return signal

    async def _prior_week_breached(
        self, program_id: UUID, week_start: date, attribute: str
    ) -> bool:
        prior = week_start - timedelta(days=7)
        row = (
            (
                await self.db.execute(
                    select(FairnessSignal.severity).where(
                        FairnessSignal.program_id == program_id,
                        FairnessSignal.week_start == prior,
                        FairnessSignal.protected_attribute == attribute,
                    )
                )
            )
            .scalars()
            .first()
        )
        return row in ("high", "auto_halt")

    async def _trigger_halt(
        self,
        program: Program,
        signal: FairnessSignal,
        attribute: str,
        actor_user_id: UUID | None,
    ) -> None:
        signal.severity = "auto_halt"
        if signal.notes:
            signal.notes = f"{signal.notes} · auto-halt: 2nd consecutive breach"
        else:
            signal.notes = "auto-halt: 2nd consecutive weekly breach"
        was_halted = program.matching_halted
        program.matching_halted = True
        await self.db.flush()
        if not was_halted:  # only notify/audit on the transition
            await self._notify_admin(program, attribute, signal)
            await self._audit(
                program,
                actor_user_id=actor_user_id,
                action="fairness_auto_halt",
                reason=(
                    f"Disparate-impact Δ exceeded the threshold for '{attribute}' "
                    "two consecutive weeks; scoring halted (Spec 46 §6.2)."
                ),
                new_value={
                    "program_id": str(program.id),
                    "attribute": attribute,
                    "week_start": signal.week_start.isoformat(),
                    "delta": float(signal.delta) if signal.delta is not None else None,
                },
            )

    async def _lapse_expired_override(self, program: Program) -> None:
        if (
            program.fairness_override_active
            and program.fairness_override_expires_at is not None
            and program.fairness_override_expires_at <= self._now()
        ):
            program.fairness_override_active = False
            await self.db.flush()

    def _override_active(self, program: Program) -> bool:
        return bool(
            program.fairness_override_active
            and program.fairness_override_expires_at is not None
            and program.fairness_override_expires_at > self._now()
        )

    async def _notify_admin(self, program: Program, attribute: str, signal: FairnessSignal) -> None:
        """Best-effort in-app notification to the institution admin (§6.2)."""
        try:
            institution = await self.db.get(Institution, program.institution_id)
            if institution is None:
                return
            self.db.add(
                Notification(
                    user_id=institution.admin_user_id,
                    notification_type="fairness_auto_halt",
                    title="Matching paused — fairness threshold breached",
                    body=(
                        f"Scoring for “{program.program_name}” has been paused: the "
                        f"disparate-impact gap for {attribute.replace('_', ' ')} exceeded "
                        "your threshold for two consecutive weeks. Review and override "
                        "in Admissions → Fairness."
                    ),
                    action_url="/i/admissions?tab=fairness",
                    metadata_={"program_id": str(program.id), "attribute": attribute},
                )
            )
            await self.db.flush()
        except Exception as exc:  # noqa: BLE001 — notification must not break compute
            logger.warning("fairness halt notification failed for program=%s: %s", program.id, exc)

    async def _audit(
        self,
        program: Program,
        *,
        actor_user_id: UUID | None,
        action: str,
        reason: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        """Best-effort audit-log write (reuses the §36 fairness category)."""
        try:
            from unipaith.services.audit_service import AuditService

            await AuditService(self.db).log(
                institution_id=program.institution_id,
                actor_user_id=actor_user_id,
                action=action,
                category="fairness_signal_override",
                entity_type="program",
                entity_id=str(program.id),
                reason=reason,
                old_value=old_value,
                new_value=new_value,
            )
        except Exception as exc:  # noqa: BLE001 — audit must not break compute
            logger.warning("fairness audit write failed for program=%s: %s", program.id, exc)

    async def _institution_programs(self, institution_id: UUID) -> list[Program]:
        return list(
            (await self.db.execute(select(Program).where(Program.institution_id == institution_id)))
            .scalars()
            .all()
        )

    async def _target_program_ids(
        self, program_id: UUID | None, institution_id: UUID | None
    ) -> list[UUID]:
        if program_id is not None:
            return [program_id]
        if institution_id is not None:
            return [p.id for p in await self._institution_programs(institution_id)]
        return list((await self.db.execute(select(Program.id))).scalars().all())

    async def _recent_signals(self, program_ids: list[UUID], *, limit: int) -> list[FairnessSignal]:
        if not program_ids:
            return []
        return list(
            (
                await self.db.execute(
                    select(FairnessSignal)
                    .where(FairnessSignal.program_id.in_(program_ids))
                    .order_by(FairnessSignal.week_start.desc(), FairnessSignal.created_at.desc())
                    .limit(limit)
                )
            )
            .scalars()
            .all()
        )

    async def _override_history(self, program_ids: list[UUID]) -> list[FairnessOverride]:
        if not program_ids:
            return []
        return list(
            (
                await self.db.execute(
                    select(FairnessOverride)
                    .where(FairnessOverride.program_id.in_(program_ids))
                    .order_by(FairnessOverride.created_at.desc())
                    .limit(200)
                )
            )
            .scalars()
            .all()
        )

    @staticmethod
    def _program_brief(p: Program) -> dict:
        return {
            "program_id": str(p.id),
            "program_name": p.program_name,
            "matching_halted": p.matching_halted,
            "fairness_override_active": p.fairness_override_active,
        }

    @staticmethod
    def _signal_dict(s: FairnessSignal, prog_by_id: dict[UUID, Program]) -> dict:
        prog = prog_by_id.get(s.program_id)
        return {
            "id": str(s.id),
            "program_id": str(s.program_id),
            "program_name": prog.program_name if prog else None,
            "week_start": s.week_start.isoformat(),
            "attribute": s.protected_attribute,
            "cohort_size": s.cohort_size,
            "di_ratio": float(s.di_ratio) if s.di_ratio is not None else None,
            "delta": float(s.delta) if s.delta is not None else None,
            "severity": s.severity,
            "sample_sufficient": s.sample_sufficient,
            "notes": s.notes,
            "detail": s.detail or {},
        }

    @staticmethod
    def _override_dict(o: FairnessOverride, prog_by_id: dict[UUID, Program]) -> dict:
        prog = prog_by_id.get(o.program_id)
        return {
            "id": str(o.id),
            "program_id": str(o.program_id),
            "program_name": prog.program_name if prog else None,
            "rationale": o.rationale,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "override_expires_at": (
                o.override_expires_at.isoformat() if o.override_expires_at else None
            ),
            "revoked_at": o.revoked_at.isoformat() if o.revoked_at else None,
            "active": o.revoked_at is None,
        }


def _q_threshold(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
