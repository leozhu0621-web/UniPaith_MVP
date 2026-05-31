"""Net Price Estimator — Spec 11 §3.3a (output schema 42 §4.12).

A personalized **net price** (not the sticker price) for *this* student at *this*
program: estimated cost of attendance minus estimated aid/scholarship, expressed
as a `{min, expected, max}` range, plus a gap analysis against the student's
stated budget.

Design constraints:
- **Deterministic / rule-based.** No LLM — the same inputs always produce the
  same estimate, so it's cheap, reproducible, and unit-testable without a DB.
- **Honesty guardrails.** Always a *range* (``min <= expected <= max``), never a
  single point, never negative, always framed as an estimate — never an aid
  commitment. When the program lacks the cost data to estimate honestly, returns
  ``available=False`` with a ``reason`` instead of fabricating a number.

The core math lives in :func:`compute_net_price_estimate`, a pure function over
plain dicts. :class:`NetPriceService` only loads the rows and delegates to it.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

DISCLAIMER = (
    "This is an estimate, not a quote or an aid offer. Your actual price depends "
    "on your FAFSA/CSS results and each school's own aid decisions."
)

# Fallbacks when a program/institution doesn't publish living + books costs.
_DEFAULT_LIVING = 15_000.0
_DEFAULT_BOOKS = 1_200.0
# Conservative aid discount used only when the school publishes no net-price data.
_DEFAULT_DISCOUNT = 0.15
# Half-width of the scenario band, as a fraction of COA (drives min/max spread).
_UNCERTAINTY = 0.12
# Net price <= budget * this => "stretch"; above => "out_of_reach".
_STRETCH_CEILING = 1.25
# Merit/need adjustments to the expected aid discount, keyed by likelihood band.
_LIKELIHOOD_DISCOUNT = {"high": 0.10, "moderate": 0.0, "low": -0.05}
# `funding_requirement` values that signal demonstrated need / aid-seeking. The
# stored enum (schema) is `full_scholarship | partial | self_funded | flexible`:
# the first two are a need signal; `self_funded` / `flexible` are not. Legacy
# free-text tokens are kept so external callers passing them still work.
_NEEDS_AID_FUNDING = frozenset(
    {
        "full_scholarship",
        "partial",
        # legacy / external tolerant tokens
        "need",
        "needs_aid",
        "need_based",
        "full_funding",
        "full",
        "required",
        "yes",
    }
)


def _num(v: Any) -> float | None:
    """Coerce Decimal/str/int to a finite float, else None."""
    try:
        if v is None:
            return None
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):  # NaN / inf
        return None
    return f


def _round100(x: float) -> float:
    """Round to the nearest $100 — net-price precision beyond that is false."""
    return float(round(x / 100.0) * 100)


def _years_for(duration_months: Any, degree_type: str | None) -> float:
    months = _num(duration_months)
    if months and months > 0:
        return round(months / 12.0, 1)
    return {"bachelors": 4.0, "masters": 2.0, "phd": 5.0, "certificate": 1.0}.get(
        (degree_type or "").lower(), 2.0
    )


def _annual_coa(program: dict, ranking: dict) -> tuple[float | None, dict]:
    """Annual cost of attendance + its components. None if tuition is unknown."""
    cd = program.get("cost_data") or {}
    if not isinstance(cd, dict):
        cd = {}
    tuition = (
        _num(program.get("tuition"))
        or _num(cd.get("tuition_annual_institution"))
        or _num(cd.get("tuition_annual"))
        or _num(ranking.get("tuition_out_of_state"))
        or _num(ranking.get("tuition_in_state"))
    )
    if tuition is None or tuition <= 0:
        return None, {}

    fees = 0.0
    fees_map = cd.get("fees")
    if isinstance(fees_map, dict):
        fees = sum((_num(v) or 0.0) for v in fees_map.values())

    living = (
        _num(cd.get("estimated_living_cost")) or _num(ranking.get("room_board")) or _DEFAULT_LIVING
    )
    books = _num(cd.get("book_supplies")) or _num(ranking.get("books_supply")) or _DEFAULT_BOOKS
    intl = _num(cd.get("international_premium")) or 0.0

    coa = tuition + fees + living + books + intl
    return coa, {
        "tuition": tuition,
        "fees": fees,
        "living": living,
        "books": books,
        "international_premium": intl,
    }


def _scholarship_likelihood(
    *,
    gpa: float | None,
    percentile: float | None,
    acceptance_rate: float | None,
    needs_aid: bool,
    budget_below_coa: bool,
) -> str:
    """low | moderate | high — merit + need signal, deliberately coarse.

    A strong student at a *less* selective program is a merit-aid magnet; the
    same student at a highly selective program is competing with equally strong
    peers, so merit aid is less certain. Demonstrated need bumps the band up.
    """
    strong = (gpa is not None and gpa >= 3.7) or (percentile is not None and percentile >= 85)
    selective = acceptance_rate is not None and acceptance_rate < 0.30

    if strong and not selective:
        band = "high"
    elif strong:
        band = "moderate"
    else:
        band = "low"

    if (needs_aid or budget_below_coa) and band != "high":
        band = {"low": "moderate", "moderate": "high"}[band]
    return band


def _expected_discount(
    program: dict, ranking: dict, coa_annual: float, likelihood: str
) -> tuple[float, str]:
    """Fraction of COA we expect aid/scholarship to cover, plus its source."""
    cd = program.get("cost_data") or {}
    if not isinstance(cd, dict):
        cd = {}

    discount: float | None = None
    source = "default"

    avg_net = _num(ranking.get("avg_net_price"))
    tca = _num(ranking.get("total_cost_attendance"))
    if avg_net is not None and tca and tca > 0:
        discount = 1.0 - (avg_net / tca)
        source = "school_avg_net_price"
    else:
        npbi = cd.get("net_price_by_income")
        if isinstance(npbi, dict) and npbi:
            vals = sorted(v for v in (_num(x) for x in npbi.values()) if v is not None)
            if vals:
                mid = vals[len(vals) // 2]
                discount = 1.0 - (mid / coa_annual)
                source = "net_price_by_income"

    if discount is None:
        discount = _DEFAULT_DISCOUNT

    discount += _LIKELIHOOD_DISCOUNT.get(likelihood, 0.0)
    discount = max(0.0, min(0.9, discount))
    return discount, source


def _build_drivers(
    *,
    coa: float,
    discount: float,
    source: str,
    likelihood: str,
    budget: float | None,
) -> list[str]:
    pct = round(discount * 100)
    drivers = [
        f"Sticker cost of attendance ≈ ${round(coa):,}/yr (tuition, fees, living, books).",
    ]
    if source == "school_avg_net_price":
        drivers.append(f"Adjusted by this school's published average aid (~{pct}% off sticker).")
    elif source == "net_price_by_income":
        drivers.append(
            f"Adjusted using the school's net-price-by-income data (~{pct}% off sticker)."
        )
    else:
        drivers.append(
            f"Aid estimated conservatively (~{pct}% off sticker) — this school "
            "hasn't published net-price data."
        )
    if likelihood == "high":
        drivers.append(
            "Scholarship/aid looks likely given your academics relative to this program."
        )
    elif likelihood == "low":
        drivers.append("Merit aid looks limited here — budget closer to the estimate.")
    if budget is not None:
        drivers.append(f"Compared against your stated budget of ${round(budget):,}/yr.")
    return drivers


def _unavailable(budget: float | None, reason: str) -> dict:
    return {
        "available": False,
        "reason": reason,
        "currency": "USD",
        "cost_of_attendance_annual": None,
        "net_cost_scenario_range": None,
        "net_cost_scenario_range_total": None,
        "years": None,
        "affordability_band": "unknown",
        "aid_scholarship_likelihood_band": "unknown",
        "gap": {
            "student_annual_budget": _round100(budget) if budget is not None else None,
            "shortfall_annual": None,
            "band": "unknown",
        },
        "drivers": [],
        "disclaimer": DISCLAIMER,
    }


def compute_net_price_estimate(
    *,
    program: dict,
    ranking_data: dict | None = None,
    student_gpa: float | None = None,
    student_percentile: float | None = None,
    student_budget_annual: float | None = None,
    funding_requirement: str | None = None,
) -> dict:
    """Pure net-price estimate. See module docstring for guarantees.

    `program` keys read: tuition, cost_data, acceptance_rate, duration_months,
    degree_type. `ranking_data` is the institution's ranking_data dict (optional).
    """
    ranking = ranking_data or {}
    budget = _num(student_budget_annual)

    coa, components = _annual_coa(program, ranking)
    if coa is None or coa <= 0:
        return _unavailable(budget, "no_cost_data")

    acceptance_rate = _num(program.get("acceptance_rate"))
    needs_aid = (funding_requirement or "").strip().lower() in _NEEDS_AID_FUNDING
    budget_below_coa = budget is not None and budget < coa

    likelihood = _scholarship_likelihood(
        gpa=student_gpa,
        percentile=student_percentile,
        acceptance_rate=acceptance_rate,
        needs_aid=needs_aid,
        budget_below_coa=budget_below_coa,
    )
    discount, source = _expected_discount(program, ranking, coa, likelihood)

    expected = coa * (1.0 - discount)
    spread = coa * _UNCERTAINTY
    lo = max(0.0, expected - spread)
    hi = min(coa, expected + spread)

    expected_r = _round100(expected)
    lo_r = min(_round100(lo), expected_r)
    hi_r = max(_round100(hi), expected_r)

    years = _years_for(program.get("duration_months"), program.get("degree_type"))

    if budget is None:
        gap_band = "unknown"
        shortfall: float | None = None
    else:
        shortfall = max(0.0, expected_r - budget)
        if expected_r <= budget:
            gap_band = "affordable"
        elif expected_r <= budget * _STRETCH_CEILING:
            gap_band = "stretch"
        else:
            gap_band = "out_of_reach"

    return {
        "available": True,
        "reason": None,
        "currency": "USD",
        "cost_of_attendance_annual": _round100(coa),
        "net_cost_scenario_range": {"min": lo_r, "expected": expected_r, "max": hi_r},
        "net_cost_scenario_range_total": {
            "min": _round100(lo_r * years),
            "expected": _round100(expected_r * years),
            "max": _round100(hi_r * years),
        },
        "years": years,
        "affordability_band": gap_band,
        "aid_scholarship_likelihood_band": likelihood,
        "gap": {
            "student_annual_budget": _round100(budget) if budget is not None else None,
            "shortfall_annual": _round100(shortfall) if shortfall is not None else None,
            "band": gap_band,
        },
        "drivers": _build_drivers(
            coa=coa, discount=discount, source=source, likelihood=likelihood, budget=budget
        ),
        "disclaimer": DISCLAIMER,
    }


class NetPriceService:
    """Loads program + institution + student signals and delegates to the pure
    estimator. Resilient: a student with no profile/budget still gets an estimate
    (just without the gap analysis)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def estimate_for_student(self, *, user_id: UUID, program_id: UUID) -> dict:
        from unipaith.core.exceptions import NotFoundException
        from unipaith.models.institution import Institution, Program
        from unipaith.models.student import (
            AcademicRecord,
            StudentPreference,
            StudentProfile,
        )

        program = await self.db.scalar(select(Program).where(Program.id == program_id))
        if program is None:
            raise NotFoundException("Program not found.")

        ranking: dict = {}
        inst = await self.db.scalar(
            select(Institution).where(Institution.id == program.institution_id)
        )
        if inst is not None and isinstance(inst.ranking_data, dict):
            ranking = inst.ranking_data

        gpa = percentile = budget = None
        funding = None
        profile = await self.db.scalar(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        if profile is not None:
            recs = (
                (
                    await self.db.execute(
                        select(AcademicRecord).where(AcademicRecord.student_id == profile.id)
                    )
                )
                .scalars()
                .all()
            )
            gpas = [_num(r.normalized_gpa) for r in recs if r.normalized_gpa is not None]
            if not any(g is not None for g in gpas):
                gpas = [
                    _num(r.gpa)
                    for r in recs
                    if r.gpa is not None and (r.gpa_scale or "4.0") in ("4.0", "4", "4.00")
                ]
            gpas = [g for g in gpas if g is not None]
            gpa = max(gpas) if gpas else None
            pcts = [_num(r.percentile_rank) for r in recs if r.percentile_rank is not None]
            pcts = [p for p in pcts if p is not None]
            percentile = max(pcts) if pcts else None

            pref = await self.db.scalar(
                select(StudentPreference).where(StudentPreference.student_id == profile.id)
            )
            if pref is not None:
                budget = _num(pref.budget_max)
                funding = pref.funding_requirement

        program_dict = {
            "tuition": program.tuition,
            "cost_data": program.cost_data,
            "acceptance_rate": program.acceptance_rate,
            "duration_months": program.duration_months,
            "degree_type": program.degree_type,
        }
        return compute_net_price_estimate(
            program=program_dict,
            ranking_data=ranking,
            student_gpa=gpa,
            student_percentile=percentile,
            student_budget_annual=budget,
            funding_requirement=funding,
        )
