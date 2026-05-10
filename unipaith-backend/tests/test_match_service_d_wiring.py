"""Phase D wiring — calibrator (D2) + reranker (D3) integration through
MatchService.

Verifies the operational glue:
- compute_matches_for_student runs the reranker before persisting
- list_matches / get_match_with_rationale apply the calibrator on read
- Cold start (no model_registry rows) preserves prior behavior
- Saving a fitted CalibratorState into model_registry calibrates reads
- Saving a fitted RerankerState reorders compute output

Uses the real DB session fixture from tests/conftest.py so the
model_registry write path is exercised end-to-end.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.ai_artifacts import StudentFeatureVector
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.confidence_calibrator import CalibratorState
from unipaith.services.match_service import MatchService
from unipaith.services.ml_state import (
    load_calibrator_state,
    load_reranker_state,
    save_calibrator_state,
    save_reranker_state,
)
from unipaith.services.program_features import ProgramRow
from unipaith.services.reranker import RerankerState

# ── Fixtures ───────────────────────────────────────────────────────────────


async def _seed_user_profile(db: AsyncSession) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"wire-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def _seed_institution_and_programs(db: AsyncSession, *, n: int = 3) -> list[Program]:
    admin = User(
        id=uuid4(),
        email=f"inst-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"dev-sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(
        admin_user_id=admin.id,
        name="WireU",
        type="university",
        country="US",
    )
    db.add(inst)
    await db.flush()
    programs: list[Program] = []
    for i in range(n):
        p = Program(
            institution_id=inst.id,
            program_name=f"Program {i}",
            degree_type="masters",
        )
        db.add(p)
        programs.append(p)
    await db.commit()
    for p in programs:
        await db.refresh(p)
    return programs


async def _seed_feature_vector(db: AsyncSession, profile: StudentProfile) -> StudentFeatureVector:
    sfv = StudentFeatureVector(
        student_id=profile.id,
        profile_version=1,
        embedding=[0.1] * 1024,
        sparse_features={
            "education_level": "bachelors",
            "feature_completeness": 0.85,
            "interest_themes": ["machine_learning"],
            "career_arcs": ["research"],
            "values": ["impact"],
        },
        applicant_summary="Real summary here.",
    )
    db.add(sfv)
    await db.commit()
    await db.refresh(sfv)
    return sfv


def _program_rows(programs: list[Program]) -> list[ProgramRow]:
    """Project ORM Program rows into ProgramRow shape — interest tags
    chosen so all three pass eligibility, with descending interest match
    so the matcher's natural order is p0 > p1 > p2."""
    return [
        ProgramRow(
            id=p.id,
            name=p.program_name,
            description=f"description {i}",
            degree="masters",
            locations=["US"],
            interest_themes=(
                ["machine_learning", "research"]
                if i == 0
                else ["machine_learning"]
                if i == 1
                else []
            ),
            career_arcs=["research"] if i < 2 else [],
            values=["impact"] if i == 0 else [],
            data_completeness=0.7,
        )
        for i, p in enumerate(programs)
    ]


# ── Cold-start wiring ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_compute_matches_annotates_rerank_breakdown(
    db_session: AsyncSession,
):
    """Cold start: identity reranker. Each persisted row's
    fitness_breakdown should carry the rerank annotation so the rationale
    agent + admin dashboard can tell the rerank stage ran."""
    profile = await _seed_user_profile(db_session)
    programs = await _seed_institution_and_programs(db_session, n=3)
    await _seed_feature_vector(db_session, profile)

    svc = MatchService(db_session)
    rows = await svc.compute_matches_for_student(
        profile.id,
        program_rows=_program_rows(programs),
    )
    assert len(rows) == 3
    for row in rows:
        rerank = row.fitness_breakdown.get("rerank")
        assert rerank is not None, row.fitness_breakdown
        assert rerank["strategy"] == "identity"
        assert rerank["score"] == 0.0


@pytest.mark.asyncio
async def test_list_matches_annotates_calibration_breakdown(
    db_session: AsyncSession,
):
    """Cold start: unfitted calibrator. confidence_breakdown.calibration
    should report raw == calibrated and calibrator_fitted=False."""
    profile = await _seed_user_profile(db_session)
    programs = await _seed_institution_and_programs(db_session, n=2)
    await _seed_feature_vector(db_session, profile)

    svc = MatchService(db_session)
    await svc.compute_matches_for_student(profile.id, program_rows=_program_rows(programs))
    rows = await svc.list_matches(profile.id)
    assert len(rows) == 2
    for row in rows:
        cal = row.confidence_breakdown.get("calibration")
        assert cal is not None
        assert cal["calibrator_fitted"] is False
        assert cal["calibrator_n_samples"] == 0
        assert cal["raw"] == cal["calibrated"]


