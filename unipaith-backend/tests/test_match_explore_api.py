"""Spec 09 — Match surface API integration tests.

Covers the enrichment added for the Match (explore) surface:
- GET /me/matches and /me/matches/{id} carry band_label + probability_bands
  + program display fields.
- GET /me/matches/{id}/probability honesty paths (present / no_history / not_ready).
- POST /me/matches/refresh recomputes the catalog applying priority weights (§5.2).
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.ai_artifacts import StudentFeatureVector
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentPreference, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.match_banding import weights_from_preferences

MATCHES = "/api/v1/students/me/matches"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


async def _seed_program(
    db: AsyncSession, *, acceptance_rate: str | None = "0.15", published: bool = True
) -> Program:
    admin = User(
        id=uuid4(),
        email=f"inst-admin-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(
        admin_user_id=admin.id, name="Test University", type="university", country="US"
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="Test Program",
        degree_type="masters",
        acceptance_rate=Decimal(acceptance_rate) if acceptance_rate is not None else None,
        is_published=published,
    )
    db.add(program)
    await db.commit()
    await db.refresh(program)
    return program


async def _seed_match(
    db: AsyncSession,
    student: StudentProfile,
    program: Program,
    *,
    fitness: str = "0.85",
    confidence: str = "0.7",
) -> MatchResult:
    match = MatchResult(
        student_id=student.id,
        program_id=program.id,
        fitness_score=Decimal(fitness),
        confidence_score=Decimal(confidence),
        fitness_breakdown={"cosine": 0.9, "soft_align": 0.8},
        confidence_breakdown={"reason": "profile_complete", "value": 0.7},
    )
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


# ── enriched list + detail ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_matches_carry_band_and_probability(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_program(db_session, acceptance_rate="0.15")
    await _seed_match(db_session, profile, program)

    resp = await student_client.get(MATCHES)
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    # Program display fields are joined in (cards render from this alone).
    assert item["program_name"] == "Test Program"
    assert item["institution_id"] is not None
    assert item["institution_name"] == "Test University"
    assert item["acceptance_rate"] is not None
    # Spec 09 §6 — band present.
    assert item["band_label"] in {"reach", "target", "safer"}
    # Spec 09 §4A — probability bands present (history + match-ready).
    pb = item["probability_bands"]
    assert pb is not None
    assert pb["admit"]["label"] in {"likely", "target", "reach", "unlikely"}
    assert pb["admit"]["low"] < pb["admit"]["high"]


@pytest.mark.asyncio
async def test_detail_carries_band_and_probability(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_program(db_session, acceptance_rate="0.4")
    await _seed_match(db_session, profile, program)

    resp = await student_client.get(f"{MATCHES}/{program.id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["band_label"] in {"reach", "target", "safer"}
    assert data["probability_bands"] is not None
    assert data["program_name"] == "Test Program"


# ── probability endpoint honesty paths ─────────────────────────────────────


@pytest.mark.asyncio
async def test_probability_endpoint_present(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_program(db_session, acceptance_rate="0.3")
    await _seed_match(db_session, profile, program, confidence="0.7")

    resp = await student_client.get(f"{MATCHES}/{program.id}/probability")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["match_ready"] is True
    assert data["probability_bands"] is not None
    assert data["reason"] is None


@pytest.mark.asyncio
async def test_probability_null_when_no_history(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_program(db_session, acceptance_rate=None)
    await _seed_match(db_session, profile, program, confidence="0.7")

    data = (await student_client.get(f"{MATCHES}/{program.id}/probability")).json()
    assert data["probability_bands"] is None
    assert data["reason"] == "no_history"


@pytest.mark.asyncio
async def test_probability_null_when_not_match_ready(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_program(db_session, acceptance_rate="0.3")
    await _seed_match(db_session, profile, program, confidence="0.1")  # below match-ready min

    data = (await student_client.get(f"{MATCHES}/{program.id}/probability")).json()
    assert data["match_ready"] is False
    assert data["probability_bands"] is None
    assert data["reason"] == "not_match_ready"


# ── refresh applies priority weights (§5.2) ────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_applies_priority_weights(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    await _seed_program(db_session, acceptance_rate="0.3", published=True)

    # Feature vector so the matcher produces rows (Discovery completed).
    db_session.add(
        StudentFeatureVector(
            student_id=profile.id,
            profile_version=1,
            sparse_features={"feature_completeness": 0.6, "interest_themes": ["cs"]},
            applicant_summary="A CS-focused applicant.",
            embedding=None,
        )
    )
    # Cost-heavy priority preferences (§5.2 sliders).
    cost_heavy = StudentPreference(
        student_id=profile.id,
        weight_cost=10,
        weight_outcomes=0,
        weight_ranking=0,
        weight_location=10,
        weight_flexibility=10,
        weight_support=0,
    )
    db_session.add(cost_heavy)
    await db_session.commit()

    resp = await student_client.post(f"{MATCHES}/refresh")
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert len(items) >= 1
    assert items[0]["band_label"] in {"reach", "target", "safer"}

    # The persisted match must have been scored with the mapped priority weights.
    # The student/program carry no embedding here (the cold-start default), so
    # the cosine term can't fire: the *nominal* weights record the priority
    # mapping that reached the scorer, while the *effective* weights drop cosine
    # and renormalize the remainder to a true convex combination.
    expected = weights_from_preferences(cost_heavy)
    row = (
        (await db_session.execute(select(MatchResult).where(MatchResult.student_id == profile.id)))
        .scalars()
        .first()
    )
    assert row is not None
    bd = row.fitness_breakdown
    assert bd.get("nominal_weights") == expected
    assert bd.get("cosine_applied") is False
    assert "cosine" not in bd["weights"]
    assert abs(sum(bd["weights"].values()) - 1.0) < 1e-9


@pytest.mark.asyncio
async def test_refresh_empty_without_feature_vector(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    await _seed_program(db_session, published=True)
    # No feature vector → matcher returns nothing → empty list (not a 5xx).
    resp = await student_client.post(f"{MATCHES}/refresh")
    assert resp.status_code == 200
    assert resp.json() == []
