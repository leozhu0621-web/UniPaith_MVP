"""
Tests for the AI matching pipeline.
All tests use AI_MOCK_MODE=true — no GPU or LLM required.
"""

import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

os.environ["AI_MOCK_MODE"] = "true"

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import HistoricalOutcome
from unipaith.models.engagement import StudentEngagementSignal
from unipaith.models.institution import Institution, Program, TargetSegment
from unipaith.models.matching import (
    Embedding,
    InstitutionFeature,
    MatchResult,
    PredictionLog,
    StudentFeature,
)
from unipaith.models.student import (
    AcademicRecord,
    Activity,
    OnboardingProgress,
    StudentPreference,
    StudentProfile,
    TestScore,
)
from unipaith.models.user import User, UserRole


async def _seed_student_with_profile(db: AsyncSession, user: User) -> StudentProfile:
    """Create a fully populated student profile for testing."""
    db.add(user)
    await db.flush()

    profile = StudentProfile(
        user_id=user.id,
        first_name="Maria",
        last_name="Santos",
        nationality="Brazilian",
        country_of_residence="Brazil",
        bio_text="CS student passionate about data science and NLP.",
        goals_text="Want a masters in data science at a top US program.",
    )
    db.add(profile)
    await db.flush()

    db.add(AcademicRecord(
        student_id=profile.id,
        institution_name="USP",
        degree_type="bachelors",
        field_of_study="Computer Science",
        gpa=Decimal("3.7"),
        gpa_scale="4.0",
        start_date=date(2021, 2, 1),
        end_date=date(2024, 12, 15),
        country="Brazil",
    ))
    db.add(TestScore(
        student_id=profile.id,
        test_type="GRE",
        total_score=325,
        section_scores={"verbal": 158, "quantitative": 167},
        test_date=date(2024, 6, 1),
    ))
    db.add(TestScore(
        student_id=profile.id,
        test_type="TOEFL",
        total_score=105,
        test_date=date(2024, 5, 1),
    ))
    db.add(Activity(
        student_id=profile.id,
        activity_type="research",
        title="Research Assistant",
        organization="USP AI Lab",
        description="NLP research on healthcare text mining.",
        start_date=date(2023, 1, 1),
        end_date=date(2024, 6, 1),
    ))
    db.add(Activity(
        student_id=profile.id,
        activity_type="work_experience",
        title="Data Science Intern",
        organization="Nubank",
        start_date=date(2024, 6, 1),
        end_date=date(2024, 9, 1),
    ))
    db.add(StudentPreference(
        student_id=profile.id,
        preferred_countries=["United States"],
        budget_max=60000,
        funding_requirement="partial",
        career_goals=["data scientist", "ml engineer"],
        values_priorities={"ranking": 4, "cost": 5},
    ))
    db.add(OnboardingProgress(
        student_id=profile.id,
        steps_completed=["account", "basic_profile", "academics", "test_scores", "activities", "bio", "goals", "preferences"],
        completion_percentage=100,
        last_step_at=datetime.now(timezone.utc),
    ))
    await db.flush()
    return profile


async def _seed_institution_and_programs(db: AsyncSession) -> list[Program]:
    """Create an institution with published programs."""
    admin_user = User(
        email="admin@mit-demo.edu",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin_user)
    await db.flush()

    institution = Institution(
        admin_user_id=admin_user.id,
        name="MIT",
        type="university",
        country="United States",
        region="Northeast",
        city="Cambridge",
        ranking_data={"qs": 1, "us_news": 2},
        description_text="World-renowned research university.",
    )
    db.add(institution)
    await db.flush()

    programs = []
    program_specs = [
        ("MS in Data Science", "masters", "IDSS", 58000, 12, Decimal("0.08")),
        ("PhD in Computer Science", "phd", "CSAIL", 0, 60, Decimal("0.05")),
        ("MBA", "masters", "Sloan", 82000, 24, Decimal("0.12")),
    ]
    for name, degree, dept, tuition, dur, rate in program_specs:
        p = Program(
            institution_id=institution.id,
            program_name=name,
            degree_type=degree,
            department=dept,
            tuition=tuition,
            duration_months=dur,
            acceptance_rate=rate,
            is_published=True,
            description_text=f"{name} at MIT — top program.",
            requirements={"min_gpa": 3.5, "gre_required": True, "toefl_min": 100},
            highlights=["Top ranked", "Research focused"],
            application_deadline=date(2026, 12, 15),
        )
        db.add(p)
        programs.append(p)
    await db.flush()
    return programs


