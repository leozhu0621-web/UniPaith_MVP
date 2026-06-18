"""Phase A — Match dual-score tests.

Covers:
- New columns persist correctly
- Response schema serializes both new + legacy fields
- Backfill SQL produces fitness_score = match_score, confidence = 0.5
- /explain endpoint returns and caches a deterministic rationale
- CHECK constraints reject out-of-range scores at the DB level
- strategy_version_id FK SET NULL on cascade
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.strategy import StudentStrategy
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

MATCHES = "/api/v1/students/me/matches"


async def _ensure_profile(db: AsyncSession, user: User) -> StudentProfile:
    profile = StudentProfile(user_id=user.id)
    db.add(user)
    db.add(profile)
    await db.commit()
    return profile


async def _seed_institution_and_program(db: AsyncSession) -> Program:
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
        admin_user_id=admin.id,
        name="Test University",
        type="university",
        country="US",
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="Test Program",
        degree_type="masters",
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
    fitness_breakdown: dict | None = None,
    confidence_breakdown: dict | None = None,
    strategy_version_id=None,
) -> MatchResult:
    match = MatchResult(
        student_id=student.id,
        program_id=program.id,
        fitness_score=Decimal(fitness),
        confidence_score=Decimal(confidence),
        fitness_breakdown=fitness_breakdown or {"gpa_alignment": 0.9, "interest_match": 0.8},
        confidence_breakdown=confidence_breakdown or {"reason": "profile_complete", "value": 0.7},
        strategy_version_id=strategy_version_id,
    )
    db.add(match)
    await db.commit()
    await db.refresh(match)
    return match


# ── persistence + response shape ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_match_serializes_qualitative_readouts_not_raw_scores(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """AI-Structure-3 §14 backend-only contract: the student match response carries
    the qualitative readouts (breakdown drivers, band, rationale) but NOT the raw CPEF
    numbers. The raw fitness/confidence numbers are computed on the backend (they drive
    the band) and never serialized to the student."""
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    await _seed_match(
        db_session,
        profile,
        program,
        fitness_breakdown={
            "interest_match": 0.8,  # a raw number → must be stripped
            "top_driver": "interest alignment",  # qualitative → survives
            "applied": True,  # flag → survives
        },
        confidence_breakdown={"reason": "profile_complete", "value": 0.7},
    )

    resp = await student_client.get(f"{MATCHES}/{program.id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    fb = data.get("fitness_breakdown") or {}
    cb = data.get("confidence_breakdown") or {}
    # qualitative drivers + flags survive
    assert fb.get("top_driver") == "interest alignment"
    assert fb.get("applied") is True
    assert cb.get("reason") == "profile_complete"
    assert "band_label" in data
    # the student never sees a number: raw scores absent AND breakdown numbers stripped
    assert "fitness_score" not in data and "confidence_score" not in data
    assert "interest_match" not in fb
    assert "value" not in cb


@pytest.mark.asyncio
async def test_student_match_response_contains_no_raw_score_field(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """Serialization contract (AI-Structure-3 §14 'backend-only … the student never sees
    a number'): NONE of the raw matching-number fields may appear on ANY student match
    response — neither the list nor the detail endpoint. The student gets band +
    rationale + probability bands only."""
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    # Seed a realistic CPEF breakdown carrying raw numbers at multiple depths.
    await _seed_match(
        db_session,
        profile,
        program,
        fitness_breakdown={
            "value": 0.46,
            "m": 0.46,
            "s2p_value": 0.46,
            "inner": 0.59,
            "coverage": 0.68,
            "mean_rho": 0.81,
            "alpha": 0.70,
            "signals": [{"name": "cost", "f": 0.8, "rho": 0.9, "A": 0.81}],
            "model": "cpef",
        },
        confidence_breakdown={"mean_rho": 0.81, "model": "cpef", "m": 0.46},
    )

    raw_fields = {"fitness_score", "confidence_score", "match_score", "score_breakdown"}

    def _has_number(obj) -> bool:
        if isinstance(obj, bool):
            return False
        if isinstance(obj, (int, float)):
            return True
        if isinstance(obj, dict):
            return any(_has_number(v) for v in obj.values())
        if isinstance(obj, list):
            return any(_has_number(v) for v in obj)
        return False

    detail = (await student_client.get(f"{MATCHES}/{program.id}")).json()
    assert raw_fields.isdisjoint(detail.keys()), (
        f"student detail leaked raw score fields: {raw_fields & set(detail.keys())}"
    )
    # §14: no raw number may reach the student through the breakdown channel either.
    assert not _has_number(detail.get("fitness_breakdown") or {}), (
        "raw number leaked via student fitness_breakdown"
    )
    assert not _has_number(detail.get("confidence_breakdown") or {}), (
        "raw number leaked via student confidence_breakdown"
    )

    listed = (await student_client.get(MATCHES)).json()
    for item in listed:
        assert raw_fields.isdisjoint(item.keys()), (
            f"student list leaked raw score fields: {raw_fields & set(item.keys())}"
        )
        assert not _has_number(item.get("fitness_breakdown") or {})
        assert not _has_number(item.get("confidence_breakdown") or {})


@pytest.mark.asyncio
async def test_real_cpef_breakdown_carries_no_number_to_student(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """AI-Structure-3 §14 — the strongest form of the backend-only contract.

    The sibling test above hand-seeds a breakdown that *looks like* CPEF output;
    this one runs the REAL ``mutual_match()`` (cpef) function and feeds its live
    breakdown through the student projection. That guards against drift: if
    ``cpef()`` grows a new numeric key (or renames one), a hand-seeded look-alike
    could silently miss the leak, but this test consumes whatever shape the
    matcher actually writes under ``cpef_matching_enabled=true``.

    Asserts that NONE of the raw rank-key / confidence numbers (value, m,
    s2p_value, inner, mean_rho, coverage, veto, alpha) survive into the student's
    ``fitness_breakdown`` / ``confidence_breakdown`` — neither as a scalar (so
    ``RationalePopover.BreakdownBlock`` renders no numeric chip) nor as a residual
    key — while the qualitative shell (model tag + per-signal driver names) does
    survive so the popover still has something to show.
    """
    from unipaith.api.students import _redact_match_for_student
    from unipaith.services.matching import ProgramFeatures, StudentFeatures, mutual_match

    student_features = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_must": ["USA"],
            "budget_max_usd_per_year": 35000,
            "interest_themes": ["data_science"],
            "gpa": 3.0,
            "field_of_study": "data_science",
        },
        profile_completeness=0.8,
    )
    program_features = ProgramFeatures(
        program_id="good",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "tuition_usd_per_year": 30000,
            "interest_themes": ["data_science"],
            # Program preferences so the nested p2s sub-dict also carries numbers,
            # exercising _strip_numbers at depth.
            "pref_min_gpa": 3.0,
            "pref_fields": ["data_science"],
            "pref_levels": ["bachelors"],
        },
    )
    m, fitness_bd = mutual_match(student_features, program_features)
    # Mirror services.matching._score_cpef's confidence breakdown shape exactly.
    confidence_bd = {"mean_rho": fitness_bd["mean_rho"], "model": "cpef", "m": fitness_bd["m"]}

    # Sanity — the RAW breakdown DOES carry the rank-key numbers, so the redaction
    # below is actually doing work (the test can't pass vacuously).
    assert isinstance(fitness_bd["value"], (int, float))
    assert isinstance(fitness_bd["m"], (int, float))
    for k in ("s2p_value", "inner", "mean_rho", "coverage", "veto", "alpha"):
        assert k in fitness_bd, f"expected real cpef breakdown to carry '{k}'"
    assert fitness_bd["signals"], "expected real cpef breakdown to carry signal drivers"

    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    match = await _seed_match(
        db_session,
        profile,
        program,
        fitness=str(round(float(m), 4)),
        confidence=str(round(float(fitness_bd["mean_rho"]), 4)),
        fitness_breakdown=fitness_bd,
        confidence_breakdown=confidence_bd,
    )

    raw_numeric_keys = {"value", "m", "s2p_value", "inner", "mean_rho", "coverage", "veto", "alpha"}

    def _has_number(obj) -> bool:
        if isinstance(obj, bool):
            return False
        if isinstance(obj, (int, float)):
            return True
        if isinstance(obj, dict):
            return any(_has_number(v) for v in obj.values())
        if isinstance(obj, list):
            return any(_has_number(v) for v in obj)
        return False

    def _all_keys(obj) -> set[str]:
        keys: set[str] = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.add(str(k))
                keys |= _all_keys(v)
        elif isinstance(obj, list):
            for v in obj:
                keys |= _all_keys(v)
        return keys

    # 1) The exact function the API serializes through:
    #    StudentMatchResponse.model_validate(match) + the §5.5/§14 redaction.
    proj = _redact_match_for_student(match)
    fb = proj.fitness_breakdown or {}
    cb = proj.confidence_breakdown or {}
    assert not _has_number(fb), f"raw number leaked via student fitness_breakdown: {fb}"
    assert not _has_number(cb), f"raw number leaked via student confidence_breakdown: {cb}"
    leaked = (_all_keys(fb) | _all_keys(cb)) & raw_numeric_keys
    assert not leaked, f"raw rank-key/confidence numbers survived projection: {leaked}"
    # The qualitative shell survives so the popover still renders the drivers.
    assert fb.get("model") == "cpef"
    driver_names = [s.get("key") for s in (fb.get("signals") or []) if isinstance(s, dict)]
    assert driver_names and all(isinstance(k, str) for k in driver_names), (
        "qualitative per-signal driver names should survive the projection"
    )

    # 2) End-to-end through the live student endpoint (full serialization path).
    detail = (await student_client.get(f"{MATCHES}/{program.id}")).json()
    assert raw_fields_disjoint(detail)
    assert not _has_number(detail.get("fitness_breakdown") or {})
    assert not _has_number(detail.get("confidence_breakdown") or {})
    leaked_e2e = (
        _all_keys(detail.get("fitness_breakdown") or {})
        | _all_keys(detail.get("confidence_breakdown") or {})
    ) & raw_numeric_keys
    assert not leaked_e2e, f"raw numbers survived to the endpoint response: {leaked_e2e}"


def raw_fields_disjoint(payload: dict) -> bool:
    """No raw matching-number field on a student payload (AI-Structure-3 §14)."""
    return {"fitness_score", "confidence_score", "match_score", "score_breakdown"}.isdisjoint(
        payload.keys()
    )


@pytest.mark.asyncio
async def test_explain_popover_breakdown_carries_no_rank_key_number(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    """AI-Structure-3 §14 on the channel the popover ACTUALLY renders.

    RationalePopover prefers the /explain response's breakdowns over the match-list
    props, so the contract has to hold on POST /me/matches/{id}/explain too — not
    just on GET /me/matches/{id}. Seed a REAL ``mutual_match()`` (cpef) breakdown,
    hit /explain, and assert no raw rank-key scalar (value/m/inner/mean_rho/…)
    survives and the popover would render no numeric chip from it.
    """
    from unipaith.ai.rationale_redaction import RAW_SCORE_KEYS
    from unipaith.services.matching import ProgramFeatures, StudentFeatures, mutual_match

    student_features = StudentFeatures(
        sparse={
            "education_level": "bachelors",
            "geo_must": ["USA"],
            "budget_max_usd_per_year": 35000,
            "interest_themes": ["data_science"],
            "gpa": 3.0,
            "field_of_study": "data_science",
        },
        profile_completeness=0.8,
    )
    program_features = ProgramFeatures(
        program_id="good",
        sparse={
            "target_education_level": "masters",
            "locations": ["USA"],
            "tuition_usd_per_year": 30000,
            "interest_themes": ["data_science"],
        },
    )
    m, fitness_bd = mutual_match(student_features, program_features)
    confidence_bd = {"mean_rho": fitness_bd["mean_rho"], "model": "cpef", "m": fitness_bd["m"]}

    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    await _seed_match(
        db_session,
        profile,
        program,
        fitness=str(round(float(m), 4)),
        confidence=str(round(float(fitness_bd["mean_rho"]), 4)),
        fitness_breakdown=fitness_bd,
        confidence_breakdown=confidence_bd,
    )

    def _all_keys(obj) -> set[str]:
        keys: set[str] = set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                keys.add(str(k))
                keys |= _all_keys(v)
        elif isinstance(obj, list):
            for v in obj:
                keys |= _all_keys(v)
        return keys

    def _renders_numeric_chip(bd: dict) -> bool:
        # Mirrors RationalePopover.formatBreakdownValue — only top-level scalars
        # render; a number renders as a numeric chip (bool renders as yes/no).
        return any(
            isinstance(v, (int, float)) and not isinstance(v, bool) for v in (bd or {}).values()
        )

    resp = await student_client.post(f"{MATCHES}/{program.id}/explain")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    fb = data.get("fitness_breakdown") or {}
    cb = data.get("confidence_breakdown") or {}
    leaked = (_all_keys(fb) | _all_keys(cb)) & RAW_SCORE_KEYS
    assert not leaked, f"/explain leaked raw rank-key scalars to the student: {leaked}"
    assert not _renders_numeric_chip(fb), f"popover would render a numeric fitness chip: {fb}"
    assert not _renders_numeric_chip(cb), f"popover would render a numeric confidence chip: {cb}"
    # The qualitative shell still reaches the popover so it has drivers to show.
    assert fb.get("model") == "cpef"


# ── CHECK constraints ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fitness_score_above_one_rejected(db_session: AsyncSession, mock_student_user: User):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    bad = MatchResult(
        student_id=profile.id,
        program_id=program.id,
        fitness_score=Decimal("1.5"),
        confidence_score=Decimal("0.5"),
    )
    db_session.add(bad)
    with pytest.raises(IntegrityError):
        await db_session.commit()


@pytest.mark.asyncio
async def test_confidence_score_below_zero_rejected(
    db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    bad = MatchResult(
        student_id=profile.id,
        program_id=program.id,
        fitness_score=Decimal("0.5"),
        confidence_score=Decimal("-0.1"),
    )
    db_session.add(bad)
    with pytest.raises(IntegrityError):
        await db_session.commit()


# ── /explain endpoint ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_explain_returns_stub_rationale(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    await _seed_match(db_session, profile, program)

    resp = await student_client.post(f"{MATCHES}/{program.id}/explain")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["program_id"] == str(program.id)
    assert data["is_stub"] is True
    assert "Fitness 0.85" in data["rationale_text"]
    assert "Confidence 0.70" in data["rationale_text"]
    # The driver names from fitness_breakdown should appear.
    assert "gpa_alignment" in data["rationale_text"]


@pytest.mark.asyncio
async def test_explain_caches_rationale_on_match_row(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    await _seed_match(db_session, profile, program)

    await student_client.post(f"{MATCHES}/{program.id}/explain")

    # GET /matches/{program_id} should now return the cached rationale.
    detail = (await student_client.get(f"{MATCHES}/{program.id}")).json()
    assert detail["rationale_text"] is not None
    assert detail["rationale_generated_at"] is not None


@pytest.mark.asyncio
async def test_explain_404_when_no_match(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _ensure_profile(db_session, mock_student_user)
    bogus = "00000000-0000-0000-0000-000000000000"
    resp = await student_client.post(f"{MATCHES}/{bogus}/explain")
    assert resp.status_code == 404


# ── strategy_version_id ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_strategy_fk_set_null_on_strategy_delete(
    db_session: AsyncSession, mock_student_user: User
):
    """Deleting a strategy must NOT delete downstream match rows; FK is
    SET NULL so matches survive but lose the strategy attribution."""
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    strategy = StudentStrategy(
        student_id=profile.id,
        version=1,
        status="active",
        career_target="x",
    )
    db_session.add(strategy)
    await db_session.commit()
    await db_session.refresh(strategy)

    match = await _seed_match(db_session, profile, program, strategy_version_id=strategy.id)
    assert match.strategy_version_id == strategy.id

    await db_session.delete(strategy)
    await db_session.commit()
    await db_session.refresh(match)
    assert match.strategy_version_id is None


# ── backfill SQL (simulated) ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_backfill_logic_simulation(db_session: AsyncSession, mock_student_user: User):
    """Tests run against a fresh schema (Base.metadata.create_all), so we
    can't replay the alembic backfill literally. Instead, we simulate a
    legacy row by writing new-column nulls equivalent and asserting our
    backfill SQL matches the documented rule when applied directly."""
    profile = await _ensure_profile(db_session, mock_student_user)
    program = await _seed_institution_and_program(db_session)
    # Insert a row populated with legacy fields only (new fields default-nulled
    # via raw SQL — bypasses the model's NOT NULL since this is what the
    # alembic migration is also doing during the backfill window).
    legacy_id = uuid4()
    await db_session.execute(
        text(
            """
            INSERT INTO match_results
              (id, student_id, program_id, match_score, score_breakdown,
               fitness_score, confidence_score, fitness_breakdown,
               confidence_breakdown, is_stale)
            VALUES
              (:id, :sid, :pid, 0.6, '{"gpa": 0.7}'::jsonb,
               0, 0, NULL, NULL, false)
            """
        ),
        {"id": legacy_id, "sid": profile.id, "pid": program.id},
    )
    await db_session.commit()

    # Apply the documented backfill rule.
    await db_session.execute(
        text(
            """
            UPDATE match_results
            SET fitness_score = COALESCE(match_score, 0),
                confidence_score = 0.5,
                fitness_breakdown = COALESCE(score_breakdown, '{}'::jsonb),
                confidence_breakdown = '{"reason": "legacy_backfill", "value": 0.5}'::jsonb
            WHERE id = :id
            """
        ),
        {"id": legacy_id},
    )
    await db_session.commit()

    row = (
        await db_session.execute(select(MatchResult).where(MatchResult.id == legacy_id))
    ).scalar_one()
    assert row.fitness_score == Decimal("0.6000")
    assert row.confidence_score == Decimal("0.5000")
    assert row.fitness_breakdown == {"gpa": 0.7}
    assert row.confidence_breakdown["reason"] == "legacy_backfill"
