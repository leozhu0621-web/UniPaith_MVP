"""TDD: weight_research + weight_campus_life scored preference weights.

Covers:
(a) CATALOG includes both new weights with type=weight, ask_kind=scale.
(b) CatalogService maps them to "What matters most" section.
(c) EnrichmentService.set_value scales 0-5 → 0-10 and stores on StudentPreference.
(d) Matcher decision: stored-only (no program-side feature to weight against);
    weights_from_preferences ignores them — existing composition weights unchanged.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from tests._uni_helpers import ensure_profile
from unipaith.models.student import StudentPreference
from unipaith.services.catalog_service import _SECTION_BY_KEY, CatalogService
from unipaith.services.enrichment_planner import CATALOG
from unipaith.services.intake.intake_engine_service import IntakeEngineService
from unipaith.services.match_banding import weights_from_preferences

BASE = "/api/v1/students/me/enrichment"


# ── (a) CATALOG content ──────────────────────────────────────────────────────


def test_weight_research_in_catalog():
    by_key = {f["key"]: f for f in CATALOG}
    assert "weight_research" in by_key, "weight_research missing from CATALOG"
    entry = by_key["weight_research"]
    assert entry["type"] == "weight"
    assert entry["ask_kind"] == "scale"
    assert "options" not in entry or entry.get("options") is None


def test_weight_campus_life_in_catalog():
    by_key = {f["key"]: f for f in CATALOG}
    assert "weight_campus_life" in by_key, "weight_campus_life missing from CATALOG"
    entry = by_key["weight_campus_life"]
    assert entry["type"] == "weight"
    assert entry["ask_kind"] == "scale"
    assert "options" not in entry or entry.get("options") is None


# ── (b) Section mapping ───────────────────────────────────────────────────────


def test_section_by_key_maps_weight_research():
    assert _SECTION_BY_KEY.get("weight_research") == "What matters most"


def test_section_by_key_maps_weight_campus_life():
    assert _SECTION_BY_KEY.get("weight_campus_life") == "What matters most"


@pytest.mark.asyncio
async def test_catalog_service_seeds_new_weights(db_session):
    """After seeding, both new weight keys appear in the loaded catalog."""
    svc = CatalogService(db_session)
    await svc.ensure_seeded()
    loaded = await svc.load()
    by_key = {e["key"]: e for e in loaded}
    for key in ("weight_research", "weight_campus_life"):
        assert key in by_key, f"{key} missing from seeded catalog"
        assert by_key[key]["type"] == "weight"
        assert by_key[key]["ask_kind"] == "scale"


# ── (c) EnrichmentService write path ─────────────────────────────────────────


async def _preference(db, user):
    pid = await IntakeEngineService(db).profile_id_for_user(user.id)
    db.expire_all()
    return (
        await db.execute(select(StudentPreference).where(StudentPreference.student_id == pid))
    ).scalar_one_or_none()


@pytest.mark.asyncio
async def test_weight_research_scales_to_preference(student_client, db_session, mock_student_user):
    """weight_research=4 (0-5) must project as 8 (0-10) onto StudentPreference."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/weight_research/value", json={"value": 4})
    assert r.status_code == 200, r.text
    pref = await _preference(db_session, mock_student_user)
    assert pref is not None
    assert pref.weight_research == 8, (
        f"weight_research 4 (0-5) must project as 8 (0-10), got {pref.weight_research}"
    )


@pytest.mark.asyncio
async def test_weight_campus_life_scales_to_preference(
    student_client, db_session, mock_student_user
):
    """weight_campus_life=3 (0-5) must project as 6 (0-10) onto StudentPreference."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/weight_campus_life/value", json={"value": 3})
    assert r.status_code == 200, r.text
    pref = await _preference(db_session, mock_student_user)
    assert pref is not None
    assert pref.weight_campus_life == 6, (
        f"weight_campus_life 3 (0-5) must project as 6 (0-10), got {pref.weight_campus_life}"
    )


# ── (d) Matcher — stored-only, not wired into composition weights ─────────────
#
# weight_research and weight_campus_life are captured on StudentPreference but
# NOT fed into weights_from_preferences() because there is no corresponding
# program-side feature vector dimension to weight against (the matcher's three
# levers — cosine / soft_align / needs_match — each map to real program fields).
# Wiring them would require inventing program features, which violates the
# "no fabricated data" rule. They are available for a future per-dimension
# program signal (e.g. research_activity_score, campus_events_score) once the
# program enrichment pipeline produces those fields.


class _FakePref:
    """Minimal duck-typed preference object for testing matcher isolation."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getattr__(self, name):
        return None  # any unset weight returns None


def test_matcher_ignores_new_weights_when_only_they_are_set():
    """weights_from_preferences returns None when only the new weights are set
    (no existing weight is set), preserving DEFAULT_WEIGHTS behaviour."""
    pref = _FakePref(weight_research=8, weight_campus_life=6)
    result = weights_from_preferences(pref)
    # All 7 original weights are None → function returns None → caller uses DEFAULT_WEIGHTS
    assert result is None


def test_matcher_unchanged_when_new_weights_coexist_with_existing():
    """Adding weight_research/weight_campus_life does not change the composition
    produced by the existing 7 sliders (the new weights are not read by the function)."""
    pref_without = _FakePref(weight_cost=6, weight_outcomes=8)
    pref_with = _FakePref(
        weight_cost=6, weight_outcomes=8, weight_research=10, weight_campus_life=10
    )
    assert weights_from_preferences(pref_without) == weights_from_preferences(pref_with), (
        "weight_research and weight_campus_life must not alter the matcher composition"
    )
