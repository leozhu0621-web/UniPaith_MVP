"""Tests for saved lists (save/unsave/list programs)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User


async def _seed_student_and_program(db: AsyncSession, student_user: User, institution_user: User):
    """Create a student profile, institution, and published program."""
    db.add(student_user)
    db.add(institution_user)

    profile = StudentProfile(user_id=student_user.id, first_name="Test", last_name="Student")
    db.add(profile)

    institution = Institution(
        admin_user_id=institution_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(institution)
    await db.flush()

    program = Program(
        institution_id=institution.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
    )
    db.add(program)
    await db.commit()
    return profile, institution, program


@pytest.mark.asyncio
async def test_save_program(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await student_client.post(
        "/api/v1/students/me/saved",
        json={"program_id": str(program.id)},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["program_id"] == str(program.id)


@pytest.mark.asyncio
async def test_unsave_program(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    # Save first
    save_resp = await student_client.post(
        "/api/v1/students/me/saved",
        json={"program_id": str(program.id)},
    )
    assert save_resp.status_code == 201

    # Unsave
    resp = await student_client.delete(f"/api/v1/students/me/saved/{program.id}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_list_saved(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program1 = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )

    program2 = Program(
        institution_id=institution.id,
        program_name="Data Science PhD",
        degree_type="phd",
        is_published=True,
        tuition=60000,
    )
    db_session.add(program2)
    await db_session.commit()

    # Save both programs
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program1.id)})
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program2.id)})

    resp = await student_client.get("/api/v1/students/me/saved")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_save_duplicate(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    # Save once
    resp1 = await student_client.post(
        "/api/v1/students/me/saved", json={"program_id": str(program.id)}
    )
    assert resp1.status_code == 201

    # Save again — expect conflict
    resp2 = await student_client.post(
        "/api/v1/students/me/saved", json={"program_id": str(program.id)}
    )
    assert resp2.status_code == 409


# ---------------------------------------------------------------------------
# Spec 13 — curation (priority + tags), derived status, conversion, compare.
# ---------------------------------------------------------------------------


async def _seed_match(db, profile, program, *, fitness, confidence, tier=None):
    match = MatchResult(
        student_id=profile.id,
        program_id=program.id,
        fitness_score=fitness,
        confidence_score=confidence,
        match_tier=tier,
    )
    db.add(match)
    await db.commit()
    return match


def _row_for(listing, program):
    return next(r for r in listing if r["program_id"] == str(program.id))


@pytest.mark.asyncio
async def test_priority_and_tags_persist(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """G-S5 — priority + tags persist server-side (were localStorage-only)."""
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    patch = await student_client.patch(
        f"/api/v1/students/me/saved/{program.id}",
        json={
            "priority": "planning_to_apply",
            "tags": ["dream", "funded", "Dream"],  # dupes collapse (case-insensitive)
            "notes": "why I saved this",
        },
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["priority"] == "planning_to_apply"
    assert body["tags"] == ["dream", "funded"]
    assert body["notes"] == "why I saved this"

    # Fresh GET == survives a reload.
    row = _row_for((await student_client.get("/api/v1/students/me/saved")).json(), program)
    assert row["priority"] == "planning_to_apply"
    assert row["tags"] == ["dream", "funded"]
    assert row["notes"] == "why I saved this"


@pytest.mark.asyncio
async def test_patch_invalid_priority_rejected(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    resp = await student_client.patch(
        f"/api/v1/students/me/saved/{program.id}", json={"priority": "totally_invalid"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_start_application_creates_and_idempotent(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})

    first = await student_client.post(f"/api/v1/students/me/saved/{program.id}/start-application")
    assert first.status_code == 201
    fb = first.json()
    assert fb["created"] is True
    assert fb["status"] == "application_started"
    app_id = fb["app_id"]

    # Double-click never 409s — the existing application is reused.
    second = await student_client.post(f"/api/v1/students/me/saved/{program.id}/start-application")
    assert second.status_code == 201
    sb = second.json()
    assert sb["created"] is False
    assert sb["app_id"] == app_id

    row = _row_for((await student_client.get("/api/v1/students/me/saved")).json(), program)
    assert row["status"] == "application_started"


@pytest.mark.asyncio
async def test_start_application_requires_saved(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    resp = await student_client.post(f"/api/v1/students/me/saved/{program.id}/start-application")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_dropped_priority_status(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    await student_client.patch(
        f"/api/v1/students/me/saved/{program.id}", json={"priority": "dropped"}
    )
    row = _row_for((await student_client.get("/api/v1/students/me/saved")).json(), program)
    assert row["priority"] == "dropped"
    assert row["status"] == "dropped"


@pytest.mark.asyncio
async def test_band_label_and_scores_from_match(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    await _seed_match(db_session, profile, program, fitness=0.92, confidence=0.80, tier=3)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    row = _row_for((await student_client.get("/api/v1/students/me/saved")).json(), program)
    assert row["band_label"] == "safer"
    assert row["fitness_score"] == pytest.approx(0.92, abs=1e-3)
    assert row["confidence_score"] == pytest.approx(0.80, abs=1e-3)


@pytest.mark.asyncio
async def test_list_includes_program_detail(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, _, program = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program.id)})
    row = _row_for((await student_client.get("/api/v1/students/me/saved")).json(), program)
    assert row["program_name"] == "CS Masters"
    assert row["institution_name"] == "Test University"
    assert float(row["tuition"]) == 50000
    assert row["priority"] == "considering"  # default
    assert row["status"] == "considering"  # no application yet
    assert row["program"]["program_name"] == "CS Masters"


@pytest.mark.asyncio
async def test_compare_dual_scores(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, institution, program1 = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    program2 = Program(
        institution_id=institution.id,
        program_name="Data Science PhD",
        degree_type="phd",
        is_published=True,
        tuition=60000,
    )
    db_session.add(program2)
    await db_session.commit()
    await _seed_match(db_session, profile, program1, fitness=0.90, confidence=0.70, tier=3)
    await _seed_match(db_session, profile, program2, fitness=0.50, confidence=0.60, tier=1)
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program1.id)})
    await student_client.post("/api/v1/students/me/saved", json={"program_id": str(program2.id)})

    resp = await student_client.post(
        "/api/v1/students/me/saved/compare",
        json={"program_ids": [str(program1.id), str(program2.id)]},
    )
    assert resp.status_code == 200
    progs = resp.json()["programs"]
    assert len(progs) == 2
    assert progs[0]["id"] == str(program1.id)  # request order preserved
    for p in progs:
        assert "fitness_score" in p
        assert "confidence_score" in p
        assert "band_label" in p
    assert progs[0]["band_label"] == "safer"
    assert progs[1]["band_label"] == "reach"


@pytest.mark.asyncio
async def test_compare_rejects_more_than_four(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, institution, program1 = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    ids = [str(program1.id)]
    for i in range(4):
        p = Program(
            institution_id=institution.id,
            program_name=f"Program {i}",
            degree_type="masters",
            is_published=True,
            tuition=1000,
        )
        db_session.add(p)
        await db_session.flush()
        ids.append(str(p.id))
    await db_session.commit()
    # 5 ids exceeds the Spec 13 §5 cap of 4.
    resp = await student_client.post("/api/v1/students/me/saved/compare", json={"program_ids": ids})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_compare_programs_returns_spec10_dimensions(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 10 §8 — compare returns the fields backing the five dimensions."""
    _, institution, program1 = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    program2 = Program(
        institution_id=institution.id,
        program_name="Data Science PhD",
        degree_type="phd",
        is_published=True,
        tuition=60000,
        campus_setting="urban",
        delivery_format="on_campus",
        acceptance_rate=0.2,
        outcomes_data={"median_salary": 88000, "employment_rate": 0.9, "payback_months": 20},
    )
    db_session.add(program2)
    await db_session.commit()

    resp = await student_client.post(
        "/api/v1/students/me/saved/compare",
        json={"program_ids": [str(program1.id), str(program2.id)]},
    )
    assert resp.status_code == 200
    progs = resp.json()["programs"]
    assert len(progs) == 2
    keys = set(progs[0].keys())
    for k in (
        "campus_setting",
        "median_salary",
        "employment_rate",
        "payback_months",
        "fitness_score",
        "confidence_score",
        "tuition",
        "delivery_format",
        "acceptance_rate",
    ):
        assert k in keys, f"compare row missing {k}"

    ds = next(p for p in progs if p["program_name"] == "Data Science PhD")
    assert ds["median_salary"] == 88000
    assert ds["employment_rate"] == 0.9
    assert ds["campus_setting"] == "urban"


@pytest.mark.asyncio
async def test_saved_schools_from_follows(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    """Spec 13 §3.2 — the Schools tab reads the student's followed institutions,
    enriched with location + a published-program count for the school card."""
    from unipaith.models.follow import InstitutionFollow

    profile, institution, _ = await _seed_student_and_program(
        db_session, mock_student_user, mock_institution_user
    )
    db_session.add(InstitutionFollow(student_id=profile.id, institution_id=institution.id))
    await db_session.commit()

    # The follows endpoint and the saved-institutions alias return the same card.
    for path in (
        "/api/v1/students/me/follows",
        "/api/v1/students/me/saved-institutions",
    ):
        resp = await student_client.get(path)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        school = data[0]
        assert school["institution_id"] == str(institution.id)
        assert school["name"] == "Test University"
        assert school["country"] == "United States"
        assert school["program_count"] == 1
