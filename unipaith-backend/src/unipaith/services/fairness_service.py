"""Fairness auto-halt service (gap audit G-I5 / Spec 43 §6).

Computes the matching model's disparate impact per program × protected-attribute
× week (4/5ths rule) and halts a program's matching when the disparate-impact
delta breaches the threshold for two consecutive weeks. A human admin can
override the halt; the override is audit-logged by the caller.

"Selection" here means the matcher recommended the program to the student
(fitness_score >= RECOMMEND_BAR) — i.e. the question is whether the model
recommends at materially different rates across protected groups.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.fairness import (
    DEFAULT_DISPARATE_IMPACT_THRESHOLD,
    PROTECTED_ATTRIBUTES,
    FairnessSignal,
)
from unipaith.models.institution import Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentDataConsent, StudentProfile

logger = logging.getLogger(__name__)

RECOMMEND_BAR = 0.5  # fitness at/above which the program is "recommended"
MIN_GROUP_SIZE = 5  # ignore groups too small to be statistically meaningful
CONSECUTIVE_WEEKS_TO_HALT = 2


def _attr_value(attr: str, gender, nationality, first_gen) -> str | None:
    if attr == "gender_identity":
        return gender
    if attr == "nationality":
        return nationality
    if attr == "first_generation_status":
        if first_gen is None:
            return None
        return "first_generation" if first_gen else "continuing_generation"
    return None


class FairnessService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_weekly_signals(
        self, program_id: UUID, week_start: date
    ) -> list[FairnessSignal]:
        """Compute + upsert a FairnessSignal per protected attribute for the week."""
        start_dt = datetime(week_start.year, week_start.month, week_start.day, tzinfo=UTC)
        end_dt = start_dt + timedelta(days=7)

        rows = (
            await self.db.execute(
                select(
                    MatchResult.fitness_score,
                    StudentProfile.gender_identity,
                    StudentProfile.nationality,
                    StudentDataConsent.first_generation_status,
                )
                .join(StudentProfile, MatchResult.student_id == StudentProfile.id)
                .outerjoin(
                    StudentDataConsent,
                    StudentDataConsent.student_id == StudentProfile.id,
                )
                .where(
                    MatchResult.program_id == program_id,
                    MatchResult.computed_at >= start_dt,
                    MatchResult.computed_at < end_dt,
                )
            )
        ).all()

        threshold = await self._threshold(program_id)
        out: list[FairnessSignal] = []
        for attr in PROTECTED_ATTRIBUTES:
            sig = self._compute_attr(program_id, attr, week_start, rows, threshold)
            if sig is not None:
                await self._upsert(sig)
                out.append(sig)
        return out

    def _compute_attr(self, program_id, attr, week_start, rows, threshold) -> FairnessSignal | None:
        # group -> [selected_count, total_count]
        groups: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        for fitness, gender, nationality, first_gen in rows:
            val = _attr_value(attr, gender, nationality, first_gen)
            if not val:
                continue
            groups[val][1] += 1
            if fitness is not None and float(fitness) >= RECOMMEND_BAR:
                groups[val][0] += 1

        # Keep only groups with a meaningful sample.
        rates = {g: sel / tot for g, (sel, tot) in groups.items() if tot >= MIN_GROUP_SIZE}
        if len(rates) < 2:
            return None  # need at least two comparable groups

        ref_group = max(rates, key=rates.get)  # highest selection rate = reference
        dis_group = min(rates, key=rates.get)
        ref_rate = rates[ref_group]
        dis_rate = rates[dis_group]
        ratio = (dis_rate / ref_rate) if ref_rate > 0 else 1.0
        delta = max(0.0, 1.0 - ratio)
        sample = sum(tot for _, (_, tot) in groups.items())

        return FairnessSignal(
            program_id=program_id,
            protected_attribute=attr,
            week_start=week_start,
            reference_group=str(ref_group)[:120],
            disadvantaged_group=str(dis_group)[:120],
            reference_rate=round(ref_rate, 4),
            disadvantaged_rate=round(dis_rate, 4),
            disparate_impact_ratio=round(ratio, 4),
            disparate_impact_delta=round(delta, 4),
            sample_size=sample,
            breached=delta > threshold,
        )

    async def _upsert(self, sig: FairnessSignal) -> None:
        existing = await self.db.scalar(
            select(FairnessSignal).where(
                FairnessSignal.program_id == sig.program_id,
                FairnessSignal.protected_attribute == sig.protected_attribute,
                FairnessSignal.week_start == sig.week_start,
            )
        )
        if existing is None:
            self.db.add(sig)
        else:
            existing.reference_group = sig.reference_group
            existing.disadvantaged_group = sig.disadvantaged_group
            existing.reference_rate = sig.reference_rate
            existing.disadvantaged_rate = sig.disadvantaged_rate
            existing.disparate_impact_ratio = sig.disparate_impact_ratio
            existing.disparate_impact_delta = sig.disparate_impact_delta
            existing.sample_size = sig.sample_size
            existing.breached = sig.breached
        await self.db.flush()

    async def evaluate_auto_halt(self, program_id: UUID) -> bool:
        """Halt matching if any protected attribute breached for the last
        CONSECUTIVE_WEEKS_TO_HALT consecutive weeks. Returns the new halt state."""
        signals = (
            (
                await self.db.execute(
                    select(FairnessSignal)
                    .where(FairnessSignal.program_id == program_id)
                    .order_by(FairnessSignal.week_start.desc())
                )
            )
            .scalars()
            .all()
        )
        # Per attribute, look at the most recent weeks in order.
        by_attr: dict[str, list[FairnessSignal]] = defaultdict(list)
        for s in signals:
            by_attr[s.protected_attribute].append(s)

        should_halt = False
        for attr_signals in by_attr.values():
            recent = attr_signals[:CONSECUTIVE_WEEKS_TO_HALT]
            if len(recent) >= CONSECUTIVE_WEEKS_TO_HALT and all(s.breached for s in recent):
                should_halt = True
                break

        if should_halt:
            program = await self.db.get(Program, program_id)
            if program is not None and not program.matching_halted:
                program.matching_halted = True
                await self.db.flush()
                logger.warning(
                    "fairness auto-halt: program=%s matching halted after %d "
                    "consecutive breached weeks",
                    program_id,
                    CONSECUTIVE_WEEKS_TO_HALT,
                )
        return should_halt

    async def override_halt(self, program_id: UUID) -> Program | None:
        """Clear a fairness halt (admin override). Caller audit-logs the action."""
        program = await self.db.get(Program, program_id)
        if program is None:
            return None
        program.matching_halted = False
        await self.db.flush()
        return program

    async def list_signals(self, program_id: UUID, *, weeks: int = 8) -> list[FairnessSignal]:
        return list(
            (
                await self.db.execute(
                    select(FairnessSignal)
                    .where(FairnessSignal.program_id == program_id)
                    .order_by(FairnessSignal.week_start.desc())
                    .limit(weeks * len(PROTECTED_ATTRIBUTES))
                )
            )
            .scalars()
            .all()
        )

    async def _threshold(self, program_id: UUID) -> float:
        program = await self.db.get(Program, program_id)
        if program is not None and program.fairness_threshold_override is not None:
            return float(program.fairness_threshold_override)
        return DEFAULT_DISPARATE_IMPACT_THRESHOLD
