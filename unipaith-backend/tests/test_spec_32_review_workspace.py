"""Spec 32 — Review Workspace: consolidated packet, side-by-side variance +
synthesis (§4), grounded assistant (§6), integrity actions (§7), blind review
+ reveal (§7A.1), test-optional (§7A.3), calibration (§7A.2), locked applicant
(§9). Runs in AI_MOCK_MODE → exercises the deterministic rule-based paths."""

from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application, ApplicationScore, IntegritySignal, Rubric
from unipaith.models.institution import Institution, Program, Reviewer
from unipaith.models.student import StudentProfile
from unipaith.models.user import User

API = "/api/v1/reviews"


async def _seed(db: AsyncSession, student_user: User, inst_user: User, *, blind: bool = False):
    db.add(student_user)
    db.add(inst_user)
    profile = StudentProfile(
        user_id=student_user.id,
        first_name="Sienna",
        last_name="Chen",
        nationality="Canada",
        date_of_birth=__import__("datetime").date(2003, 4, 1),
    )
    db.add(profile)
    institution = Institution(
        admin_user_id=inst_user.id,
        name="Test University",
        type="university",
        country="United States",
        review_config={"blind_review_default": blind, "calibration_enabled": True},
    )
    db.add(institution)
    await db.flush()
    program = Program(
        institution_id=institution.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
        requirements={"test_policy": "test_optional"},
    )
    db.add(program)
    await db.flush()
    application = Application(student_id=profile.id, program_id=program.id, status="submitted")
    db.add(application)
    reviewer = Reviewer(institution_id=institution.id, user_id=inst_user.id, name="Dr. Reviewer")
    db.add(reviewer)
    await db.flush()
    return profile, institution, program, application, reviewer


