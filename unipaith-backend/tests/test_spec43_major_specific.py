"""Spec 43 — Major-Specific Field Catalog tests.

Covers: the 15-track catalog + major→track inference, track-signal upsert
(catalog coercion + version++ / §5 provenance), unknown-track rejection, the
flag-gated §4.18 coach overlay (tracks + summary), the back-compat
``/me/major-readiness`` shim onto the new canonical store, and pure-engine
checks. The flag-ON path is exercised explicitly (the MissingGreenlet class only
shows with the AI surface enabled).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai import major_track_coach
from unipaith.config import settings
from unipaith.models.student import AcademicRecord, StudentProfile
from unipaith.models.user import User
from unipaith.services import major_track_catalog as cat

BASE = "/api/v1/students/me/major-specific"
LEGACY = "/api/v1/students/me/major-readiness"


async def _ensure_profile(
    db: AsyncSession, user: User, *, field_of_study: str | None = None
) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.flush()
    # field_of_study (the de-facto major signal) lives on AcademicRecord.
    if field_of_study is not None:
        db.add(
            AcademicRecord(
                student_id=profile.id,
                institution_name="Test University",
                degree_type="bachelor",
                field_of_study=field_of_study,
                is_current=True,
            )
        )
    await db.commit()
    return profile


# ── Catalog + inference ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_catalog_returns_15_tracks_and_suggestions(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user, field_of_study="Computer Science")
    r = await student_client.get(f"{BASE}/catalog")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["tracks"]) == 15
    keys = {t["track_key"] for t in body["tracks"]}
    assert keys == set(cat.TRACK_KEYS)
    # Each track schema has a label + non-empty grouped fields.
    for t in body["tracks"]:
        assert t["label"]
        assert t["groups"] and all(g["fields"] for g in t["groups"])
    # Major → track inference (Spec 43 §1).
    assert "cs_data_ai" in body["suggested_tracks"]


def test_infer_tracks_pure():
    assert cat.infer_tracks_from_major("Computer Science") == ["cs_data_ai"]
    assert cat.infer_tracks_from_major("Mechanical Engineering") == ["engineering"]
    assert cat.infer_tracks_from_major("Software Engineering") == ["cs_data_ai"]
    assert cat.infer_tracks_from_major("Nursing") == ["health"]
    assert cat.infer_tracks_from_major(None) == []
    assert cat.infer_tracks_from_major("Underwater Basket Weaving") == []


# ── Track signals (write + read) ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_track_coerces_and_versions(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    r = await student_client.put(
        f"{BASE}/tracks/cs_data_ai",
        json={
            "signals": {
                "cs_fundamentals_self_rating_dsa": 5,
                "cs_fundamentals_self_rating_algorithms": 4,
                "cs_fundamentals_self_rating_os": 9,  # out of 1-5 → dropped
                "github_link": "https://github.com/me",
                "open_source_contributions": True,
                "not_a_real_field": "x",  # unknown → dropped
                "leetcode_frequency": "not_an_option",  # off-vocab enum → dropped
            }
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    sig = body["signals"]
    assert sig["cs_fundamentals_self_rating_dsa"] == 5
    assert "cs_fundamentals_self_rating_os" not in sig  # out-of-range dropped
    assert "not_a_real_field" not in sig
    assert "leetcode_frequency" not in sig
    assert sig["github_link"] == "https://github.com/me"
    assert sig["open_source_contributions"] is True
    # §5 record metadata.
    assert body["source"] == "student-typed"
    assert body["confidence"] == 95
    assert body["record_version"] == 1

    # Second save versions up.
    r2 = await student_client.put(
        f"{BASE}/tracks/cs_data_ai",
        json={"signals": {"cs_fundamentals_self_rating_dsa": 3}},
    )
    assert r2.json()["record_version"] == 2


@pytest.mark.asyncio
async def test_unknown_track_400(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    r = await student_client.put(f"{BASE}/tracks/not_a_track", json={"signals": {}})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_tracks_flag_off_no_coach(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "ai_major_specific_v2_enabled", False)
    await _ensure_profile(db_session, mock_student_user, field_of_study="Data Science")
    await student_client.put(
        f"{BASE}/tracks/cs_data_ai", json={"signals": {"cs_fundamentals_self_rating_dsa": 4}}
    )
    r = await student_client.get(f"{BASE}/tracks")
    assert r.status_code == 200
    body = r.json()
    assert body["active_tracks"] == ["cs_data_ai"]
    assert "cs_data_ai" in body["suggested_tracks"]
    assert body["tracks"][0]["coach"] is None  # overlay off


@pytest.mark.asyncio
async def test_tracks_flag_on_attaches_coach(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User, monkeypatch
):
    # TEST THE AI SURFACE FLAG-ON.
    monkeypatch.setattr(settings, "ai_major_specific_v2_enabled", True)
    await _ensure_profile(db_session, mock_student_user)
    # Strong CS signals → high readiness.
    strong = {k: 5 for k in cat.rating_field_keys("cs_data_ai")}
    strong["github_link"] = "https://github.com/me"
    await student_client.put(f"{BASE}/tracks/cs_data_ai", json={"signals": strong})
    r = await student_client.get(f"{BASE}/tracks")
    coach = r.json()["tracks"][0]["coach"]
    assert coach is not None
    assert coach["readiness_band"] == "high"
    assert coach["coding_readiness_band"] == "high"  # CS-specific alias
    assert coach["major_track_fit_score"] >= 70
    assert isinstance(coach["project_coverage_map"], dict)
    assert isinstance(coach["suggested_artifacts_to_add"], list)


@pytest.mark.asyncio
async def test_summary_flag_on(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "ai_major_specific_v2_enabled", True)
    await _ensure_profile(db_session, mock_student_user)
    await student_client.put(
        f"{BASE}/tracks/business", json={"signals": {"domain_finance": 4, "domain_strategy": 5}}
    )
    s = await student_client.get(f"{BASE}/summary")
    assert s.status_code == 200
    body = s.json()
    assert body["inference_enabled"] is True
    assert body["active_track_count"] == 1
    assert body["primary_track"] == "business"
    assert "business" in body["major_track_fit_score_per_target_track"]


@pytest.mark.asyncio
async def test_summary_empty_never_5xx(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User, monkeypatch
):
    monkeypatch.setattr(settings, "ai_major_specific_v2_enabled", True)
    await _ensure_profile(db_session, mock_student_user)
    s = await student_client.get(f"{BASE}/summary")
    assert s.status_code == 200
    assert s.json()["active_track_count"] == 0


# ── Legacy back-compat shim ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_legacy_major_readiness_shim_roundtrips(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    # Legacy upsert (6-track name) writes to the new canonical store.
    u = await student_client.put(LEGACY, json={"track": "cs", "readiness_data": {"foo": 1}})
    assert u.status_code == 200, u.text
    assert u.json()["track"] == "cs"  # remapped back on read
    assert u.json()["readiness_data"] == {"foo": 1}
    # Legacy GET returns it.
    g = await student_client.get(LEGACY)
    assert any(row["track"] == "cs" for row in g.json())
    # The new surface sees the same row under the canonical track_key.
    nt = await student_client.get(f"{BASE}/tracks")
    assert "cs_data_ai" in nt.json()["active_tracks"]


# ── Pure engine checks (no DB) ───────────────────────────────────────────────


def test_coach_track_pure_high_and_low():
    strong = {k: 5 for k in cat.rating_field_keys("cs_data_ai")}
    strong["github_link"] = "https://github.com/me"
    strong["portfolio_link"] = "https://demo.example.com"
    strong["research_output_link"] = "https://doi.org/x"
    hi = major_track_coach.coach_track("cs_data_ai", strong)
    assert hi["readiness_band"] == "high"
    assert hi["major_track_fit_score"] >= 80
    assert hi["skill_gap_severity"] == "none"
    assert hi["track_recommendation"] is not None

    lo = major_track_coach.coach_track("cs_data_ai", {})
    assert lo["readiness_band"] == "low"
    assert lo["major_track_fit_score"] == 0
    # Empty profile → artifact suggestions surface the missing evidence.
    assert lo["suggested_artifacts_to_add"]


def test_coach_summary_pure_picks_primary():
    out = major_track_coach.coach_summary(
        [
            {"track_key": "cs_data_ai", "signals": {"cs_fundamentals_self_rating_dsa": 5}},
            {"track_key": "business", "signals": {}},
        ]
    )
    assert out["primary_track"] == "cs_data_ai"
    assert set(out["major_track_fit_score_per_target_track"]) == {"cs_data_ai", "business"}