# ========================================================================
# FEATURE EXTRACTION TESTS
# ========================================================================


async def test_extract_student_features_mock(db_session: AsyncSession, mock_student_user: User):
    profile = await _seed_student_with_profile(db_session, mock_student_user)

    from unipaith.ai.feature_extraction import FeatureExtractor
    extractor = FeatureExtractor(db_session)
    features = await extractor.extract_student_features(profile.id)

    assert "structured" in features
    assert "llm_extracted" in features
    assert features["version"] == "1.0"

    structured = features["structured"]
    assert structured["normalized_gpa"] is not None
    assert structured["normalized_gpa"] == pytest.approx(0.925, abs=0.01)
    assert structured["highest_degree_level"] == 3  # bachelors
    assert structured["research_count"] == 1
    assert structured["work_experience_years"] > 0
    assert structured["nationality"] == "Brazilian"
    assert structured["budget_flexibility"] == "low"  # partial funding

    llm = features["llm_extracted"]
    assert "academic_strength" in llm
    assert "key_themes" in llm


async def test_extract_program_features_mock(db_session: AsyncSession):
    programs = await _seed_institution_and_programs(db_session)

    from unipaith.ai.feature_extraction import FeatureExtractor
    extractor = FeatureExtractor(db_session)
    features = await extractor.extract_program_features(programs[0].id)

    assert features["structured"]["institution_name"] == "MIT"
    assert features["structured"]["degree_type"] == "masters"
    assert features["structured"]["tuition_annual"] == 58000
    assert features["structured"]["acceptance_rate"] == pytest.approx(0.08)


async def test_feature_upsert(db_session: AsyncSession, mock_student_user: User):
    profile = await _seed_student_with_profile(db_session, mock_student_user)

    from unipaith.ai.feature_extraction import FeatureExtractor
    extractor = FeatureExtractor(db_session)
    await extractor.extract_student_features(profile.id)
    await extractor.extract_student_features(profile.id)

    from sqlalchemy import func, select
    count = (await db_session.execute(
        select(func.count()).select_from(StudentFeature)
        .where(StudentFeature.student_id == profile.id)
    )).scalar_one()
    assert count == 1  # Upserted, not duplicated


# ========================================================================
# EMBEDDING TESTS
# ========================================================================


async def test_generate_student_embedding(db_session: AsyncSession, mock_student_user: User):
    profile = await _seed_student_with_profile(db_session, mock_student_user)

    from unipaith.ai.feature_extraction import FeatureExtractor
    await FeatureExtractor(db_session).extract_student_features(profile.id)

    from unipaith.ai.embedding_pipeline import EmbeddingPipeline
    embedding = await EmbeddingPipeline(db_session).generate_student_embedding(profile.id)

    assert len(embedding) == 768

    from sqlalchemy import select
    result = await db_session.execute(
        select(Embedding).where(
            Embedding.entity_type == "student",
            Embedding.entity_id == profile.id,
        )
    )
    stored = result.scalar_one()
    assert stored is not None


async def test_mock_embedding_deterministic():
    from unipaith.ai.embedding_client import MockEmbeddingClient
    client = MockEmbeddingClient()
    e1 = await client.embed_text("hello world")
    e2 = await client.embed_text("hello world")
    assert e1 == e2

    e3 = await client.embed_text("different text")
    assert e1 != e3


# ========================================================================
# MATCHING SERVICE TESTS
# ========================================================================


async def test_onboarding_gate_blocks_below_80(db_session: AsyncSession, mock_student_user: User):
    """Student at 50% completion should be blocked from getting matches."""
    db_session.add(mock_student_user)
    await db_session.flush()

    profile = StudentProfile(user_id=mock_student_user.id, first_name="Test")
    db_session.add(profile)
    await db_session.flush()

    db_session.add(OnboardingProgress(
        student_id=profile.id,
        steps_completed=["account", "basic_profile"],
        completion_percentage=50,
    ))
    await db_session.flush()

    from unipaith.core.exceptions import BadRequestException
    from unipaith.services.matching_service import MatchingService

    svc = MatchingService(db_session)
    with pytest.raises(BadRequestException, match="80%"):
        await svc.get_matches(profile.id)


