"""Spec 70 §1-§2 — financial fit: EFC + Scholarship-Finder (deterministic).

The student-facing money-fit layer the papers' Persuasion stage calls for — a
"customized aid package within their means" (`Master Paper`:86): a simplified
EFC estimate, a deterministic eligibility-rule Scholarship-Finder over the `60`
``scholarships`` catalog, and net-price-after-scholarships. Everything is
deterministic, reproducible, and framed as an **estimate — never an aid
commitment**. The admit-probability bands (`ai/probability`) and the
reverse-admissions offer engine (§3, reuses `34`) build on this.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.reference import Scholarship

ESTIMATE_DISCLAIMER = "Estimate only — not an aid offer or guarantee."


def estimate_efc(
    income_usd: float | None,
    *,
    family_size: int = 4,
    num_in_college: int = 1,
    assets_usd: float = 0,
) -> int | None:
    """Simplified, federal-methodology-INSPIRED Expected Family Contribution.

    A transparent, reproducible approximation (NOT the official FM): an income-
    protection allowance scaling with family size, a marginal assessment on the
    remainder + a light asset assessment, divided across siblings in college.
    Higher income/assets → higher EFC; bigger family / more in college → lower.
    Rounded to the nearest $100; returns None when income is unknown.
    """
    if income_usd is None or income_usd < 0:
        return None
    ipa = 10000 + 4500 * max(0, family_size - 1)
    available = max(0.0, income_usd - ipa)
    income_contribution = available * 0.22
    asset_contribution = max(0.0, assets_usd) * 0.05
    efc = (income_contribution + asset_contribution) / max(1, num_in_college)
    return int(round(efc / 100.0) * 100)


def estimate_net_price(
    cost_of_attendance: float | None, *, efc: int | None = None, gift_aid: float = 0
) -> dict:
    """Net price = cost of attendance − gift aid (grants + scholarships), floored
    at 0; unmet need = COA − EFC − gift aid. Always an estimate (§2)."""
    coa = max(0, int(cost_of_attendance or 0))
    gift = max(0, int(gift_aid or 0))
    out: dict[str, Any] = {
        "cost_of_attendance": coa,
        "gift_aid": gift,
        "net_price": max(0, coa - gift),
        "disclaimer": ESTIMATE_DISCLAIMER,
    }
    if efc is not None:
        out["estimated_efc"] = int(efc)
        out["unmet_need"] = max(0, coa - int(efc) - gift)
    return out


@dataclass
class ScholarshipMatch:
    scholarship_id: Any
    name: str
    award_estimate: int
    reasons: list[str]
    scholarship_type: str


def scholarship_eligibility(eligibility: dict | None, ctx: dict) -> tuple[bool, list[str]]:
    """Return (eligible, reasons). A failed HARD constraint eliminates; an
    *unknown* student field (not in ctx) is not a failure — a thin profile still
    surfaces broadly-eligible awards (the gap is just unverified, §2)."""
    eligibility = eligibility or {}
    reasons: list[str] = []

    # Numeric minimums the student must meet.
    for ekey, ckey, label in (("min_gpa", "gpa", "GPA"), ("min_test", "test_score", "test score")):
        need = eligibility.get(ekey)
        have = ctx.get(ckey)
        if need is not None and have is not None:
            if have < need:
                return False, [f"{label} below required {need}"]
            reasons.append(f"meets {label} ≥ {need}")

    # Income ceiling (need-based awards).
    ceiling = eligibility.get("max_income_usd")
    income = ctx.get("income_usd")
    if ceiling is not None and income is not None:
        if income > ceiling:
            return False, ["household income above the need threshold"]
        reasons.append("within the need threshold")

    # Set memberships.
    for ekey, ckey, label in (
        ("fields_cip", "cip_family", "field"),
        ("degree_levels", "degree_level", "degree level"),
        ("countries", "country", "residency"),
    ):
        allowed = eligibility.get(ekey)
        have = ctx.get(ckey)
        if allowed and have is not None:
            if have not in allowed:
                return False, [f"{label} not eligible"]
            reasons.append(f"{label} match")

    # Boolean requirements.
    if eligibility.get("first_gen_required"):
        if not ctx.get("first_gen"):
            return False, ["first-generation status required"]
        reasons.append("first-generation eligible")

    return True, reasons or ["no specific restrictions"]


def _award_estimate(sch: dict) -> int:
    lo = sch.get("amount_min") or 0
    hi = sch.get("amount_max") or lo
    return int((float(lo) + float(hi)) / 2) if (lo or hi) else 0


def match_scholarships(ctx: dict, scholarships: list[dict]) -> list[ScholarshipMatch]:
    """Rank eligible scholarships: larger award first, then more-specific match."""
    matches: list[ScholarshipMatch] = []
    for sch in scholarships:
        eligible, reasons = scholarship_eligibility(sch.get("eligibility"), ctx)
        if not eligible:
            continue
        matches.append(
            ScholarshipMatch(
                scholarship_id=sch.get("id"),
                name=sch.get("name", ""),
                award_estimate=_award_estimate(sch),
                reasons=reasons,
                scholarship_type=sch.get("scholarship_type", "external"),
            )
        )
    matches.sort(key=lambda m: (m.award_estimate, len(m.reasons)), reverse=True)
    return matches


class FinancialFitService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def find_scholarships(
        self,
        ctx: dict,
        *,
        institution_id: Any | None = None,
        limit: int = 20,
    ) -> list[ScholarshipMatch]:
        """Match the live scholarship catalog against a student context. External
        awards (no institution) always apply; institution-scoped awards apply only
        for that institution."""
        res = await self.db.execute(
            select(Scholarship).where(Scholarship.status.notin_(("superseded", "archived")))
        )
        rows = res.scalars().all()
        dicts = [
            {
                "id": s.id,
                "name": s.name,
                "scholarship_type": s.scholarship_type,
                "amount_min": float(s.amount_min) if s.amount_min is not None else None,
                "amount_max": float(s.amount_max) if s.amount_max is not None else None,
                "eligibility": s.eligibility,
                "institution_id": s.institution_id,
            }
            for s in rows
        ]
        if institution_id is not None:
            dicts = [d for d in dicts if d["institution_id"] in (None, institution_id)]
        return match_scholarships(ctx, dicts)[:limit]