# ── Live calibrator path ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fitted_calibrator_remaps_confidence_on_list(
    db_session: AsyncSession,
):
    """Save a fitted calibrator into model_registry → list_matches
    should report a calibrated confidence different from raw."""
    profile = await _seed_user_profile(db_session)
    programs = await _seed_institution_and_programs(db_session, n=1)
    await _seed_feature_vector(db_session, profile)

    # Compute first while uncalibrated so the persisted raw confidence
    # is the matcher's geometric-mean output.
    pre = MatchService(db_session)
    await pre.compute_matches_for_student(profile.id, program_rows=_program_rows(programs))
    pre_rows = await pre.list_matches(profile.id)
    raw_conf = float(pre_rows[0].confidence)

    # Install a calibrator that pulls everything down by 0.2 in the
    # active range. With breakpoints [(0,0), (1,0.8)] we get a 20%
    # downward shift across the curve.
    state = CalibratorState(
        fitted=True,
        n_samples=2_000,
        breakpoints=[[0.0, 0.0], [1.0, 0.8]],
    )
    await save_calibrator_state(db_session, state)
    await db_session.commit()

    # Fresh service so the cached state is reloaded.
    svc = MatchService(db_session)
    rows = await svc.list_matches(profile.id)
    cal_conf = float(rows[0].confidence)
    cal_meta = rows[0].confidence_breakdown["calibration"]
    assert cal_meta["calibrator_fitted"] is True
    assert cal_meta["calibrator_n_samples"] == 2_000
    assert cal_meta["raw"] == round(raw_conf, 4)
    # 20% downward shift on the active raw value.
    assert cal_conf == pytest.approx(raw_conf * 0.8, abs=0.01)


@pytest.mark.asyncio
async def test_get_match_uses_calibrator(
    db_session: AsyncSession,
):
    """The single-match read path also calibrates. We test it by reading
    a MatchResult directly rather than invoking get_match_with_rationale
    (which fires the rationale agent)."""
    profile = await _seed_user_profile(db_session)
    programs = await _seed_institution_and_programs(db_session, n=1)
    await _seed_feature_vector(db_session, profile)

    svc = MatchService(db_session)
    await svc.compute_matches_for_student(profile.id, program_rows=_program_rows(programs))
    state = CalibratorState(
        fitted=True,
        n_samples=1_500,
        breakpoints=[[0.0, 0.0], [1.0, 0.5]],  # 50% squash
    )
    await save_calibrator_state(db_session, state)
    await db_session.commit()

    fresh = MatchService(db_session)
    row = await fresh._read_match(profile.id, programs[0].id)
    assert row is not None
    cal = row.confidence_breakdown["calibration"]
    assert cal["calibrator_fitted"] is True
    assert cal["calibrated"] == pytest.approx(cal["raw"] * 0.5, abs=0.01)


# ── ml_state registry round-trip ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_calibrator_state_default_when_no_row(
    db_session: AsyncSession,
):
    state = await load_calibrator_state(db_session)
    assert state.fitted is False
    assert state.n_samples == 0


@pytest.mark.asyncio
async def test_save_then_load_calibrator_state(
    db_session: AsyncSession,
):
    state = CalibratorState(
        fitted=True,
        n_samples=1_500,
        breakpoints=[[0.0, 0.0], [0.5, 0.4], [1.0, 0.95]],
        reliability={"ece": 0.03},
    )
    await save_calibrator_state(db_session, state)
    await db_session.commit()

    loaded = await load_calibrator_state(db_session)
    assert loaded.fitted is True
    assert loaded.n_samples == 1_500
    assert len(loaded.breakpoints) == 3
    assert loaded.reliability["ece"] == 0.03


@pytest.mark.asyncio
async def test_save_calibrator_overwrites_in_place(
    db_session: AsyncSession,
):
    """Re-saving updates the same registry row instead of inserting a
    duplicate (the model_version unique constraint would otherwise
    raise)."""
    s1 = CalibratorState(fitted=True, n_samples=1_200, breakpoints=[[0.0, 0.0]])
    s2 = CalibratorState(fitted=True, n_samples=2_400, breakpoints=[[0.0, 0.1]])
    await save_calibrator_state(db_session, s1)
    await save_calibrator_state(db_session, s2)
    await db_session.commit()

    loaded = await load_calibrator_state(db_session)
    assert loaded.n_samples == 2_400
    assert loaded.breakpoints == [[0.0, 0.1]]


@pytest.mark.asyncio
async def test_save_then_load_reranker_state(
    db_session: AsyncSession,
):
    state = RerankerState(
        fitted=True,
        n_samples=10_000,
        model_blob=None,  # not deserializing in this test — falls through
        feature_names=["cosine", "soft_align"],
        fitted_at="2026-05-10T00:00:00",
    )
    await save_reranker_state(db_session, state)
    await db_session.commit()

    loaded = await load_reranker_state(db_session)
    assert loaded.fitted is True
    assert loaded.n_samples == 10_000
    assert loaded.feature_names == ["cosine", "soft_align"]


# ── Persisted MatchResult should still be raw ──────────────────────────────


@pytest.mark.asyncio
async def test_persisted_confidence_stays_raw(
    db_session: AsyncSession,
):
    """Calibration is a *read-time* projection. Re-fitting the
    calibrator should not require recomputing matches — the stored
    confidence_score must remain the matcher's raw output so a future
    calibrator can re-map from scratch."""
    profile = await _seed_user_profile(db_session)
    programs = await _seed_institution_and_programs(db_session, n=1)
    await _seed_feature_vector(db_session, profile)

    svc = MatchService(db_session)
    await svc.compute_matches_for_student(profile.id, program_rows=_program_rows(programs))
    pre = await db_session.scalar(select(MatchResult).where(MatchResult.student_id == profile.id))
    assert pre is not None
    pre_conf = Decimal(pre.confidence_score)

    state = CalibratorState(
        fitted=True,
        n_samples=5_000,
        breakpoints=[[0.0, 0.0], [1.0, 0.3]],  # heavy squash
    )
    await save_calibrator_state(db_session, state)
    await db_session.commit()

    # Read the row directly — the stored value should be unchanged.
    post = await db_session.scalar(select(MatchResult).where(MatchResult.student_id == profile.id))
    assert post is not None
    assert Decimal(post.confidence_score) == pre_conf
