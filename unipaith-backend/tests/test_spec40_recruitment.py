"""Spec 40 · Recruitment CRM (Pre-Applicant).

Covers the §9 invariants:
- Prospect import dedups + applies suppression; consent defaults respected.
- Prospect converts to applicant with a forward link; no duplicate person record.
- Fair visit captures prospects tagged with source → shows in attribution (28).
- Territory dashboard math (conversion, yield) correct.

Plus: ProspectPrioritizer ranking + manual fallback, TerritoryOptimizer
deterministic fallback (no 5xx), trip over-budget / conflict flags, the
prospect→segment consent gate, and an API smoke pass.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import func, select

from unipaith.config import settings
from unipaith.models.application import Application
from unipaith.models.attribution import AttributionEvent
from unipaith.models.institution import CampaignSuppression, Institution, Program, UploadedContact
from unipaith.models.recruitment import Prospect
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.schemas.recruitment import (
    CapturedLead,
    ConvertProspectRequest,
    CreateFairRequest,
    CreateProspectRequest,
    CreateTerritoryRequest,
    CreateTripRequest,
    FairCaptureRequest,
    ProspectImportRequest,
    ProspectImportRow,
    ProspectToSegmentRequest,
)
from unipaith.services.recruitment_service import RecruitmentService

pytestmark = pytest.mark.asyncio


async def _seed_institution(db, inst_user: User) -> Institution:
    db.add(inst_user)
    await db.flush()
    inst = Institution(
        admin_user_id=inst_user.id,
        name="Foo U",
        type="university",
        country="US",
        city="Boston",
    )
    db.add(inst)
    await db.flush()
    return inst


async def _seed_application(db, inst: Institution) -> Application:
    program = Program(
        institution_id=inst.id,
        program_name="MS Computer Science",
        degree_type="masters",
        description_text="A program.",
        is_published=True,
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
    profile = StudentProfile(user_id=su.id)
    db.add(profile)
    await db.flush()
    app = Application(
        student_id=profile.id,
        program_id=program.id,
        status="in_progress",
    )
    db.add(app)
    await db.flush()
    return app


# ── §9.1 import: dedup + suppression + consent default ────────────────────────


async def test_import_dedups_applies_suppression_and_consent_default(
    db_session, mock_institution_user
):
    inst = await _seed_institution(db_session, mock_institution_user)
    # Pre-suppress one email (e.g. a prior unsubscribe).
    db_session.add(
        CampaignSuppression(
            institution_id=inst.id, email="blocked@example.com", reason="unsubscribe"
        )
    )
    await db_session.flush()

    svc = RecruitmentService(db_session)
    req = ProspectImportRequest(
        source="list",
        source_detail="Spring fair purchase",
        rows=[
            ProspectImportRow(name="Ada Lovelace", email="ada@example.com"),
            ProspectImportRow(name="Ada Dup", email="ADA@example.com"),  # dup (case-insensitive)
            ProspectImportRow(
                name="Blocked Person", email="blocked@example.com", consent_outreach=True
            ),
            ProspectImportRow(
                name="Grace Hopper", email="grace@example.com", consent_outreach=True
            ),
            ProspectImportRow(name="No Email Person", email=None),
        ],
    )
    result = await svc.import_prospects(inst.id, req)

    assert result["total_rows"] == 5
    assert result["imported"] == 4  # ada, blocked, grace, no-email (dup excluded)
    assert result["deduped"] == 1  # the ADA@ duplicate
    assert result["suppressed"] == 1  # blocked@

    rows = (
        (await db_session.execute(select(Prospect).where(Prospect.institution_id == inst.id)))
        .scalars()
        .all()
    )
    by_email = {(_p.email or "").lower(): _p for _p in rows}
    # Suppressed address: imported as a record but outreach consent forced off.
    assert by_email["blocked@example.com"].consent_outreach is False
    # No explicit opt-in → consent defaults off (opt-in only, §7/46).
    assert by_email["ada@example.com"].consent_outreach is False
    # Explicit opt-in, not suppressed → consent on.
    assert by_email["grace@example.com"].consent_outreach is True
    # Exactly one Ada row (dedup, no duplicate person).
    assert sum(1 for p in rows if (p.email or "").lower() == "ada@example.com") == 1


# ── §9.2 convert: forward link, no duplicate person, idempotent ───────────────


async def test_convert_links_forward_and_is_idempotent(db_session, mock_institution_user):
    inst = await _seed_institution(db_session, mock_institution_user)
    application = await _seed_application(db_session, inst)
    svc = RecruitmentService(db_session)

    prospect = await svc.create_prospect(
        inst.id, CreateProspectRequest(name="Linus", email="linus@example.com", stage="engaged")
    )
    converted = await svc.convert_prospect(
        inst.id, prospect.id, ConvertProspectRequest(application_id=application.id)
    )
    assert converted.stage == "applicant"
    assert converted.converted_application_id == application.id

    # Idempotent: convert again keeps the same link, spawns no second person.
    again = await svc.convert_prospect(
        inst.id, prospect.id, ConvertProspectRequest(application_id=application.id)
    )
    assert again.id == prospect.id
    assert again.converted_application_id == application.id
    count = await db_session.scalar(
        select(func.count()).select_from(Prospect).where(Prospect.institution_id == inst.id)
    )
    assert count == 1


# ── §9.3 fair capture: source tagging → attribution ───────────────────────────


async def test_fair_capture_creates_prospects_and_attribution(db_session, mock_institution_user):
    inst = await _seed_institution(db_session, mock_institution_user)
    svc = RecruitmentService(db_session)
    fair = await svc.create_fair(
        inst.id, CreateFairRequest(name="NACAC Boston", kind="fair", region="MA")
    )

    result = await svc.capture_leads(
        inst.id,
        fair.id,
        FairCaptureRequest(
            leads=[
                CapturedLead(name="Met One", email="one@example.com", interests=["cs"]),
                CapturedLead(name="Met Two", email="two@example.com", consent_outreach=True),
            ]
        ),
    )
    assert result["captured"] == 2

    # Prospects created and tagged with the fair source.
    prospects = (
        (await db_session.execute(select(Prospect).where(Prospect.institution_id == inst.id)))
        .scalars()
        .all()
    )
    assert len(prospects) == 2
    assert all(p.source == "fair" for p in prospects)
    assert all(p.source_detail == "NACAC Boston" for p in prospects)

    # Attribution events recorded with the fair source (Spec 28 §9).
    events = (
        (
            await db_session.execute(
                select(AttributionEvent).where(
                    AttributionEvent.institution_id == inst.id,
                    AttributionEvent.source_kind == "fair",
                    AttributionEvent.source_id == fair.id,
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(events) == 2
    assert all(e.action == "lead_captured" for e in events)


# ── §9.4 territory dashboard math ─────────────────────────────────────────────


async def test_territory_dashboard_math(db_session, mock_institution_user):
    inst = await _seed_institution(db_session, mock_institution_user)
    svc = RecruitmentService(db_session)
    t = await svc.create_territory(inst.id, CreateTerritoryRequest(name="Northeast"))
    tid = t["id"]

    # 4 prospects in the territory, 1 already an applicant → 25% conversion.
    for i in range(3):
        await svc.create_prospect(
            inst.id,
            CreateProspectRequest(name=f"P{i}", email=f"p{i}@example.com", territory_id=tid),
        )
    await svc.create_prospect(
        inst.id,
        CreateProspectRequest(
            name="Applied", email="applied@example.com", territory_id=tid, stage="applicant"
        ),
    )

    dash = await svc.territory_dashboard(inst.id)
    assert dash["total_prospects"] == 4
    assert dash["total_applicants"] == 1
    assert dash["overall_conversion_rate"] == 0.25
    row = next(r for r in dash["territories"] if r["id"] == tid)
    assert row["prospect_count"] == 4
    assert row["applicant_count"] == 1
    assert row["conversion_rate"] == 0.25
    # New territory has no owner → unassigned nudge.
    assert row["unassigned"] is True


# ── §5 AI: prioritizer ranking + manual fallback ──────────────────────────────


async def test_prioritizer_ranks_when_enabled(db_session, mock_institution_user, monkeypatch):
    inst = await _seed_institution(db_session, mock_institution_user)
    svc = RecruitmentService(db_session)
    # A cold suspect from a purchased list, and a hot inbound inquiry.
    await svc.create_prospect(
        inst.id,
        CreateProspectRequest(
            name="Cold", email="cold@example.com", stage="suspect", source="list"
        ),
    )
    await svc.create_prospect(
        inst.id,
        CreateProspectRequest(
            name="Hot",
            email="hot@example.com",
            stage="inquiry",
            source="referral",
            interests=["cs"],
            consent_outreach=True,
        ),
    )

    monkeypatch.setattr(settings, "ai_recruitment_v2_enabled", True)
    rows, score_map, prioritized, _counts = await svc.list_prospects(inst.id)
    assert prioritized is True
    assert rows[0].name == "Hot"  # ranked first by apply-likelihood
    # Scoring is read-only — computed into score_map, never written to the rows.
    hot_score = score_map[str(rows[0].id)]["apply_likelihood"]
    cold_score = score_map[str(rows[-1].id)]["apply_likelihood"]
    assert hot_score >= cold_score
    assert all(p.apply_likelihood is None for p in rows)  # never persisted

    # Flag off → manual (recency) fallback, no scoring.
    monkeypatch.setattr(settings, "ai_recruitment_v2_enabled", False)
    rows2, score_map2, prioritized2, _ = await svc.list_prospects(inst.id)
    assert prioritized2 is False
    assert score_map2 == {}


async def test_territory_optimizer_falls_back_to_deterministic(
    db_session, mock_institution_user, monkeypatch
):
    inst = await _seed_institution(db_session, mock_institution_user)
    svc = RecruitmentService(db_session)
    await svc.create_fair(
        inst.id,
        CreateFairRequest(name="Lincoln HS", kind="high_school", region="MA", prior_year_yield=18),
    )
    t = await svc.create_territory(inst.id, CreateTerritoryRequest(name="MA"))

    # AI off → deterministic suggestions, non-empty, ai_generated False.
    monkeypatch.setattr(settings, "ai_recruitment_v2_enabled", False)
    out = await svc.optimize_territory(inst.id, t["id"])
    assert out["ai_generated"] is False
    assert len(out["suggestions"]) >= 1
    # The unassigned territory should be nudged to assign an owner.
    assert any(s["kind"] == "assign_owner" for s in out["suggestions"])


# ── §3 prospect → segment (consent-gated) ─────────────────────────────────────


async def test_prospects_to_segment_consent_gated(db_session, mock_institution_user):
    inst = await _seed_institution(db_session, mock_institution_user)
    svc = RecruitmentService(db_session)
    consented = await svc.create_prospect(
        inst.id,
        CreateProspectRequest(name="OptIn", email="optin@example.com", consent_outreach=True),
    )
    no_consent = await svc.create_prospect(
        inst.id, CreateProspectRequest(name="NoConsent", email="noconsent@example.com")
    )
    no_email = await svc.create_prospect(inst.id, CreateProspectRequest(name="NoEmail"))

    out = await svc.prospects_to_segment(
        inst.id,
        mock_institution_user.id,
        ProspectToSegmentRequest(
            prospect_ids=[consented.id, no_consent.id, no_email.id], list_name="Warm leads"
        ),
    )
    assert out["added"] == 1
    assert out["skipped_no_consent"] == 1
    assert out["skipped_no_email"] == 1
    contacts = (
        (
            await db_session.execute(
                select(UploadedContact).where(UploadedContact.list_id == out["list_id"])
            )
        )
        .scalars()
        .all()
    )
    assert {c.email for c in contacts} == {"optin@example.com"}


# ── §2.2/§6 trip over-budget + conflict flags ─────────────────────────────────


async def test_trip_over_budget_and_conflict_flags(db_session, mock_institution_user):
    inst = await _seed_institution(db_session, mock_institution_user)
    svc = RecruitmentService(db_session)
    recruiter = mock_institution_user.id  # a real, persisted user (FK target)
    await svc.create_trip(
        inst.id,
        CreateTripRequest(
            name="Trip A",
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 5),
            recruiter_user_id=recruiter,
            budget=1000,
            spend=1500,  # over budget
        ),
    )
    await svc.create_trip(
        inst.id,
        CreateTripRequest(
            name="Trip B",
            start_date=date(2026, 9, 4),
            end_date=date(2026, 9, 8),  # overlaps A
            recruiter_user_id=recruiter,
        ),
    )
    trips = await svc.list_trips(inst.id)
    trip_a = next(t for t in trips if t.name == "Trip A")
    trip_b = next(t for t in trips if t.name == "Trip B")
    ob_a, cf_a = svc.trip_flags(trip_a, trips)
    _ob_b, cf_b = svc.trip_flags(trip_b, trips)
    assert ob_a is True  # spend > budget
    assert cf_a is True and cf_b is True  # same recruiter, overlapping dates


# ── API smoke ─────────────────────────────────────────────────────────────────


async def test_api_summary_and_prospect_crud(institution_client, db_session, mock_institution_user):
    # institution_client persisted the user; create its Institution.
    inst = Institution(
        admin_user_id=mock_institution_user.id, name="Bar U", type="university", country="US"
    )
    db_session.add(inst)
    await db_session.flush()

    # Empty state.
    r = await institution_client.get("/api/v1/institutions/me/recruitment/summary")
    assert r.status_code == 200
    assert r.json()["is_empty"] is True

    # Create a prospect via the API.
    r = await institution_client.post(
        "/api/v1/institutions/me/recruitment/prospects",
        json={"name": "Web Lead", "email": "web@example.com", "source": "web", "interests": ["cs"]},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    assert r.json()["consent_outreach"] is False  # opt-in only

    # List shows it.
    r = await institution_client.get("/api/v1/institutions/me/recruitment/prospects")
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["id"] == pid