async def test_full_match_pipeline_mock(db_session: AsyncSession, mock_student_user: User):
    """Full end-to-end matching pipeline with mock AI."""
    profile = await _seed_student_with_profile(db_session, mock_student_user)
    programs = await _seed_institution_and_programs(db_session)

    # Bootstrap program features + embeddings
    from unipaith.services.matching_service import MatchingService
    svc = MatchingService(db_session)
    bootstrap_result = await svc.bootstrap_all_programs()
    assert bootstrap_result["features_extracted"] == 3
    assert bootstrap_result["embeddings_generated"] == 3

    # Get matches
    matches = await svc.get_matches(profile.id)
    assert len(matches) > 0
    assert len(matches) <= 30

    # Verify match structure
    m = matches[0]
    assert m.match_score is not None
    assert m.match_tier in (1, 2, 3)
    assert m.score_breakdown is not None
    assert "embedding_similarity" in m.score_breakdown
    assert m.reasoning_text is not None
    assert len(m.reasoning_text) > 0
    assert m.model_version == "v1.0-mvp"
    assert m.is_stale is False


async def test_match_caching(db_session: AsyncSession, mock_student_user: User):
    """Second call should return cached results."""
    profile = await _seed_student_with_profile(db_session, mock_student_user)
    await _seed_institution_and_programs(db_session)

    from unipaith.services.matching_service import MatchingService
    svc = MatchingService(db_session)
    await svc.bootstrap_all_programs()

    matches1 = await svc.get_matches(profile.id)
    matches2 = await svc.get_matches(profile.id)

    assert len(matches1) == len(matches2)
    assert matches1[0].id == matches2[0].id  # Same cached objects


async def test_force_refresh(db_session: AsyncSession, mock_student_user: User):
    """force_refresh=True should recompute even if cached."""
    profile = await _seed_student_with_profile(db_session, mock_student_user)
    await _seed_institution_and_programs(db_session)

    from unipaith.services.matching_service import MatchingService
    svc = MatchingService(db_session)
    await svc.bootstrap_all_programs()

    matches1 = await svc.get_matches(profile.id)
    # Force refresh should not error
    matches2 = await svc.get_matches(profile.id, force_refresh=True)
    assert len(matches2) > 0


async def test_prediction_logging(db_session: AsyncSession, mock_student_user: User):
    """Verify prediction_logs table is populated after matching."""
    profile = await _seed_student_with_profile(db_session, mock_student_user)
    await _seed_institution_and_programs(db_session)

    from unipaith.services.matching_service import MatchingService
    svc = MatchingService(db_session)
    await svc.bootstrap_all_programs()
    await svc.get_matches(profile.id)

    from sqlalchemy import func, select
    count = (await db_session.execute(
        select(func.count()).select_from(PredictionLog)
        .where(PredictionLog.student_id == profile.id)
    )).scalar_one()
    assert count > 0


# ========================================================================
# API ENDPOINT TESTS
# ========================================================================


async def test_get_matches_endpoint(
    db_session: AsyncSession,
    student_client: AsyncClient,
    mock_student_user: User,
):
    profile = await _seed_student_with_profile(db_session, mock_student_user)
    await _seed_institution_and_programs(db_session)

    from unipaith.services.matching_service import MatchingService
    svc = MatchingService(db_session)
    await svc.bootstrap_all_programs()

    resp = await student_client.get("/api/v1/students/me/matches")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "match_score" in data[0]
    assert "reasoning_text" in data[0]


async def test_matches_require_auth(client: AsyncClient):
    resp = await client.get("/api/v1/students/me/matches")
    assert resp.status_code in (401, 403, 422)


async def test_log_engagement_signal(
    db_session: AsyncSession,
    student_client: AsyncClient,
    mock_student_user: User,
):
    profile = await _seed_student_with_profile(db_session, mock_student_user)
    programs = await _seed_institution_and_programs(db_session)

    resp = await student_client.post(
        "/api/v1/students/me/engagement",
        json={
            "program_id": str(programs[0].id),
            "signal_type": "viewed_program",
            "signal_value": 1,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["signal_type"] == "viewed_program"
    assert data["program_id"] == str(programs[0].id)
