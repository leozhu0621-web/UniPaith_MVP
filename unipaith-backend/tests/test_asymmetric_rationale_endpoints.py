"""Spec 06 §3 / §5.5 — asymmetric rationale, end-to-end through the API.

Seeds one cached `MatchRationale` whose citations mix a student-safe program
fact with an institution-only comparative signal, then proves:

  * the STUDENT endpoint (`POST /me/matches/{id}/rationale`) returns the
    redacted projection (the institution-only citation is withheld), and
  * the INSTITUTION view (`ReviewPipelineService.get_match_rationale_for_review`)
    returns the full, loss-less projection (the same citation is present).

This is the wiring proof on top of the pure-function contract in
`test_rationale_redaction.py`.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.cache_invalidation import RATIONALE_PROMPT_VERSION
from unipaith.models.ai_artifacts import MatchRationale, StudentFeatureVector
from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

MATCHES = "/api/v1/students/me/matches"

SAFE_PROGRAM_CITATION = "program.outcomes"
INSTITUTION_ONLY_CITATION = "program.selectivity_delta"
STUDENT_CITATION = "sparse.research_experience"


async def _seed_asymmetric_rationale(
    db: AsyncSession, student_user: User
) -> tuple[StudentProfile, Institution, Program, Application]:
    profile = StudentProfile(user_id=student_user.id)
    db.add(student_user)
    db.add(profile)
    await db.flush()

    # A feature vector must exist for the rationale cache lookup.
    db.add(StudentFeatureVector(student_id=profile.id, profile_version=1, sparse_features={}))

    admin = User(
        id=uuid4(),
        email=f"inst-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid4().hex[:8]}",
        role=UserRole.institution_admin,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    inst = Institution(admin_user_id=admin.id, name="Test U", type="university", country="US")
    db.add(inst)
    await db.flush()
    program = Program(institution_id=inst.id, program_name="CS MS", degree_type="masters")
    db.add(program)
    await db.flush()

    db.add(
        MatchResult(
            student_id=profile.id,
            program_id=program.id,
            fitness_score=Decimal("0.82"),
            confidence_score=Decimal("0.61"),
            fitness_breakdown={"academic_fit": 0.9, "cohort_percentile": 0.95},
            confidence_breakdown={"reason": "test", "calibration": {"calibrator_n_samples": 10}},
        )
    )
    # The cached rationale — keys must match the lookup (profile_v=1,
    # program_v=program.feature_version=1, prompt_v=current).
    db.add(
        MatchRationale(
            student_id=profile.id,
            program_id=program.id,
            profile_version=1,
            program_version=1,
            prompt_version=RATIONALE_PROMPT_VERSION,
            rationale_text="Strong research alignment; selective program.",
            cited_student_fields=[STUDENT_CITATION],
            cited_program_fields=[SAFE_PROGRAM_CITATION, INSTITUTION_ONLY_CITATION],
        )
    )
    app = Application(student_id=profile.id, program_id=program.id, status="submitted")
    db.add(app)
    await db.commit()
    await db.refresh(program)
    await db.refresh(app)
    return profile, inst, program, app


@pytest.mark.asyncio
async def test_student_rationale_endpoint_is_redacted(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    _, _, program, _ = await _seed_asymmetric_rationale(db_session, mock_student_user)

    resp = await student_client.post(f"{MATCHES}/{program.id}/rationale")
    assert resp.status_code == 200
    body = resp.json()

    # The student keeps their own signal + the public program fact …
    assert STUDENT_CITATION in body["cited_student_fields"]
    assert SAFE_PROGRAM_CITATION in body["cited_program_fields"]
    # … but the institution-only comparative signal is withheld.
    assert INSTITUTION_ONLY_CITATION not in body["cited_program_fields"]
    assert body["redacted"] is True
    assert body["rationale_text"]


@pytest.mark.asyncio
async def test_institution_view_is_lossless(db_session: AsyncSession, mock_student_user: User):
    _, inst, _, app = await _seed_asymmetric_rationale(db_session, mock_student_user)

    from unipaith.services.review_pipeline_service import ReviewPipelineService

    result = await ReviewPipelineService(db_session).get_match_rationale_for_review(inst.id, app.id)

    assert result["available"] is True
    assert result["redacted"] is False
    # The reviewer sees the full evidence — including the comparative signal.
    assert SAFE_PROGRAM_CITATION in result["cited_program_fields"]
    assert INSTITUTION_ONLY_CITATION in result["cited_program_fields"]
    assert STUDENT_CITATION in result["cited_student_fields"]
    # Full breakdowns retained for the reviewer.
    assert "cohort_percentile" in result["fitness_breakdown"]


@pytest.mark.asyncio
async def test_institution_view_tenant_guarded(db_session: AsyncSession, mock_student_user: User):
    """A reviewer from another institution cannot read the rationale."""
    _, _, _, app = await _seed_asymmetric_rationale(db_session, mock_student_user)

    from unipaith.core.exceptions import NotFoundException
    from unipaith.services.review_pipeline_service import ReviewPipelineService

    other_inst_id = uuid4()
    with pytest.raises(NotFoundException):
        await ReviewPipelineService(db_session).get_match_rationale_for_review(
            other_inst_id, app.id
        )
