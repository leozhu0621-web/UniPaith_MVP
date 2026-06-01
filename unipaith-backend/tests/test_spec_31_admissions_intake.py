"""Spec 31 · Admissions Intake — dashboard contract, intelligence digest,
yield-risk alerts, integrity resolve workflow, and batch-action audit logging.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import (
    Application,
    IntegritySignal,
    Interview,
)
from unipaith.models.audit import AdmissionsAuditLog
from unipaith.models.institution import Inquiry, Institution, Program, Reviewer
from unipaith.models.matching import MatchResult
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole

API = "/api/v1"


async def _student(db: AsyncSession, *, nationality: str | None = None) -> StudentProfile:
    u = User(
        id=uuid.uuid4(),
        email=f"s-{uuid.uuid4().hex[:8]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db.add(u)
    p = StudentProfile(user_id=u.id, first_name="A", last_name="B", nationality=nationality)
    db.add(p)
    await db.flush()
    return p


async def _seed(db: AsyncSession, institution_user: User) -> dict:
    """Institution + published program + reviewer."""
    db.add(institution_user)
    inst = Institution(
        admin_user_id=institution_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.flush()
    program = Program(
        institution_id=inst.id,
        program_name="CS Masters",
        degree_type="masters",
        is_published=True,
        tuition=50000,
    )
    db.add(program)
    await db.flush()
    reviewer = Reviewer(
        institution_id=inst.id,
        user_id=institution_user.id,
        name="Dr. Reviewer",
        department="CS",
    )
    db.add(reviewer)
    await db.flush()
    return {"inst": inst, "program": program, "reviewer": reviewer}


@pytest.mark.asyncio
async def test_dashboard_summary_contract(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    ctx = await _seed(db_session, mock_institution_user)
    program = ctx["program"]

    # submitted app, no reviewer assignment → needs reviewer assignment
    s1 = await _student(db_session)
    app1 = Application(student_id=s1.id, program_id=program.id, status="submitted")
    db_session.add(app1)
    # admitted app, no student response → counts toward decisions
    s2 = await _student(db_session)
    app2 = Application(
        student_id=s2.id,
        program_id=program.id,
        status="decision_made",
        decision="admitted",
        decision_at=datetime.now(UTC),
    )
    db_session.add(app2)
    await db_session.flush()

    # match results → avg_match
    db_session.add(
        MatchResult(
            student_id=s1.id, program_id=program.id, fitness_score=0.8, confidence_score=0.7
        )
    )
    db_session.add(
        MatchResult(
            student_id=s2.id, program_id=program.id, fitness_score=0.6, confidence_score=0.7
        )
    )
    # open integrity signal on app1
    db_session.add(
        IntegritySignal(
            application_id=app1.id,
            institution_id=ctx["inst"].id,
            signal_type="duplicate_submission",
            severity="high",
            title="Dup",
            description="d",
            status="open",
        )
    )
    # unconfirmed interview → interview confirmations pending
    db_session.add(
        Interview(
            application_id=app1.id,
            interviewer_id=ctx["reviewer"].id,
            interview_type="standard",
            status="proposed",
            confirmed_time=None,
        )
    )
    # a fresh inquiry → new_inquiries_24h
    db_session.add(
        Inquiry(
            institution_id=ctx["inst"].id,
            student_name="N",
            student_email="n@example.com",
            subject="Q",
            message="m",
            status="new",
        )
    )
    await db_session.commit()

    resp = await institution_client.get(f"{API}/institutions/me/dashboard")
    assert resp.status_code == 200
    data = resp.json()

    # Spec 31 §2/§8 contract fields all present.
    for key in (
        "cycle",
        "avg_match",
        "conversion_pct",
        "projected_yield_pct",
        "new_inquiries_24h",
        "unanswered_inquiries_4h",
        "integrity_signals_count",
        "priority_queue",
        "fairness",
    ):
        assert key in data, f"missing dashboard field: {key}"

    assert data["cycle"]  # a non-empty label was derived
    assert data["avg_match"] == 70  # mean of 0.8 and 0.6 → 0.70 → 70
    assert data["new_inquiries_24h"] >= 1
    assert data["integrity_signals_count"] >= 1

    cats = {item["category"]: item for item in data["priority_queue"]}
    # all three §2 categories present with deep links
    assert any("reviewer assignment" in c for c in cats)
    assert any("integrity flags" in c for c in cats)
    assert any("interview confirmation" in c for c in cats)
    for item in data["priority_queue"]:
        assert item["deep_link"].startswith("/i/admissions")
        assert item["count"] >= 1


@pytest.mark.asyncio
async def test_intelligence_digest_fallback(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    await _seed(db_session, mock_institution_user)
    await db_session.commit()
    resp = await institution_client.get(f"{API}/institutions/me/intelligence/digest")
    assert resp.status_code == 200
    data = resp.json()
    # AI_MOCK_MODE + flag off → deterministic rule-based narrator, never 5xx.
    assert isinstance(data["digest"], str) and data["digest"]
    assert data["source"] == "rule_based"
    assert "generated_at" in data
    assert isinstance(data["stats"], dict)


@pytest.mark.asyncio
async def test_yield_risk_alerts(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    ctx = await _seed(db_session, mock_institution_user)
    program = ctx["program"]
    s = await _student(db_session)
    db_session.add(
        Application(
            student_id=s.id,
            program_id=program.id,
            status="decision_made",
            decision="admitted",
            decision_at=datetime.now(UTC) - timedelta(days=12),
        )
    )
    await db_session.commit()

    resp = await institution_client.get(f"{API}/institutions/me/intelligence/yield-risks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["alerts"]) == 1
    alert = data["alerts"][0]
    for key in (
        "application_id",
        "student_id",
        "program_id",
        "risk_level",
        "competing_programs",
        "reason",
    ):
        assert key in alert
    # admitted 12 days ago, no response → high risk
    assert alert["risk_level"] == "high"


@pytest.mark.asyncio
async def test_yield_risk_ordering(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    ctx = await _seed(db_session, mock_institution_user)
    program = ctx["program"]
    # one long-waiting (high) + one fresh (low)
    s_old = await _student(db_session)
    db_session.add(
        Application(
            student_id=s_old.id,
            program_id=program.id,
            status="decision_made",
            decision="admitted",
            decision_at=datetime.now(UTC) - timedelta(days=20),
        )
    )
    s_new = await _student(db_session)
    db_session.add(
        Application(
            student_id=s_new.id,
            program_id=program.id,
            status="decision_made",
            decision="admitted",
            decision_at=datetime.now(UTC),
        )
    )
    await db_session.commit()
    resp = await institution_client.get(f"{API}/institutions/me/intelligence/yield-risks")
    alerts = resp.json()["alerts"]
    assert len(alerts) == 2
    order = {"high": 0, "medium": 1, "low": 2}
    risks = [order[a["risk_level"]] for a in alerts]
    assert risks == sorted(risks)  # most urgent first


@pytest.mark.asyncio
async def test_integrity_resolve_workflow(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    ctx = await _seed(db_session, mock_institution_user)
    program = ctx["program"]
    s = await _student(db_session)
    app = Application(student_id=s.id, program_id=program.id, status="submitted")
    db_session.add(app)
    await db_session.flush()

    for resolution in ("acceptable", "requires_clarification", "reject_application"):
        sig = IntegritySignal(
            application_id=app.id,
            institution_id=ctx["inst"].id,
            signal_type="essay_authenticity",
            severity="medium",
            title="AI patterns",
            description="d",
            status="open",
        )
        db_session.add(sig)
        await db_session.commit()

        resp = await institution_client.post(
            f"{API}/reviews/integrity-signals/{sig.id}/resolve",
            params={"resolution": resolution, "notes": "reviewed"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "resolved"
        assert body["resolution"] == resolution

        # audit-logged (spec §6)
        logs = (
            (
                await db_session.execute(
                    select(AdmissionsAuditLog).where(
                        AdmissionsAuditLog.action == "integrity_signal_resolved",
                        AdmissionsAuditLog.entity_id == str(sig.id),
                    )
                )
            )
            .scalars()
            .all()
        )
        assert len(logs) == 1
        assert logs[0].new_value["resolution"] == resolution


@pytest.mark.asyncio
async def test_integrity_resolve_rejects_invalid_resolution(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    ctx = await _seed(db_session, mock_institution_user)
    program = ctx["program"]
    s = await _student(db_session)
    app = Application(student_id=s.id, program_id=program.id, status="submitted")
    db_session.add(app)
    await db_session.flush()
    sig = IntegritySignal(
        application_id=app.id,
        institution_id=ctx["inst"].id,
        signal_type="duplicate_submission",
        severity="high",
        title="Dup",
        description="d",
        status="open",
    )
    db_session.add(sig)
    await db_session.commit()

    resp = await institution_client.post(
        f"{API}/reviews/integrity-signals/{sig.id}/resolve",
        params={"resolution": "not_a_real_outcome"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_batch_status_audit_per_item(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    ctx = await _seed(db_session, mock_institution_user)
    program = ctx["program"]
    apps = []
    for _ in range(3):
        s = await _student(db_session)
        a = Application(student_id=s.id, program_id=program.id, status="submitted")
        db_session.add(a)
        apps.append(a)
    await db_session.commit()

    ids = [str(a.id) for a in apps]
    resp = await institution_client.post(
        f"{API}/applications/batch/status",
        json={"application_ids": ids, "status": "under_review"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["success_count"] == 3

    # one audit-log entry per application (spec §5)
    logs = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(
                    AdmissionsAuditLog.action == "batch_update_status",
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(logs) == 3
    assert {str(log.application_id) for log in logs} == set(ids)


@pytest.mark.asyncio
async def test_fairness_signal_warns_on_skew(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    ctx = await _seed(db_session, mock_institution_user)
    program = ctx["program"]
    # 22 applicants, all the same nationality → 100% skew ≥ 70% threshold.
    for _ in range(22):
        s = await _student(db_session, nationality="Wakanda")
        db_session.add(Application(student_id=s.id, program_id=program.id, status="submitted"))
    await db_session.commit()

    resp = await institution_client.get(f"{API}/institutions/me/dashboard")
    fairness = resp.json()["fairness"]
    assert fairness["status"] == "warning"
    assert fairness["dimension"] == "nationality"
