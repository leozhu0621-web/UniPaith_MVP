"""Regression: a signup-wizard student's interest track must reach the matcher
field so the field signal + wrong-discipline veto fire — and the onboarding seed
must read the JUST-PICKED interests (ordering bug: the seed ran before
profile.onboarding_state was updated, so matches were computed field-blind)."""

import pytest
from sqlalchemy import select

from tests._uni_helpers import ensure_profile
from unipaith.models.ai_artifacts import StudentFeatureVector
from unipaith.models.student import StudentProfile
from unipaith.schemas.student import OnboardingAnswers, PatchOnboardingStateRequest
from unipaith.services.match_service import MatchService
from unipaith.services.matching import ProgramFeatures, StudentFeatures, score
from unipaith.services.student_service import StudentService


@pytest.mark.asyncio
async def test_seed_matches_sees_just_picked_interests(db_session, mock_student_user, monkeypatch):
    """At seed time the profile must already carry the new interests, else the
    match overlay sets no field_of_study and matches are field-blind."""
    await ensure_profile(db_session, mock_student_user)
    svc = StudentService(db_session)

    seen: dict = {}

    async def _capture_seed(student_id):
        prof = await db_session.scalar(
            select(StudentProfile).where(StudentProfile.id == student_id)
        )
        seen["interests"] = ((prof.onboarding_state or {}).get("answers") or {}).get("interests")

    monkeypatch.setattr(svc, "_seed_matches_from_onboarding", _capture_seed)

    await svc.patch_onboarding_state(
        mock_student_user.id,
        PatchOnboardingStateRequest(
            answers=OnboardingAnswers(interests=["cs_data_ai"], degree_level="bachelors"),
            completed=True,
        ),
    )
    # With the bug, the seed read the PRE-merge state → None. After the fix it
    # sees the just-picked interest, so the overlay can set field_of_study.
    assert seen.get("interests") == ["cs_data_ai"], seen


@pytest.mark.asyncio
async def test_wizard_interest_sets_field_of_study(db_session, mock_student_user):
    profile = await ensure_profile(db_session, mock_student_user)
    profile.onboarding_state = {"answers": {"interests": ["cs_data_ai"]}}
    db_session.add(
        StudentFeatureVector(
            student_id=profile.id,
            sparse_features={"education_level": "bachelors", "intended_majors": []},
        )
    )
    await db_session.flush()

    feats = await MatchService(db_session)._student_features(profile.id)
    assert feats is not None
    assert feats.sparse.get("field_of_study") == "computer_science", feats.sparse


def test_field_veto_sinks_history_for_cs_student():
    student = StudentFeatures(
        sparse={"education_level": "bachelors", "field_of_study": "computer_science"},
        embedding=None,
        profile_completeness=0.8,
    )
    cs = ProgramFeatures(
        program_id="cs",
        sparse={"target_education_level": "bachelors", "fields_offered": ["computer_science"]},
    )
    history = ProgramFeatures(
        program_id="hist",
        sparse={"target_education_level": "bachelors", "fields_offered": ["history"]},
    )
    cs_fit = float(score(student, cs, cpef_enabled=True).fitness)
    hist = score(student, history, cpef_enabled=True)
    keys = [d.get("key") for d in (hist.fitness_breakdown or {}).get("dealbreakers", [])]
    assert cs_fit > float(hist.fitness)
    assert "field" in keys, hist.fitness_breakdown
