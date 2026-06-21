from __future__ import annotations

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.application import Application
from unipaith.models.institution import Institution, Program
from unipaith.models.my_space import MySpaceTaskState
from unipaith.models.student import RecommendationRequest, StudentProfile
from unipaith.models.user import User
from unipaith.services.application_service import ApplicationService

BASE = "/api/v1/students/me/my-space"


async def _seed_student(
    db: AsyncSession,
    user: User,
    institution_user: User | None = None,
):
    profile = StudentProfile(user_id=user.id, first_name="Ada", last_name="Lovelace")
    db.add(profile)
    program = None
    app = None
    if institution_user is not None:
        db.add(institution_user)
        inst = Institution(
            admin_user_id=institution_user.id,
            name="Example University",
            type="university",
            country="United States",
        )
        db.add(inst)
        await db.flush()
        program = Program(
            institution_id=inst.id,
            program_name="MS Computer Science",
            degree_type="MS",
            application_deadline=(datetime.now(UTC) + timedelta(days=7)).date(),
        )
        db.add(program)
        await db.flush()
        app = Application(
            student_id=profile.id,
            program_id=program.id,
            status="draft",
            completeness_status="incomplete",
            missing_items={"items": ["Transcript", "Statement of purpose"]},
            readiness_pct=55,
        )
        db.add(app)
    await db.flush()
    return profile, program, app


@pytest.mark.asyncio
async def test_my_space_overview_composes_release_ready_tasks(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    mock_institution_user: User,
):
    profile, _program, app = await _seed_student(
        db_session,
        mock_student_user,
        mock_institution_user,
    )
    db_session.add(
        RecommendationRequest(
            student_id=profile.id,
            recommender_name="Prof. Lee",
            status="requested",
            due_date=(datetime.now(UTC) + timedelta(days=1)).date(),
        )
    )
    await db_session.flush()

    resp = await student_client.get(f"{BASE}/overview")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["student"]["first_name"] == "Ada"
    assert data["generated_at"]
    assert {r["key"] for r in data["readiness"]} >= {
        "profile",
        "match",
        "apply",
        "major_evidence",
    }
    assert {m["key"]: m["value"] for m in data["pipeline"]}["drafts"] == 1

    tasks = {t["key"]: t for t in data["tasks"]}
    app_task = tasks[f"application:{app.id}:missing"]
    assert app_task["owner"] == "student"
    assert app_task["missing_field"] == "Transcript"
    assert app_task["cta_route"] == f"/s/applications/{app.id}"
    assert app_task["provenance"][0]["source"] == "applications"

    rec_task = next(t for t in data["tasks"] if t["key"].startswith("recommender:"))
    assert rec_task["owner"] == "recommender"
    assert rec_task["urgency"] == "focus_now"
    assert rec_task["blocker"] == "Recommendation due soon"
    due_soon_copy = "Letter is due soon. Nudge the recommender or confirm a backup."
    assert rec_task["description"] == due_soon_copy
    waiting = next(i for i in data["waiting_on"] if i["key"].startswith("recommender:"))
    assert waiting["status"] == "due_soon"
    assert waiting["description"] == due_soon_copy
    strategy_task = tasks["strategy:create"]
    strategy_route = urlsplit(strategy_task["cta_route"])
    strategy_params = parse_qs(strategy_route.query)
    assert strategy_route.path == "/s"
    assert strategy_params["intent"] == ["strategy"]
    assert strategy_params["source_task"] == ["strategy:create"]
    assert strategy_params["return_to"] == ["/s/space"]
    assert strategy_params["artifact_destination"] == ["strategy_draft"]
    assert data["import_status"]["route"] == "/s/import"
    assert all(t["provenance"] for t in data["tasks"])


@pytest.mark.asyncio
async def test_my_space_task_patch_persists_only_presentation_state(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
):
    profile, _program, _app = await _seed_student(db_session, mock_student_user)
    snoozed_until = (datetime.now(UTC) + timedelta(days=5)).isoformat()

    resp = await student_client.patch(
        f"{BASE}/tasks/strategy:create",
        json={"dismissed": True, "snoozed_until": snoozed_until},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["task_key"] == "strategy:create"
    assert data["dismissed"] is True
    state = await db_session.scalar(
        select(MySpaceTaskState).where(
            MySpaceTaskState.student_id == profile.id,
            MySpaceTaskState.task_key == "strategy:create",
        )
    )
    assert state is not None
    assert state.dismissed is True
    assert state.snoozed_until is not None

    restored = await student_client.patch(
        f"{BASE}/tasks/strategy:create",
        json={"dismissed": False, "snoozed_until": None},
    )

    assert restored.status_code == 200, restored.text
    restored_data = restored.json()
    assert restored_data["dismissed"] is False
    assert restored_data["snoozed_until"] is None
    await db_session.refresh(state)
    assert state.dismissed is False
    assert state.snoozed_until is None

    overview = await student_client.get(f"{BASE}/overview")
    assert overview.status_code == 200, overview.text
    strategy_task = next(t for t in overview.json()["tasks"] if t["key"] == "strategy:create")
    assert strategy_task["active"] is True


@pytest.mark.asyncio
async def test_my_space_overview_partial_dependency_failure_returns_access_issue(
    student_client: AsyncClient,
    db_session: AsyncSession,
    mock_student_user: User,
    monkeypatch: pytest.MonkeyPatch,
):
    await _seed_student(db_session, mock_student_user)

    async def fail_apps(self, student_id):  # noqa: ANN001, ANN202
        raise RuntimeError("applications service unavailable")

    monkeypatch.setattr(ApplicationService, "list_student_applications", fail_apps)

    resp = await student_client.get(f"{BASE}/overview")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["pipeline"][1]["key"] == "drafts"
    assert data["access_issues"][0]["source"] == "partial_failure"
    assert "applications" in data["access_issues"][0]["label"]
