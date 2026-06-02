"""Spec 41 — Graduate & PhD Admissions tests.

Covers the five §9 invariants:
1. Advisor match ranks by research-interest similarity; mutual-interest flagged.
2. Funding package cannot exceed source pool budget.
3. Department review is scoped to that department's applicants.
4. Two-stage release: department recommend → central confirm → offer (Spec 34).
5. Grad features hidden for undergrad programs.

Plus the two-stage role gate (faculty may recommend, not release) and the
funding-package → offer mirror that surfaces the package to the student (Spec 18).
"""

from __future__ import annotations

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from unipaith.core.exceptions import BadRequestException
from unipaith.database import get_db
from unipaith.dependencies import get_current_user
from unipaith.main import app
from unipaith.models.application import Application, OfferLetter
from unipaith.models.graduate import Department, FacultyProfile, FundingPool
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.graduate_service import GraduateService, is_graduate_degree


async def _user(db, role="student") -> User:
    u = User(
        id=uuid.uuid4(),
        email=f"{role}-{uuid.uuid4().hex[:8]}@test.edu",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole(role),
        is_active=True,
    )
    db.add(u)
    await db.flush()
    return u


async def _application(
    db, program: Program, status="submitted"
) -> tuple[StudentProfile, Application]:
    su = await _user(db, "student")
    profile = StudentProfile(user_id=su.id)
    db.add(profile)
    await db.flush()
    appn = Application(student_id=profile.id, program_id=program.id, status=status)
    db.add(appn)
    await db.flush()
    return profile, appn


async def _seed(db, admin_user: User, *, degree_type="phd", with_dept=True):
    inst = Institution(
        admin_user_id=admin_user.id, name="Test University", type="university", country="US"
    )
    db.add(inst)
    await db.flush()
    dept = None
    if with_dept:
        dept = Department(institution_id=inst.id, name="Computer Science", code="CS")
        db.add(dept)
        await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="PhD in Computer Science",
        degree_type=degree_type,
        department_id=dept.id if dept else None,
        is_published=True,
    )
    db.add(program)
    await db.flush()
    return inst, dept, program


# ── degree gating (§6 / invariant 5) ──────────────────────────────────────────


def test_is_graduate_degree_gating():
    for grad in ("phd", "PhD", "masters", "master", "MS", "MBA", "M.S."):
        assert is_graduate_degree(grad) is True, grad
    for ug in ("bachelors", "bachelor", "BS", "associate", "high_school", "", None):
        assert is_graduate_degree(ug) is False, ug


@pytest.mark.asyncio
async def test_grad_features_hidden_for_undergrad(db_session, mock_institution_user):
    """Invariant 5 — grad-only endpoints reject undergrad programs."""
    admin = await _persist(db_session, mock_institution_user)
    inst, _dept, program = await _seed(db_session, admin, degree_type="bachelors", with_dept=False)
    _profile, appn = await _application(db_session, program)
    svc = GraduateService(db_session)
    with pytest.raises(BadRequestException):
        await svc.list_advisor_matches(inst.id, appn.id)


# ── advisor matching (§2.1 / invariant 1) ─────────────────────────────────────


@pytest.mark.asyncio
async def test_advisor_match_ranks_by_similarity_and_flags_mutual(
    db_session, mock_institution_user
):
    """Invariant 1 — ranking by research similarity + mutual-interest flag."""
    admin = await _persist(db_session, mock_institution_user)
    inst, dept, program = await _seed(db_session, admin)
    _profile, appn = await _application(db_session, program)
    svc = GraduateService(db_session)

    aligned = FacultyProfile(
        institution_id=inst.id,
        department_id=dept.id,
        name="Dr Aligned",
        research_areas=["machine learning", "natural language processing"],
        accepting_students=True,
    )
    other = FacultyProfile(
        institution_id=inst.id,
        department_id=dept.id,
        name="Dr Other",
        research_areas=["medieval history", "poetry"],
    )
    db_session.add_all([aligned, other])
    await db_session.flush()

    # Applicant states research interests + names the aligned advisor.
    await svc.upsert_intent(
        inst.id,
        appn.id,
        {
            "research_interests": ["machine learning", "deep learning"],
            "target_advisor_ids": [str(aligned.id)],
        },
    )

    result = await svc.list_advisor_matches(inst.id, appn.id)
    matches = result["matches"]
    assert matches[0]["faculty_id"] == str(aligned.id), "aligned advisor must rank first"
    assert matches[0]["alignment_score"] > matches[-1]["alignment_score"]
    assert matches[0]["applicant_named_advisor"] is True
    # Not mutual until the advisor flags interest.
    assert matches[0]["mutual"] is False

    flagged = await svc.flag_advisor_interest(inst.id, appn.id, aligned.id, True)
    assert flagged["mutual"] is True, "named + flagged ⇒ mutual"