@pytest.mark.asyncio
async def test_review_packet_has_real_name_and_rubric_scores(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, inst, program, app, reviewer = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    rubric = Rubric(
        institution_id=inst.id,
        program_id=program.id,
        rubric_name="R",
        criteria=[{"name": "academics", "weight": 0.5, "max_score": 5}],
        is_active=True,
    )
    db_session.add(rubric)
    await db_session.flush()
    # Two reviewers diverge on the same criterion.
    r2 = Reviewer(institution_id=inst.id, user_id=mock_student_user.id, name="Dr. Two")
    db_session.add(r2)
    await db_session.flush()
    db_session.add_all(
        [
            ApplicationScore(
                application_id=app.id,
                reviewer_id=reviewer.id,
                rubric_id=rubric.id,
                criterion_scores={"academics": 5},
                total_weighted_score=Decimal("2.5"),
                reviewer_notes="Excellent",
                scored_by_type="human",
            ),
            ApplicationScore(
                application_id=app.id,
                reviewer_id=r2.id,
                rubric_id=rubric.id,
                criterion_scores={"academics": 2},
                total_weighted_score=Decimal("1.0"),
                reviewer_notes="Concerns",
                scored_by_type="human",
            ),
        ]
    )
    await db_session.commit()

    resp = await institution_client.get(f"{API}/applications/{app.id}/review-packet")
    assert resp.status_code == 200
    data = resp.json()
    assert data["student"]["display_name"] == "Sienna Chen"
    assert data["reviewer_count"] == 2
    crit = next(c for c in data["rubric_scores"] if c["criterion"] == "academics")
    assert crit["variance"] == 3.0 and crit["divergent"] is True
    assert data["blind_review"]["enabled"] is False
    assert data["test_optional"]["policy"] == "test_optional"
    assert data["locked"] is False


@pytest.mark.asyncio
async def test_blind_review_redacts_then_reveal_unredacts(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, inst, program, app, _ = await _seed(
        db_session, mock_student_user, mock_institution_user, blind=True
    )
    await db_session.commit()

    resp = await institution_client.get(f"{API}/applications/{app.id}/review-packet")
    data = resp.json()
    assert data["blind_review"]["enabled"] is True
    assert data["blind_review"]["revealed"] is False
    assert data["student"]["display_name"].startswith("Applicant")
    assert data["student"]["first_name"] is None
    assert "first_name" in data["blind_review"]["redacted_fields"]

    # Reveal is audit-logged; re-fetch with reveal=true unredacts.
    rev = await institution_client.post(
        f"{API}/applications/{app.id}/reveal-identity", json={"reason": "post-score review"}
    )
    assert rev.status_code == 200 and rev.json()["revealed"] is True
    data2 = (
        await institution_client.get(
            f"{API}/applications/{app.id}/review-packet", params={"reveal": "true"}
        )
    ).json()
    assert data2["student"]["display_name"] == "Sienna Chen"
    assert data2["blind_review"]["revealed"] is True


@pytest.mark.asyncio
async def test_locked_applicant_blocks_scoring(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, inst, program, app, _ = await _seed(db_session, mock_student_user, mock_institution_user)
    rubric = Rubric(
        institution_id=inst.id,
        program_id=program.id,
        rubric_name="R",
        criteria=[{"name": "fit", "weight": 1.0, "max_score": 5}],
        is_active=True,
    )
    db_session.add(rubric)
    app.decision = "admitted"  # released decision → locked
    await db_session.commit()

    resp = await institution_client.post(
        f"{API}/applications/{app.id}/score",
        json={"rubric_id": str(rubric.id), "criterion_scores": {"fit": 4}},
    )
    assert resp.status_code == 400
    assert "locked" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_integrity_action_reject_flips_application(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, inst, program, app, _ = await _seed(db_session, mock_student_user, mock_institution_user)
    sig = IntegritySignal(
        application_id=app.id,
        institution_id=inst.id,
        signal_type="duplicate_submission",
        severity="high",
        title="Duplicate detected",
        description="dup",
        status="open",
    )
    db_session.add(sig)
    await db_session.commit()

    resp = await institution_client.post(
        f"{API}/integrity-signals/{sig.id}/action",
        json={"action": "reject_application", "notes": "confirmed fraud"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "rejected" and body["rejected_application"] is True
    await db_session.refresh(app)
    assert app.decision == "rejected"


@pytest.mark.asyncio
async def test_synthesis_and_assistant_rule_based(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    _, inst, program, app, reviewer = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    rubric = Rubric(
        institution_id=inst.id,
        program_id=program.id,
        rubric_name="R",
        criteria=[{"name": "academics", "weight": 1.0, "max_score": 5}],
        is_active=True,
    )
    db_session.add(rubric)
    r2 = Reviewer(institution_id=inst.id, user_id=mock_student_user.id, name="Dr. Two")
    db_session.add(r2)
    await db_session.flush()
    db_session.add_all(
        [
            ApplicationScore(
                application_id=app.id,
                reviewer_id=reviewer.id,
                rubric_id=rubric.id,
                criterion_scores={"academics": 5},
                total_weighted_score=Decimal("5"),
                scored_by_type="human",
            ),
            ApplicationScore(
                application_id=app.id,
                reviewer_id=r2.id,
                rubric_id=rubric.id,
                criterion_scores={"academics": 2},
                total_weighted_score=Decimal("2"),
                scored_by_type="human",
            ),
        ]
    )
    await db_session.commit()

    syn = await institution_client.post(f"{API}/applications/{app.id}/synthesize")
    assert syn.status_code == 200
    sd = syn.json()
    assert sd["agreement"] == "divergent" and sd["reviewer_count"] == 2
    assert sd["model_used"] == "rule_based"  # AI_MOCK_MODE

    chat = await institution_client.post(
        f"{API}/applications/{app.id}/assistant-chat",
        json={"question": "What's their strongest signal?"},
    )
    assert chat.status_code == 200
    assert chat.json()["answer"]


@pytest.mark.asyncio
async def test_calibration_reports_drift_and_test_optional(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, inst, program, app, reviewer = await _seed(
        db_session, mock_student_user, mock_institution_user
    )
    rubric = Rubric(
        institution_id=inst.id,
        program_id=program.id,
        rubric_name="R",
        criteria=[{"name": "academics", "weight": 1.0, "max_score": 5}],
        is_active=True,
    )
    db_session.add(rubric)
    await db_session.flush()
    db_session.add(
        ApplicationScore(
            application_id=app.id,
            reviewer_id=reviewer.id,
            rubric_id=rubric.id,
            criterion_scores={"academics": 4},
            total_weighted_score=Decimal("4"),
            scored_by_type="human",
        )
    )
    await db_session.commit()

    resp = await institution_client.get(f"{API}/calibration")
    assert resp.status_code == 200
    data = resp.json()
    assert "inter_rater" in data and "reviewer_drift" in data
    assert "test_optional_cohort" in data
    assert data["test_optional_cohort"]["non_submitters"]["n"] >= 1
