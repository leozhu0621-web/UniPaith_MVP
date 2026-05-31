"""Spec 11 §3.3a — Net Price Estimator.

Contract tests for the deterministic estimator. The pure-function tests need no
DB; one API test proves the authenticated endpoint wiring.

Honesty guardrails under test:
  * always a *range* with min <= expected <= max (never a single point),
  * never negative, never above sticker COA,
  * `available=False` (not a fabricated number) when cost data is missing,
  * the output is framed as an estimate — no aid-commitment language.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentPreference, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.net_price_service import (
    DISCLAIMER,
    compute_net_price_estimate,
)

NET_PRICE = "/api/v1/students/me/programs/{pid}/net-price"


def _basic_program(**over) -> dict:
    base = {
        "tuition": 48_000,
        "cost_data": {
            "fees": {"activity": 800, "health": 1_200},
            "estimated_living_cost": 18_000,
            "book_supplies": 1_400,
        },
        "acceptance_rate": 0.45,
        "duration_months": 24,
        "degree_type": "masters",
    }
    base.update(over)
    return base


# ── Pure-function contracts ─────────────────────────────────────────────────


def test_range_is_monotonic_non_negative_and_bounded():
    est = compute_net_price_estimate(program=_basic_program())
    assert est["available"] is True
    rng = est["net_cost_scenario_range"]
    coa = est["cost_of_attendance_annual"]
    assert rng["min"] <= rng["expected"] <= rng["max"]
    assert rng["min"] >= 0
    assert rng["max"] <= coa  # net price can never exceed sticker


def test_total_tracks_annual_times_years():
    est = compute_net_price_estimate(program=_basic_program(duration_months=24))
    years = est["years"]
    assert years == 2.0
    annual = est["net_cost_scenario_range"]["expected"]
    total = est["net_cost_scenario_range_total"]["expected"]
    # rounded to nearest $100, so allow a small tolerance
    assert abs(total - annual * years) <= 100


def test_affordable_when_budget_exceeds_net():
    base = compute_net_price_estimate(program=_basic_program())
    expected = base["net_cost_scenario_range"]["expected"]
    est = compute_net_price_estimate(
        program=_basic_program(), student_budget_annual=expected + 20_000
    )
    assert est["affordability_band"] == "affordable"
    assert est["gap"]["shortfall_annual"] == 0


def test_stretch_band_just_over_budget():
    base = compute_net_price_estimate(program=_basic_program())
    expected = base["net_cost_scenario_range"]["expected"]
    est = compute_net_price_estimate(program=_basic_program(), student_budget_annual=expected * 0.9)
    assert est["affordability_band"] == "stretch"
    assert est["gap"]["shortfall_annual"] > 0


def test_out_of_reach_band_far_over_budget():
    base = compute_net_price_estimate(program=_basic_program())
    expected = base["net_cost_scenario_range"]["expected"]
    est = compute_net_price_estimate(program=_basic_program(), student_budget_annual=expected * 0.4)
    assert est["affordability_band"] == "out_of_reach"
    assert est["gap"]["shortfall_annual"] > 0


def test_unknown_band_when_budget_missing():
    est = compute_net_price_estimate(program=_basic_program())
    assert est["affordability_band"] == "unknown"
    assert est["gap"]["band"] == "unknown"
    assert est["gap"]["shortfall_annual"] is None


def test_unavailable_when_no_cost_data():
    est = compute_net_price_estimate(
        program={"tuition": None, "cost_data": {}, "degree_type": "masters"}
    )
    assert est["available"] is False
    assert est["reason"] == "no_cost_data"
    assert est["net_cost_scenario_range"] is None
    # still carries the honest disclaimer, no fabricated numbers
    assert est["disclaimer"] == DISCLAIMER


def test_scholarship_likelihood_high_for_strong_student_at_accessible_program():
    est = compute_net_price_estimate(program=_basic_program(acceptance_rate=0.6), student_gpa=3.9)
    assert est["aid_scholarship_likelihood_band"] == "high"


def test_scholarship_likelihood_moderate_for_strong_student_at_selective_program():
    est = compute_net_price_estimate(program=_basic_program(acceptance_rate=0.08), student_gpa=3.9)
    # strong but selective, and no demonstrated need → moderate, not high
    assert est["aid_scholarship_likelihood_band"] == "moderate"


def test_funding_requirement_full_scholarship_raises_aid_likelihood():
    # A strong student at a selective program is "moderate" with no need signal…
    base = compute_net_price_estimate(program=_basic_program(acceptance_rate=0.08), student_gpa=3.9)
    assert base["aid_scholarship_likelihood_band"] == "moderate"
    # …but a stored `funding_requirement` of full_scholarship is a demonstrated-
    # need signal and bumps the band up. Regression: the stored enum
    # (full_scholarship | partial | self_funded | flexible) was never matched.
    with_need = compute_net_price_estimate(
        program=_basic_program(acceptance_rate=0.08),
        student_gpa=3.9,
        funding_requirement="full_scholarship",
    )
    assert with_need["aid_scholarship_likelihood_band"] == "high"


def test_funding_requirement_partial_is_a_need_signal():
    with_need = compute_net_price_estimate(
        program=_basic_program(acceptance_rate=0.08),
        student_gpa=3.9,
        funding_requirement="partial",
    )
    assert with_need["aid_scholarship_likelihood_band"] == "high"


def test_funding_requirement_self_funded_is_not_a_need_signal():
    base = compute_net_price_estimate(program=_basic_program(acceptance_rate=0.08), student_gpa=3.9)
    self_funded = compute_net_price_estimate(
        program=_basic_program(acceptance_rate=0.08),
        student_gpa=3.9,
        funding_requirement="self_funded",
    )
    assert (
        self_funded["aid_scholarship_likelihood_band"]
        == base["aid_scholarship_likelihood_band"]
        == "moderate"
    )


def test_high_aid_discount_never_drives_net_negative():
    # School publishes a very low average net price → large discount; combined
    # with a high-likelihood merit bump the floor must still clamp at >= 0.
    est = compute_net_price_estimate(
        program=_basic_program(acceptance_rate=0.7),
        ranking_data={"avg_net_price": 3_000, "total_cost_attendance": 70_000},
        student_gpa=4.0,
    )
    rng = est["net_cost_scenario_range"]
    assert rng["min"] >= 0
    assert rng["expected"] >= 0


def test_disclaimer_is_an_estimate_not_a_commitment():
    est = compute_net_price_estimate(program=_basic_program())
    text = est["disclaimer"].lower()
    assert "estimate" in text
    for forbidden in ("guarantee", "guaranteed", "promise", "offer of aid"):
        assert forbidden not in text


def test_net_price_by_income_data_used_when_no_avg_net_price():
    est = compute_net_price_estimate(
        program=_basic_program(
            cost_data={
                "fees": {"activity": 800},
                "estimated_living_cost": 18_000,
                "book_supplies": 1_400,
                "net_price_by_income": {
                    "0-30000": 12_000,
                    "48001-75000": 30_000,
                    "110001-plus": 55_000,
                },
            }
        )
    )
    assert est["available"] is True
    assert any("net-price-by-income" in d for d in est["drivers"])


# ── API wiring ──────────────────────────────────────────────────────────────


async def _seed_program(db: AsyncSession) -> Program:
    admin = User(
        id=uuid4(),
        email=f"inst-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name="Test U",
        type="university",
        country="US",
        ranking_data={"avg_net_price": 32_000, "total_cost_attendance": 70_000},
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="CS MS",
        degree_type="masters",
        tuition=48_000,
        duration_months=24,
        acceptance_rate=0.45,
        cost_data={
            "fees": {"activity": 800, "health": 1_200},
            "estimated_living_cost": 18_000,
            "book_supplies": 1_400,
        },
    )
    db.add(program)
    await db.flush()
    return program


@pytest.mark.asyncio
async def test_net_price_endpoint_returns_range_and_disclaimer(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = StudentProfile(user_id=mock_student_user.id)
    db_session.add(profile)
    await db_session.flush()
    db_session.add(StudentPreference(student_id=profile.id, budget_max=40_000))
    program = await _seed_program(db_session)
    await db_session.flush()

    resp = await student_client.get(NET_PRICE.format(pid=program.id))
    assert resp.status_code == 200
    body = resp.json()
    assert body["available"] is True
    rng = body["net_cost_scenario_range"]
    assert rng["min"] <= rng["expected"] <= rng["max"]
    assert body["affordability_band"] in {"affordable", "stretch", "out_of_reach"}
    assert body["aid_scholarship_likelihood_band"] in {"low", "moderate", "high"}
    assert body["disclaimer"]
    assert body["gap"]["student_annual_budget"] == 40_000


@pytest.mark.asyncio
async def test_net_price_endpoint_404_for_unknown_program(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    db_session.add(StudentProfile(user_id=mock_student_user.id))
    await db_session.flush()
    resp = await student_client.get(NET_PRICE.format(pid=uuid4()))
    assert resp.status_code == 404