# ── funding budget (§2.3 / invariant 2) ───────────────────────────────────────


@pytest.mark.asyncio
async def test_funding_package_cannot_exceed_pool_budget(db_session, mock_institution_user):
    """Invariant 2 — a proposed/finalized package may not over-commit a pool."""
    admin = await _persist(db_session, mock_institution_user)
    inst, dept, program = await _seed(db_session, admin)
    _profile, appn = await _application(db_session, program)
    svc = GraduateService(db_session)

    pool = FundingPool(
        institution_id=inst.id,
        department_id=dept.id,
        name="Fellowship Pool",
        kind="fellowship",
        total_budget=25000,
    )
    db_session.add(pool)
    await db_session.flush()

    # A draft can be sketched freely.
    draft = await svc.build_funding_package(
        inst.id,
        appn.id,
        {
            "status": "draft",
            "components": [
                {
                    "kind": "fellowship",
                    "amount": 30000,
                    "source_pool_id": str(pool.id),
                    "years": [1],
                }
            ],
        },
    )
    assert draft["total_value"] == 30000.0

    # Finalizing the over-budget package is blocked.
    with pytest.raises(BadRequestException):
        await svc.build_funding_package(
            inst.id,
            appn.id,
            {
                "status": "finalized",
                "components": [
                    {
                        "kind": "fellowship",
                        "amount": 30000,
                        "source_pool_id": str(pool.id),
                        "years": [1],
                    }
                ],
            },
        )

    # A within-budget finalize succeeds and the budget reflects it.
    ok = await svc.build_funding_package(
        inst.id,
        appn.id,
        {
            "status": "finalized",
            "components": [
                {
                    "kind": "fellowship",
                    "amount": 20000,
                    "source_pool_id": str(pool.id),
                    "years": [1],
                }
            ],
        },
    )
    assert ok["status"] == "finalized"
    budget = await svc.funding_budget(inst.id)
    pool_row = next(p for p in budget["pools"] if p["id"] == str(pool.id))
    assert pool_row["committed"] == 20000.0
    assert pool_row["remaining"] == 5000.0
    assert pool_row["over"] is False


# ── department scoping (§2.4 / invariant 3) ───────────────────────────────────


@pytest.mark.asyncio
async def test_department_review_scoped_to_department(db_session, mock_institution_user):
    """Invariant 3 — the department review lists only that department's applicants."""
    admin = await _persist(db_session, mock_institution_user)
    inst, dept_cs, prog_cs = await _seed(db_session, admin)
    dept_bio = Department(institution_id=inst.id, name="Biology", code="BIO")
    db_session.add(dept_bio)
    await db_session.flush()
    prog_bio = Program(
        institution_id=inst.id,
        program_name="PhD in Biology",
        degree_type="phd",
        department_id=dept_bio.id,
        is_published=True,
    )
    db_session.add(prog_bio)
    await db_session.flush()
    _p1, app_cs = await _application(db_session, prog_cs)
    _p2, app_bio = await _application(db_session, prog_bio)

    svc = GraduateService(db_session)
    cs_review = await svc.list_department_review(inst.id, dept_cs.id)
    cs_ids = {a["application_id"] for a in cs_review["applicants"]}
    assert str(app_cs.id) in cs_ids
    assert str(app_bio.id) not in cs_ids, "Biology applicant must not appear in CS review"


# ── two-stage release (§2.4 / invariant 4) ────────────────────────────────────


@pytest.mark.asyncio
async def test_two_stage_release_recommend_then_confirm(db_session, mock_institution_user):
    """Invariant 4 — department recommends, central confirms, offer is released
    with the funding package mirrored onto it (Spec 34 / 18)."""
    admin = await _persist(db_session, mock_institution_user)
    inst, dept, program = await _seed(db_session, admin)
    _profile, appn = await _application(db_session, program)
    svc = GraduateService(db_session)

    pool = FundingPool(
        institution_id=inst.id,
        department_id=dept.id,
        name="RA Pool",
        kind="grant",
        total_budget=60000,
    )
    db_session.add(pool)
    await db_session.flush()
    await svc.build_funding_package(
        inst.id,
        appn.id,
        {
            "status": "finalized",
            "components": [
                {"kind": "RA", "amount": 30000, "source_pool_id": str(pool.id), "years": [1, 2]}
            ],
        },
    )

    # Stage 1 — department recommends (does NOT release).
    review = await svc.recommend(
        inst.id, appn.id, decision="admitted", committee_notes="Strong fit", actor_user_id=admin.id
    )
    assert review.central_status == "pending"
    await db_session.refresh(appn)
    assert appn.decision is None, "recommend must not release the decision"

    # Stage 2 — central confirms → release + offer.
    out = await svc.confirm_recommendation(inst.id, appn.id, actor_user_id=admin.id, notify=False)
    assert out["decision"] == "admitted"
    assert out["offer_id"] is not None
    await db_session.refresh(appn)
    assert appn.decision == "admitted"

    offer = await db_session.get(OfferLetter, uuid.UUID(out["offer_id"]))
    assert offer is not None
    # Funding package mirrored onto the offer (student sees it, Spec 18).
    assert offer.assistantship_details is not None
    assert offer.assistantship_details["kind"] == "graduate_funding_package"
    assert offer.assistantship_details["multi_year"] is True
    assert offer.financial_package_total == 30000

    review2 = await svc.get_department_review(inst.id, appn.id)
    assert review2.central_status == "confirmed"


