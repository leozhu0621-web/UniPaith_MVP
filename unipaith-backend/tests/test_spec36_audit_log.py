"""Spec 36 · Audit Log — append-only enforcement, per-category trigger points,
filtering / pagination, CSV export, single-event detail, tenant isolation, and
the student-facing access-log subset.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.audit import AUDIT_APPEND_ONLY_INSTALL_SQL, AdmissionsAuditLog
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.services.audit_service import (
    AUDIT_CATEGORIES,
    AuditService,
    infer_category,
)

API = "/api/v1"


# ── helpers ──────────────────────────────────────────────────────────────────


async def _institution(db: AsyncSession, admin: User) -> Institution:
    inst = Institution(
        admin_user_id=admin.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.flush()
    return inst


async def _other_institution(db: AsyncSession) -> Institution:
    u = User(
        id=uuid.uuid4(),
        email=f"admin-{uuid.uuid4().hex[:8]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("institution_admin"),
        is_active=True,
    )
    db.add(u)
    inst = Institution(
        admin_user_id=u.id, name="Other U", type="university", country="United States"
    )
    db.add(inst)
    await db.flush()
    return inst


async def _student_profile(db: AsyncSession, user: User) -> StudentProfile:
    # Persist the user first (no-op if a fixture already did). Tests that don't
    # use the student_client fixture rely on this for the FK.
    db.add(user)
    await db.flush()
    p = StudentProfile(user_id=user.id, first_name="Sam", last_name="Lee")
    db.add(p)
    await db.flush()
    return p


# ── §11 append-only ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_append_only_enforced(db_session: AsyncSession):
    """No UPDATE or DELETE on admissions_audit_log (Spec 36 §11)."""
    for stmt in AUDIT_APPEND_ONLY_INSTALL_SQL:
        await db_session.execute(text(stmt))

    entry = await AuditService(db_session).log(
        institution_id=None,
        actor_user_id=None,
        action="data_export",
        category="data_export",
        entity_type="consent",
        entity_id="profile_json",
    )
    await db_session.flush()

    with pytest.raises(Exception):  # noqa: B017 — any DB error is a pass
        async with db_session.begin_nested():
            await db_session.execute(
                text("UPDATE admissions_audit_log SET action='x' WHERE id=:i"),
                {"i": str(entry.id)},
            )

    with pytest.raises(Exception):  # noqa: B017
        async with db_session.begin_nested():
            await db_session.execute(
                text("DELETE FROM admissions_audit_log WHERE id=:i"), {"i": str(entry.id)}
            )

    # INSERT still works (append is allowed).
    await AuditService(db_session).log(
        institution_id=None,
        actor_user_id=None,
        action="data_export",
        entity_type="consent",
        entity_id="again",
    )
    await db_session.flush()


# ── §2 taxonomy + every category writes a row ─────────────────────────────────


def test_infer_category_mapping():
    assert infer_category("status_change") == "status_change"
    assert infer_category("submitted") == "status_change"
    assert infer_category("decision_release") == "decision_release"
    assert infer_category("batch_assign_reviewers") == "batch_action"
    assert infer_category("integrity_signal_resolved") == "integrity_resolution"
    assert infer_category("consent_change") == "consent_change"
    assert infer_category("data_export") == "data_export"
    assert infer_category("account_deletion_requested") == "data_deletion"
    assert infer_category("fairness_signal_override") == "fairness_signal_override"
    assert infer_category("ai_artifact_accepted") == "ai_generated"
    assert infer_category("dataset_deleted") == "document_replaced"
    assert infer_category("checklist_completed") == "checklist_change"
    assert infer_category("something_unmapped") == "other"


@pytest.mark.asyncio
async def test_every_category_writes_a_row(db_session: AsyncSession):
    """Each §2 category can be recorded (substrate supports the full taxonomy)."""
    audit = AuditService(db_session)
    cats = list(AUDIT_CATEGORIES) + ["batch_action"]
    for cat in cats:
        await audit.log(
            institution_id=None,
            actor_user_id=None,
            action=f"{cat}_demo",
            category=cat,
            entity_type="application",
            entity_id=str(uuid.uuid4()),
        )
    await db_session.flush()
    rows = (await db_session.execute(select(AdmissionsAuditLog))).scalars().all()
    written = {r.category for r in rows}
    for cat in cats:
        assert cat in written, f"category {cat} not recorded"


@pytest.mark.asyncio
async def test_log_infers_category_and_actor_role(db_session: AsyncSession):
    entry = await AuditService(db_session).log(
        institution_id=None,
        actor_user_id=None,
        action="batch_release_decision",
        entity_type="application",
        entity_id="x",
    )
    assert entry.category == "batch_action"
    assert entry.actor_role == "system"  # no actor → system


# ── §2 trigger points: the five gap categories ───────────────────────────────


@pytest.mark.asyncio
async def test_consent_toggle_is_audited(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _student_profile(db_session, mock_student_user)
    r = await student_client.put(f"{API}/students/me/data-rights", json={"consent_training": True})
    assert r.status_code == 200
    rows = (
        (
            await db_session.execute(
                select(AdmissionsAuditLog).where(AdmissionsAuditLog.category == "consent_change")
            )
        )
        .scalars()
        .all()
    )
    assert any(r.entity_id == "consent_training" and r.actor_role == "student" for r in rows)


@pytest.mark.asyncio
async def test_data_export_is_audited(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _student_profile(db_session, mock_student_user)
    r = await student_client.get(f"{API}/students/me/export")
    assert r.status_code == 200
    rows = (await db_session.execute(select(AdmissionsAuditLog))).scalars().all()
    assert any(x.category == "data_export" for x in rows)


@pytest.mark.asyncio
async def test_account_deletion_is_audited(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    await _student_profile(db_session, mock_student_user)
    r = await student_client.put(
        f"{API}/students/me/data-rights", json={"deletion_requested": True}
    )
    assert r.status_code == 200
    rows = (await db_session.execute(select(AdmissionsAuditLog))).scalars().all()
    assert any(x.category == "data_deletion" for x in rows)


@pytest.mark.asyncio
async def test_ai_feedback_is_audited(db_session: AsyncSession, mock_student_user: User):
    from unipaith.services.ai_feedback_service import AiFeedbackService

    p = await _student_profile(db_session, mock_student_user)
    await AiFeedbackService(db_session).submit_feedback(
        student_id=p.id, target_id=uuid.uuid4(), surface="rationale", vote="up"
    )
    await db_session.flush()
    rows = (await db_session.execute(select(AdmissionsAuditLog))).scalars().all()
    hit = [x for x in rows if x.category == "ai_generated"]
    assert hit and hit[0].action == "ai_artifact_accepted"


@pytest.mark.asyncio
async def test_fairness_override_is_audited_and_requires_reason(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    await _institution(db_session, mock_institution_user)
    # reason required
    bad = await institution_client.post(
        f"{API}/institutions/me/intelligence/fairness/override",
        json={"signal_key": "admit_rate_gender", "action": "override"},
    )
    assert bad.status_code == 422

    ok = await institution_client.post(
        f"{API}/institutions/me/intelligence/fairness/override",
        json={
            "signal_key": "admit_rate_gender",
            "action": "override",
            "reason": "Reviewed; within statistical tolerance for this cycle.",
        },
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["category"] == "fairness_signal_override"
    assert body["reason"].startswith("Reviewed")


# ── §4/§5 institution endpoints: filters, isolation, detail, pagination, CSV ──


async def _seed_inst_rows(db: AsyncSession, inst: Institution, actor_id, n_status=3):
    audit = AuditService(db)
    for _ in range(n_status):
        await audit.log(
            institution_id=inst.id,
            actor_user_id=actor_id,
            action="status_change",
            entity_type="application",
            entity_id=str(uuid.uuid4()),
            old_value={"status": "submitted"},
            new_value={"status": "under_review"},
        )
    await audit.log(
        institution_id=inst.id,
        actor_user_id=actor_id,
        action="waiver_override",
        category="waiver_override",
        entity_type="application",
        entity_id="appX",
        reason="Test-optional waiver granted.",
    )
    await db.flush()


@pytest.mark.asyncio
async def test_list_filters_and_tenant_isolation(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    other = await _other_institution(db_session)
    await _seed_inst_rows(db_session, inst, mock_institution_user.id)
    # rows for another institution must never leak
    await _seed_inst_rows(db_session, other, other.admin_user_id, n_status=2)

    # unfiltered → only this institution's rows (3 status + 1 waiver = 4)
    r = await institution_client.get(f"{API}/institutions/me/audit-log")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 4
    assert all(item["institution_id"] == str(inst.id) for item in data["items"])

    # filter by category
    r2 = await institution_client.get(
        f"{API}/institutions/me/audit-log", params={"category": "status_change"}
    )
    assert r2.json()["total"] == 3

    # filter by entity
    r3 = await institution_client.get(
        f"{API}/institutions/me/audit-log", params={"category": "waiver_override"}
    )
    assert r3.json()["total"] == 1
    assert r3.json()["items"][0]["reason"] == "Test-optional waiver granted."


@pytest.mark.asyncio
async def test_event_detail_and_cross_tenant_404(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    other = await _other_institution(db_session)
    entry = await AuditService(db_session).log(
        institution_id=inst.id,
        actor_user_id=mock_institution_user.id,
        action="decision_release",
        entity_type="application",
        entity_id="app1",
        old_value={"decision": None},
        new_value={"decision": "admitted"},
    )
    foreign = await AuditService(db_session).log(
        institution_id=other.id,
        actor_user_id=other.admin_user_id,
        action="decision_release",
        entity_type="application",
        entity_id="appZ",
    )
    await db_session.flush()

    r = await institution_client.get(f"{API}/institutions/me/audit-log/{entry.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["new_value"] == {"decision": "admitted"}
    assert body["old_value"] == {"decision": None}

    # other institution's event is invisible
    r404 = await institution_client.get(f"{API}/institutions/me/audit-log/{foreign.id}")
    assert r404.status_code == 404


@pytest.mark.asyncio
async def test_pagination(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    audit = AuditService(db_session)
    for _ in range(60):
        await audit.log(
            institution_id=inst.id,
            actor_user_id=mock_institution_user.id,
            action="status_change",
            entity_type="application",
            entity_id=str(uuid.uuid4()),
        )
    await db_session.flush()

    p0 = (
        await institution_client.get(
            f"{API}/institutions/me/audit-log", params={"limit": 50, "offset": 0}
        )
    ).json()
    p1 = (
        await institution_client.get(
            f"{API}/institutions/me/audit-log", params={"limit": 50, "offset": 50}
        )
    ).json()
    assert p0["total"] == 60
    assert len(p0["items"]) == 50
    assert len(p1["items"]) == 10
    ids0 = {i["id"] for i in p0["items"]}
    ids1 = {i["id"] for i in p1["items"]}
    assert not (ids0 & ids1)  # no overlap across pages


@pytest.mark.asyncio
async def test_csv_export(
    institution_client: AsyncClient, db_session: AsyncSession, mock_institution_user: User
):
    inst = await _institution(db_session, mock_institution_user)
    await _seed_inst_rows(db_session, inst, mock_institution_user.id)
    r = await institution_client.get(f"{API}/institutions/me/audit-log", params={"format": "csv"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    text_body = r.text
    assert "occurred_at,category,action" in text_body.splitlines()[0]
    assert "status_change" in text_body


# ── §5 student access-log subset ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_student_access_log_includes_institution_access(
    student_client: AsyncClient, db_session: AsyncSession, mock_student_user: User
):
    profile = await _student_profile(db_session, mock_student_user)
    inst = await _other_institution(db_session)
    program = Program(
        institution_id=inst.id, program_name="CS", degree_type="masters", is_published=True
    )
    db_session.add(program)
    await db_session.flush()
    app = Application(student_id=profile.id, program_id=program.id, status="submitted")
    db_session.add(app)
    await db_session.flush()

    # institution releases a decision on this student's application
    await AuditService(db_session).log(
        institution_id=inst.id,
        actor_user_id=inst.admin_user_id,
        action="decision_release",
        entity_type="application",
        entity_id=str(app.id),
        application_id=app.id,
        new_value={"decision": "admitted"},
    )
    await db_session.flush()

    r = await student_client.get(f"{API}/students/me/access-log")
    assert r.status_code == 200
    entries = r.json()
    assert any("decision" in (e["action"] or "").lower() for e in entries)
    assert any(e["actor"] == "Other U" for e in entries)
