"""Spec 28 — Attribution & Funnel Analytics acceptance tests (§13).

1. Funnel computes correctly per fixture.
2. Filters apply consistently (program / time / segment).
3. Top-sources sort by clicks vs apply_started.
4. Drop-off alert fires above threshold.
5. Insufficient-data + filtered-to-zero states.
6. Backfill derives from the domain tables and is idempotent.
7. CSV export shape.
8. Endpoint smoke (institution-scoped).
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.attribution import AttributionEvent
from unipaith.models.institution import Institution, Program
from unipaith.models.student import StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.schemas.analytics import AppliedFilters
from unipaith.services.attribution_service import AttributionService


async def _institution(db: AsyncSession, user: User | None = None) -> Institution:
    if user is None:
        user = User(
            id=uuid.uuid4(),
            email=f"inst-{uuid.uuid4().hex[:6]}@example.com",
            cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
            role=UserRole("institution_admin"),
            is_active=True,
        )
        db.add(user)
        await db.flush()
    inst = Institution(
        admin_user_id=user.id, name="Test University", type="university", country="United States"
    )
    db.add(inst)
    await db.flush()
    return inst


async def _program(db: AsyncSession, inst: Institution, name: str = "BSc CS") -> Program:
    prog = Program(institution_id=inst.id, program_name=name, degree_type="bachelor")
    db.add(prog)
    await db.flush()
    return prog


async def _student(db: AsyncSession) -> StudentProfile:
    user = User(
        id=uuid.uuid4(),
        email=f"stu-{uuid.uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid.uuid4().hex[:8]}",
        role=UserRole("student"),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    sp = StudentProfile(user_id=user.id)
    db.add(sp)
    await db.flush()
    return sp


async def _seed(
    db: AsyncSession,
    inst_id,
    action: str,
    n: int,
    *,
    source_kind: str = "program_page",
    source_id=None,
    program_id=None,
    student_id=None,
    occurred_at=None,
    decision=None,
):
    for _ in range(n):
        db.add(
            AttributionEvent(
                institution_id=inst_id,
                source_kind=source_kind,
                source_id=source_id,
                action=action,
                program_id=program_id,
                student_id=student_id,
                occurred_at=occurred_at or datetime.now(UTC),
                meta={"decision": decision} if decision else None,
            )
        )
    await db.flush()


def _stage(report, key: str):
    return next(s for s in report.stages if s.stage == key)


# ── §13.1 funnel math + §13.4 drop-off threshold ─────────────────────────────


@pytest.mark.asyncio
async def test_funnel_computes_and_drop_off_fires(db_session: AsyncSession):
    inst = await _institution(db_session)
    prog = await _program(db_session, inst)
    # impressions 10 → clicks 5 (50%) → saves 4 → apps 1 (75% drop) → submitted 1 → accepted 1
    await _seed(db_session, inst.id, "impression", 10, source_id=prog.id, program_id=prog.id)
    await _seed(db_session, inst.id, "click", 5, source_id=prog.id, program_id=prog.id)
    await _seed(db_session, inst.id, "save", 4, source_id=prog.id, program_id=prog.id)
    await _seed(db_session, inst.id, "apply_started", 1, source_id=prog.id, program_id=prog.id)
    await _seed(db_session, inst.id, "submitted", 1, source_id=prog.id, program_id=prog.id)
    await _seed(
        db_session,
        inst.id,
        "decision_outcome",
        1,
        source_id=prog.id,
        program_id=prog.id,
        decision="admitted",
    )

    svc = AttributionService(db_session)
    report = await svc.get_funnel(inst.id, AppliedFilters(time_window="30d"))

    assert _stage(report, "impressions").count == 10
    assert _stage(report, "clicks").count == 5
    assert _stage(report, "saves").count == 4
    assert _stage(report, "apps_started").count == 1
    assert _stage(report, "submitted").count == 1
    assert _stage(report, "accepted").count == 1
    # conversion_from_prev
    assert _stage(report, "clicks").conversion_from_prev == pytest.approx(0.5)
    assert _stage(report, "saves").conversion_from_prev == pytest.approx(0.8)
    assert _stage(report, "apps_started").conversion_from_prev == pytest.approx(0.25)
    assert report.has_data is True

    # Drop-off: impressions→clicks (50%) and saves→apps_started (75%) both fire;
    # the biggest is saves→apps_started, matching the spec example.
    assert len(report.drop_off_alerts) >= 2
    top = report.drop_off_alerts[0]
    assert top.from_stage == "Saves"
    assert top.to_stage == "Apps started"
    assert top.drop_pct == pytest.approx(0.75)
    assert "75% drop" in top.hint


# ── §13.3 top-sources sort by clicks vs apply_started ────────────────────────


@pytest.mark.asyncio
async def test_top_sources_sort_clicks_vs_apply_started(db_session: AsyncSession):
    inst = await _institution(db_session)
    a = await _program(db_session, inst, "Program A")
    b = await _program(db_session, inst, "Program B")
    # A wins on clicks, B wins on apply_started
    await _seed(
        db_session, inst.id, "click", 5, source_kind="program_page", source_id=a.id, program_id=a.id
    )
    await _seed(
        db_session, inst.id, "click", 2, source_kind="program_page", source_id=b.id, program_id=b.id
    )
    await _seed(
        db_session,
        inst.id,
        "apply_started",
        1,
        source_kind="program_page",
        source_id=a.id,
        program_id=a.id,
    )
    await _seed(
        db_session,
        inst.id,
        "apply_started",
        3,
        source_kind="program_page",
        source_id=b.id,
        program_id=b.id,
    )

    svc = AttributionService(db_session)
    report = await svc.get_funnel(inst.id, AppliedFilters(time_window="30d"))

    assert report.top_sources_by_clicks[0].source_id == a.id
    assert report.top_sources_by_clicks[0].action_count == 5
    assert report.top_sources_by_clicks[0].label == "Program A"
    assert report.top_sources_by_apply_started[0].source_id == b.id
    assert report.top_sources_by_apply_started[0].action_count == 3
    # The two sorts genuinely differ.
    assert (
        report.top_sources_by_clicks[0].source_id
        != report.top_sources_by_apply_started[0].source_id
    )


# ── §13.2 filters apply consistently (program + time) ────────────────────────


@pytest.mark.asyncio
async def test_program_and_time_filters(db_session: AsyncSession):
    inst = await _institution(db_session)
    a = await _program(db_session, inst, "Program A")
    b = await _program(db_session, inst, "Program B")
    await _seed(db_session, inst.id, "save", 3, source_id=a.id, program_id=a.id)
    await _seed(db_session, inst.id, "save", 7, source_id=b.id, program_id=b.id)
    # old saves outside the 30d window
    old = datetime.now(UTC) - timedelta(days=100)
    await _seed(db_session, inst.id, "save", 5, source_id=a.id, program_id=a.id, occurred_at=old)

    svc = AttributionService(db_session)
    # Program filter
    rep_a = await svc.get_funnel(inst.id, AppliedFilters(program_id=a.id, time_window="all"))
    assert _stage(rep_a, "saves").count == 8  # 3 recent + 5 old, A only
    rep_b = await svc.get_funnel(inst.id, AppliedFilters(program_id=b.id, time_window="all"))
    assert _stage(rep_b, "saves").count == 7
    # Time filter (30d excludes the 5 old A-saves)
    rep_30 = await svc.get_funnel(inst.id, AppliedFilters(time_window="30d"))
    assert _stage(rep_30, "saves").count == 10  # 3 + 7 recent
    rep_all = await svc.get_funnel(inst.id, AppliedFilters(time_window="all"))
    assert _stage(rep_all, "saves").count == 15  # +5 old


# ── §13.5 filtered-to-zero (segment resolves to empty) ───────────────────────


@pytest.mark.asyncio
async def test_segment_filter_to_zero(db_session: AsyncSession):
    inst = await _institution(db_session)
    prog = await _program(db_session, inst)
    await _seed(db_session, inst.id, "save", 5, source_id=prog.id, program_id=prog.id)

    svc = AttributionService(db_session)
    # A non-existent segment resolves to an empty student set → zero counts.
    report = await svc.get_funnel(
        inst.id, AppliedFilters(segment_id=uuid.uuid4(), time_window="all")
    )
    assert _stage(report, "saves").count == 0
    assert report.has_data is False


# ── §13.5 insufficient data (no events at all) ───────────────────────────────


@pytest.mark.asyncio
async def test_insufficient_data_state(db_session: AsyncSession):
    inst = await _institution(db_session)
    await _program(db_session, inst)
    svc = AttributionService(db_session)
    report = await svc.get_funnel(inst.id, AppliedFilters(time_window="30d"))
    assert report.total_events == 0
    assert report.has_data is False
    assert all(s.count == 0 for s in report.stages)


# ── §13.6 backfill derives from domain tables + idempotency ──────────────────


@pytest.mark.asyncio
async def test_backfill_from_applications_idempotent(db_session: AsyncSession):
    inst = await _institution(db_session)
    prog = await _program(db_session, inst)
    student = await _student(db_session)
    db_session.add(
        Application(
            student_id=student.id,
            program_id=prog.id,
            status="submitted",
            submitted_at=datetime.now(UTC),
            decision="admitted",
            decision_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
    )
    await db_session.flush()

    svc = AttributionService(db_session)
    # get_funnel triggers a backfill → the application surfaces as 3 events.
    report = await svc.get_funnel(inst.id, AppliedFilters(time_window="all"))
    assert _stage(report, "apps_started").count == 1
    assert _stage(report, "submitted").count == 1
    assert _stage(report, "accepted").count == 1

    count1 = await db_session.scalar(
        select(func.count())
        .select_from(AttributionEvent)
        .where(AttributionEvent.institution_id == inst.id)
    )
    # A second backfill must not duplicate (stable dedupe_key + ON CONFLICT).
    await svc.backfill_institution(inst.id)
    count2 = await db_session.scalar(
        select(func.count())
        .select_from(AttributionEvent)
        .where(AttributionEvent.institution_id == inst.id)
    )
    assert count1 == count2 == 3


# ── Overview KPIs: all-time window has no bogus prior comparison ──────────────


@pytest.mark.asyncio
async def test_overview_all_time_has_no_prior_comparison(db_session: AsyncSession):
    inst = await _institution(db_session)
    prog = await _program(db_session, inst)
    student = await _student(db_session)
    db_session.add(
        Application(
            student_id=student.id,
            program_id=prog.id,
            status="submitted",
            submitted_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
        )
    )
    await db_session.flush()

    svc = AttributionService(db_session)
    rep = await svc.get_overview(inst.id, AppliedFilters(time_window="all"))
    assert rep.total_applications.value == 1
    # All-time has no prior window → no comparison (not a misleading +0%).
    assert rep.total_applications.prior is None
    assert rep.total_applications.delta_pct is None

    # A bounded window still computes a comparison cohort.
    rep30 = await svc.get_overview(inst.id, AppliedFilters(time_window="30d"))
    assert rep30.total_applications.value == 1


# ── §13.7 CSV export shape ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_csv_export_funnel(db_session: AsyncSession):
    inst = await _institution(db_session)
    prog = await _program(db_session, inst)
    await _seed(db_session, inst.id, "impression", 4, source_id=prog.id, program_id=prog.id)
    await _seed(db_session, inst.id, "save", 2, source_id=prog.id, program_id=prog.id)

    svc = AttributionService(db_session)
    csv_str = await svc.export_csv(inst.id, "funnel", AppliedFilters(time_window="all"))
    lines = csv_str.strip().splitlines()
    assert lines[0] == "stage,count,conversion_from_prev"
    assert any(row.startswith("Impressions,4") for row in lines)
    assert any(row.startswith("Saves,2") for row in lines)


# ── §13.8 endpoint smoke ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analytics_endpoints_smoke(
    institution_client: AsyncClient,
    db_session: AsyncSession,
    mock_institution_user: User,
):
    inst = await _institution(db_session, mock_institution_user)
    prog = await _program(db_session, inst)
    await _seed(db_session, inst.id, "click", 3, source_id=prog.id, program_id=prog.id)
    await db_session.commit()

    r = await institution_client.get("/api/v1/institutions/me/analytics/funnel?time_window=all")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "stages" in body and any(s["stage"] == "clicks" for s in body["stages"])
    assert body["has_data"] is True

    r2 = await institution_client.get("/api/v1/institutions/me/analytics/overview")
    assert r2.status_code == 200, r2.text
    assert "total_applications" in r2.json()

    r3 = await institution_client.get("/api/v1/institutions/me/analytics/attribution")
    assert r3.status_code == 200, r3.text

    r4 = await institution_client.get(
        "/api/v1/institutions/me/analytics/export?kind=funnel&time_window=all"
    )
    assert r4.status_code == 200
    assert "text/csv" in r4.headers["content-type"]