# ── two-stage role gate (faculty recommend, not release) ──────────────────────


@pytest.mark.asyncio
async def test_faculty_can_recommend_but_not_release(db_session, mock_institution_user):
    """The faculty sub-role may recommend (200) but cannot confirm/release (403)."""
    admin = await _persist(db_session, mock_institution_user)
    inst, dept, program = await _seed(db_session, admin)
    _profile, appn = await _application(db_session, program)

    # A faculty user linked to a profile in this department.
    fac_user = await _user(db_session, "faculty")
    fac = FacultyProfile(
        institution_id=inst.id, department_id=dept.id, user_id=fac_user.id, name="Dr Faculty"
    )
    db_session.add(fac)
    await db_session.flush()

    async def _odb():
        yield db_session

    async def _ouser():
        return fac_user

    app.dependency_overrides[get_db] = _odb
    app.dependency_overrides[get_current_user] = _ouser
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            base = "/api/v1/institutions/me/graduate"
            # Faculty may recommend.
            r = await ac.post(
                f"{base}/applications/{appn.id}/recommend",
                json={"decision": "admitted", "committee_notes": "ok"},
            )
            assert r.status_code == 200, r.text
            # Faculty may NOT release (two-stage gate → 403).
            r2 = await ac.post(f"{base}/applications/{appn.id}/confirm", json={})
            assert r2.status_code == 403, r2.text
    finally:
        app.dependency_overrides.clear()


# ── SoP extractor (§2.2 / §5) ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sop_extractor_populates_when_flag_on(db_session, mock_institution_user, monkeypatch):
    """With the AI flag on, the SoP extractor auto-tags research interests."""
    from unipaith.config import settings

    monkeypatch.setattr(settings, "ai_graduate_v2_enabled", True)
    admin = await _persist(db_session, mock_institution_user)
    inst, dept, program = await _seed(db_session, admin)
    _profile, appn = await _application(db_session, program)
    svc = GraduateService(db_session)

    # A faculty research vocabulary to ground the extraction.
    db_session.add(
        FacultyProfile(
            institution_id=inst.id,
            department_id=dept.id,
            name="Dr ML",
            research_areas=["machine learning", "robotics"],
        )
    )
    await db_session.flush()

    intent = await svc.upsert_intent(
        inst.id,
        appn.id,
        {
            "statement_of_purpose": "My research centers on machine learning applied to robotics.",
            "research_interests": [],
        },
    )
    tags = [t.lower() for t in (intent.extracted_interests or [])]
    assert "machine learning" in tags
    assert intent.alignment_summary


@pytest.mark.asyncio
async def test_student_advisor_matches_read_only(db_session, mock_institution_user):
    """Spec 41 §2.1 — the student-facing "advisors who fit your research" view
    ranks by research fit and is read-only (writes no AdvisorMatch rows)."""
    from sqlalchemy import func
    from sqlalchemy import select as _select

    from unipaith.models.graduate import AdvisorMatch

    admin = await _persist(db_session, mock_institution_user)
    inst, dept, program = await _seed(db_session, admin)
    profile, appn = await _application(db_session, program)
    svc = GraduateService(db_session)

    aligned = FacultyProfile(
        institution_id=inst.id,
        department_id=dept.id,
        name="Dr Fit",
        research_areas=["machine learning", "robotics"],
        accepting_students=True,
    )
    other = FacultyProfile(
        institution_id=inst.id,
        department_id=dept.id,
        name="Dr Unrelated",
        research_areas=["poetry"],
    )
    db_session.add_all([aligned, other])
    await db_session.flush()
    # Applicant states interests via the student path.
    await svc.student_upsert_intent(
        profile.id, appn.id, {"research_interests": ["machine learning"]}
    )

    out = await svc.student_advisor_matches(profile.id, appn.id)
    assert out["is_graduate"] is True
    assert out["matches"][0]["faculty_name"] == "Dr Fit"
    assert out["matches"][0]["alignment_score"] > out["matches"][-1]["alignment_score"]
    # Read-only: no AdvisorMatch rows were written by the student view.
    count = await db_session.scalar(
        _select(func.count(AdvisorMatch.id)).where(AdvisorMatch.application_id == appn.id)
    )
    assert count == 0


async def _persist(db, user: User) -> User:
    if user.id is None:
        user.id = uuid.uuid4()
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
