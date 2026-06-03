"""Spec 70 §1-§2 — financial fit: EFC, net-price, Scholarship-Finder."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.reference import Scholarship
from unipaith.services.financial_fit import (
    FinancialFitService,
    estimate_efc,
    estimate_net_price,
    match_scholarships,
    scholarship_eligibility,
)


def test_estimate_efc_monotonic_and_guarded():
    low, high = estimate_efc(40000), estimate_efc(120000)
    assert low is not None and high is not None and high > low
    assert estimate_efc(None) is None
    assert estimate_efc(-5) is None
    # Bigger family / more siblings in college → lower EFC.
    assert estimate_efc(120000, family_size=6) < estimate_efc(120000, family_size=2)
    assert estimate_efc(120000, num_in_college=2) < estimate_efc(120000, num_in_college=1)


def test_estimate_net_price():
    np = estimate_net_price(60000, efc=15000, gift_aid=20000)
    assert np["net_price"] == 40000  # 60000 − 20000 gift
    assert np["unmet_need"] == 25000  # 60000 − 15000 efc − 20000 gift
    assert "Estimate only" in np["disclaimer"]
    assert estimate_net_price(30000, gift_aid=50000)["net_price"] == 0  # floored


def test_scholarship_eligibility_rules():
    ctx = {
        "gpa": 3.6,
        "income_usd": 45000,
        "cip_family": "11",
        "degree_level": "masters",
        "country": "United States",
    }
    ok, reasons = scholarship_eligibility(
        {"min_gpa": 3.5, "max_income_usd": 60000, "fields_cip": ["11", "14"]}, ctx
    )
    assert ok and any("GPA" in r for r in reasons)
    assert not scholarship_eligibility({"min_gpa": 3.8}, ctx)[0]  # GPA too low
    assert not scholarship_eligibility({"max_income_usd": 30000}, ctx)[0]  # income too high
    assert not scholarship_eligibility({"fields_cip": ["52"]}, ctx)[0]  # wrong field
    # An UNKNOWN student field is not a failure (thin profile still surfaces awards).
    assert scholarship_eligibility({"min_test": 320}, {"gpa": 3.6})[0]
    # first-gen requirement.
    assert not scholarship_eligibility({"first_gen_required": True}, ctx)[0]
    assert scholarship_eligibility({"first_gen_required": True}, {**ctx, "first_gen": True})[0]


def test_match_scholarships_ranks_by_award():
    ctx = {"gpa": 3.7, "cip_family": "11"}
    schs = [
        {
            "id": "a",
            "name": "Small",
            "amount_min": 1000,
            "amount_max": 2000,
            "eligibility": {"min_gpa": 3.0},
        },
        {
            "id": "b",
            "name": "Big",
            "amount_min": 10000,
            "amount_max": 20000,
            "eligibility": {"fields_cip": ["11"]},
        },
        {
            "id": "c",
            "name": "Locked",
            "amount_min": 50000,
            "amount_max": 50000,
            "eligibility": {"min_gpa": 4.0},
        },
    ]
    matches = match_scholarships(ctx, schs)
    assert [m.name for m in matches] == ["Big", "Small"]  # 'Locked' excluded; larger award first


@pytest.mark.asyncio
async def test_find_scholarships_service(db_session: AsyncSession):
    db_session.add(
        Scholarship(
            name="STEM Merit",
            slug="stem-merit",
            scholarship_type="merit",
            amount_min=5000,
            amount_max=10000,
            eligibility={"fields_cip": ["11"], "min_gpa": 3.5},
            status="live",
        )
    )
    db_session.add(
        Scholarship(
            name="Need Grant",
            slug="need-grant",
            scholarship_type="need",
            amount_min=8000,
            amount_max=8000,
            eligibility={"max_income_usd": 40000},
            status="live",
        )
    )
    await db_session.flush()
    svc = FinancialFitService(db_session)
    matches = await svc.find_scholarships({"gpa": 3.8, "cip_family": "11", "income_usd": 30000})
    assert {m.name for m in matches} == {"STEM Merit", "Need Grant"}
    # High-income, non-CS student matches neither.
    assert await svc.find_scholarships({"gpa": 3.8, "cip_family": "52", "income_usd": 200000}) == []
