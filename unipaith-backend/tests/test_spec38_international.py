"""Spec 38 · International Admissions (institution processing).

Covers the §9 acceptance tests:
- foreign GPA normalizes to the program scale; reviewer sees raw + normalized;
- I-20 generation blocked until financial proof (+ admit + enrollment intent),
  and every generation is audit-logged;
- the international tab is hidden for domestic applicants;
- country-requirement pack auto-attaches by nationality;
- English-proficiency waiver eligibility (native country / prior degree).
"""

import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from unipaith.core.exceptions import UnprocessableEntityException
from unipaith.models.application import Application, EnrollmentRecord
from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.institution import Institution, Program
from unipaith.models.student import (
    AcademicRecord,
    StudentProfile,
    StudentVisaInfo,
    TestScore,
)
from unipaith.models.user import User, UserRole
from unipaith.services.international_service import InternationalService

pytestmark = pytest.mark.asyncio


async def _seed_intl(
    db,
    inst_user,
    *,
    nationality="China",
    inst_country="US",
    gpa=85,
    gpa_scale="percentage",
    financial_proof=True,
    visa_required=True,
    decision=None,
    enrollment_state=None,
    english_policy=None,
    transcript_language=None,
    status="submitted",
):
    db.add(inst_user)
    await db.flush()
    inst = Institution(
        admin_user_id=inst_user.id,
        name="Foo U",
        type="university",
        country=inst_country,
        city="Boston",
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="MS Computer Science",
        degree_type="masters",
        description_text="A program.",
        tuition=48000,
        is_published=True,
        english_policy=english_policy,
    )
    db.add(program)
    await db.flush()
    su = User(
        id=uuid.uuid4(),
        email=f"stu-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db.add(su)
    await db.flush()
    profile = StudentProfile(
        user_id=su.id,
        first_name="Li",
        last_name="Wei",
        nationality=nationality,
        place_of_birth=nationality,
        country_of_residence=nationality,
    )
    db.add(profile)
    await db.flush()
    db.add(
        AcademicRecord(
            student_id=profile.id,
            institution_name="Source University",
            degree_type="bachelors",
            gpa=gpa,
            gpa_scale=gpa_scale,
            grading_scale_type=gpa_scale,
            country=nationality,
            transcript_language=transcript_language,
        )
    )
    db.add(
        StudentVisaInfo(
            student_id=profile.id,
            visa_required=visa_required,
            financial_proof_available=financial_proof,
            financial_proof_amount_band="50000-75000",
            sponsorship_source="self",
        )
    )
    db.add(TestScore(student_id=profile.id, test_type="TOEFL", total_score=100))
    app = Application(
        student_id=profile.id,
        program_id=program.id,
        status=status,
        decision=decision,
        submitted_at=datetime.now(UTC),
    )
    db.add(app)
    await db.flush()
    if enrollment_state:
        db.add(
            EnrollmentRecord(
                application_id=app.id,
                student_id=profile.id,
                program_id=program.id,
                state=enrollment_state,
            )
        )
        await db.flush()
    await db.commit()
    return inst, program, profile, app


# ── §9: GPA normalization (raw + normalized) ─────────────────────────────────
async def test_foreign_gpa_normalizes_raw_and_normalized(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, gpa=85, gpa_scale="percentage"
    )
    svc = InternationalService(db_session)
    result = await svc.normalize_gpa(inst.id, app.id, mock_institution_user.id)
    assert result["normalized_gpa"] == "3.6"
    assert "85" in result["source_scale"]
    assert result["raw_gpa"].startswith("85")
    # The reviewer sees both raw and normalized in the workspace view.
    view = await svc.get_or_init(inst.id, app.id)
    assert view["processing"]["credential_eval"]["normalized_gpa"] == "3.6"
    assert view["student_inputs"]["raw_gpa"].startswith("85")


# ── §9: I-20 gate (financial proof + admit + enrollment intent) ──────────────
async def test_i20_blocked_without_financial_proof(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session,
        mock_institution_user,
        financial_proof=False,
        decision="admitted",
        enrollment_state="intent_confirmed",
    )
    svc = InternationalService(db_session)
    with pytest.raises(UnprocessableEntityException) as exc:
        await svc.generate_immigration_doc(inst.id, app.id, mock_institution_user.id)
    fields = [b["field"] for b in exc.value.detail["missing_fields"]]
    assert "financial_proof_available" in fields


async def test_i20_blocked_without_enrollment_intent(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session,
        mock_institution_user,
        financial_proof=True,
        decision="admitted",
        enrollment_state=None,
    )
    svc = InternationalService(db_session)
    with pytest.raises(UnprocessableEntityException) as exc:
        await svc.generate_immigration_doc(inst.id, app.id, mock_institution_user.id)
    fields = [b["field"] for b in exc.value.detail["missing_fields"]]
    assert "enrollment_intent" in fields


async def test_i20_blocked_without_admit(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session,
        mock_institution_user,
        financial_proof=True,
        decision=None,
        enrollment_state="intent_confirmed",
    )
    svc = InternationalService(db_session)
    with pytest.raises(UnprocessableEntityException) as exc:
        await svc.generate_immigration_doc(inst.id, app.id, mock_institution_user.id)
    fields = [b["field"] for b in exc.value.detail["missing_fields"]]
    assert "decision" in fields


async def test_i20_generates_when_ready_and_audits(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session,
        mock_institution_user,
        financial_proof=True,
        decision="admitted",
        enrollment_state="intent_confirmed",
    )
    svc = InternationalService(db_session)
    result = await svc.generate_immigration_doc(
        inst.id, app.id, mock_institution_user.id, doc_type="I-20"
    )
    assert result["status"] == "drafted"
    assert result["sevis_id"]
    assert result["sevis_export"]["form_type"] == "I-20"
    assert result["sevis_export"]["visa_class"] == "F-1"
    # Every generation is audit-logged (§2.4 / §36 / §46).
    rows = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(
                    AdmissionsAuditLog.action == "immigration_doc_generate"
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].application_id == app.id


async def test_ds2019_generates_with_j1_class(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session,
        mock_institution_user,
        financial_proof=True,
        decision="conditional_admission",
        enrollment_state="enrollment_confirmed",
    )
    svc = InternationalService(db_session)
    result = await svc.generate_immigration_doc(
        inst.id, app.id, mock_institution_user.id, doc_type="DS-2019"
    )
    assert result["sevis_export"]["visa_class"] == "J-1"


# ── §9: domestic applicant → tab hidden ──────────────────────────────────────
async def test_international_tab_hidden_for_domestic(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session,
        mock_institution_user,
        nationality="United States",
        inst_country="US",
        visa_required=False,
    )
    svc = InternationalService(db_session)
    view = await svc.get_or_init(inst.id, app.id)
    assert view["is_international"] is False
    # No processing record is initialized for a domestic applicant.
    assert view["processing"] is None
    # The packet summary agrees so the UI hides the tab.
    loaded = await svc._load_profile(profile.id)
    summary = await svc.packet_summary(app, program, loaded, inst)
    assert summary["is_international"] is False


async def test_international_applicant_flagged(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, nationality="China", inst_country="US"
    )
    svc = InternationalService(db_session)
    loaded = await svc._load_profile(profile.id)
    summary = await svc.packet_summary(app, program, loaded, inst)
    assert summary["is_international"] is True
    assert "never a selection criterion" in summary["fairness_note"]


# ── §9: country-requirement pack auto-attaches by nationality ────────────────
async def test_country_pack_auto_attaches_by_nationality(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, nationality="China"
    )
    svc = InternationalService(db_session)
    view = await svc.get_or_init(inst.id, app.id)
    assert view["is_international"] is True
    items = view["processing"]["country_requirements"]
    assert len(items) >= 1
    assert any("Credential evaluation" in it["item"] for it in items)
    assert all(it["status"] == "pending" for it in items)


async def test_suggest_country_pack_sets_requirements(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, nationality="India"
    )
    svc = InternationalService(db_session)
    await svc.get_or_init(inst.id, app.id)
    result = await svc.suggest_country_pack(inst.id, app.id, mock_institution_user.id)
    assert result["ai_used"] is False  # flag off in tests → deterministic default
    assert len(result["requirements"]) >= 1


# ── English-proficiency waiver (§2.2) ────────────────────────────────────────
async def test_english_waiver_native_country(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, nationality="Australia", inst_country="US"
    )
    svc = InternationalService(db_session)
    loaded = await svc._load_profile(profile.id)
    elig = svc.english_waiver_eligibility(loaded, program)
    assert elig["eligible"] is True
    assert "English-speaking" in elig["basis"]


async def test_english_waiver_prior_degree_in_english(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session,
        mock_institution_user,
        nationality="China",
        transcript_language="English",
        english_policy={"waiver_prior_degree_in_english": True},
    )
    svc = InternationalService(db_session)
    loaded = await svc._load_profile(profile.id)
    elig = svc.english_waiver_eligibility(loaded, program)
    assert elig["eligible"] is True
    assert "English" in elig["basis"]


async def test_english_no_waiver_when_not_eligible(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, nationality="China", transcript_language="Mandarin"
    )
    svc = InternationalService(db_session)
    loaded = await svc._load_profile(profile.id)
    elig = svc.english_waiver_eligibility(loaded, program)
    assert elig["eligible"] is False


# ── update + feasibility ─────────────────────────────────────────────────────
async def test_update_persists_and_feasibility(db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, nationality="China"
    )
    svc = InternationalService(db_session)
    await svc.get_or_init(inst.id, app.id)
    view = await svc.update(
        inst.id,
        app.id,
        mock_institution_user.id,
        {
            "credential_status": "verified",
            "english_test": "TOEFL",
            "english_score": 105,
            "english_meets_minimum": True,
            "visa_outcome": "approved",
        },
    )
    assert view["processing"]["credential_eval"]["status"] == "verified"
    assert view["processing"]["english_proficiency"]["meets_minimum"] is True
    assert view["feasibility"]["band"] == "strong"  # visa approved short-circuits


# ── HTTP endpoints ───────────────────────────────────────────────────────────
async def test_get_international_via_api(institution_client, db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, nationality="China"
    )
    r = await institution_client.get(f"/api/v1/applications/review/{app.id}/international")
    assert r.status_code == 200
    body = r.json()
    assert body["is_international"] is True
    assert body["processing"] is not None
    assert body["immigration_gate"]["can_generate"] is False  # not admitted yet


async def test_english_policy_patch_via_api(institution_client, db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(db_session, mock_institution_user)
    r = await institution_client.patch(
        f"/api/v1/institutions/me/programs/{program.id}/english-policy",
        json={
            "accepted_tests": [{"test": "TOEFL", "min_score": 100}],
            "waiver_prior_degree_in_english": True,
        },
    )
    assert r.status_code == 200
    policy = r.json()["english_policy"]
    assert policy["accepted_tests"][0]["test"] == "TOEFL"
    assert policy["waiver_prior_degree_in_english"] is True


async def test_country_requirements_via_api(institution_client, db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(db_session, mock_institution_user)
    r = await institution_client.get("/api/v1/institutions/me/international/country-requirements")
    assert r.status_code == 200
    packs = r.json()
    assert any(p["country_code"] == "CN" for p in packs)


async def test_i20_generate_via_api_blocked(institution_client, db_session, mock_institution_user):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, financial_proof=False, decision="admitted"
    )
    r = await institution_client.post(
        f"/api/v1/applications/review/{app.id}/immigration-doc/generate",
        json={"doc_type": "I-20"},
    )
    assert r.status_code == 422


async def test_applicants_queue_lists_only_international(
    institution_client, db_session, mock_institution_user
):
    inst, program, profile, app = await _seed_intl(
        db_session, mock_institution_user, nationality="China", inst_country="US"
    )
    r = await institution_client.get("/api/v1/institutions/me/international/applicants")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["application_id"] == str(app.id)
    assert rows[0]["nationality"] == "China"
    assert rows[0]["immigration_doc_status"] == "not_started"
