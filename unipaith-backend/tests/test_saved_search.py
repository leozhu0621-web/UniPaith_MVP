"""Spec 56 §6 — Saved searches + the alert loop.

HTTP tests cover the CRUD surface (create / list / update / delete + the
per-user cap + ownership isolation). Service tests cover the alert loop's logic
(new-match emission, first-run baseline seeding, the consent gate, and the
per-user-per-day cap) with ``_execute`` monkeypatched so we test the alert
decision-making, not the FTS engine (which is covered elsewhere).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.config import settings
from unipaith.models.saved_search import SavedSearch
from unipaith.models.student import StudentDataConsent, StudentProfile
from unipaith.models.user import User, UserRole
from unipaith.models.workflow import Notification
from unipaith.services.saved_search_service import (
    ALERT_NOTIFICATION_TYPE,
    SavedSearchService,
)

# asyncio_mode = "auto" (pyproject) runs these async tests without an explicit mark.

BASE = "/api/v1/students/me/saved-searches"


def _body(name: str = "CS masters", *, alert: bool = False) -> dict:
    return {
        "name": name,
        "entity_type": "program",
        "query": {"query": "computer science", "chips": [], "filters": {}, "sort": "relevance"},
        "alert_enabled": alert,
    }


# ── HTTP CRUD ────────────────────────────────────────────────────────────────
async def test_create_and_list(student_client: AsyncClient):
    r = await student_client.post(BASE, json=_body())
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["name"] == "CS masters"
    assert created["entity_type"] == "program"
    assert created["alert_enabled"] is False
    assert created["query"]["query"] == "computer science"

    r2 = await student_client.get(BASE)
    assert r2.status_code == 200
    rows = r2.json()
    assert len(rows) == 1
    assert rows[0]["id"] == created["id"]


async def test_update_rename_and_toggle_alert(student_client: AsyncClient):
    created = (await student_client.post(BASE, json=_body())).json()
    r = await student_client.patch(
        f"{BASE}/{created['id']}", json={"name": "Renamed", "alert_enabled": True}
    )
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["name"] == "Renamed"
    assert updated["alert_enabled"] is True


async def test_delete(student_client: AsyncClient):
    created = (await student_client.post(BASE, json=_body())).json()
    r = await student_client.delete(f"{BASE}/{created['id']}")
    assert r.status_code == 204
    rows = (await student_client.get(BASE)).json()
    assert rows == []


async def test_max_per_user_cap(student_client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "saved_search_max_per_user", 2)
    assert (await student_client.post(BASE, json=_body("one"))).status_code == 201
    assert (await student_client.post(BASE, json=_body("two"))).status_code == 201
    over = await student_client.post(BASE, json=_body("three"))
    assert over.status_code == 400
    assert "up to 2" in over.json()["detail"]


async def test_missing_search_404(student_client: AsyncClient):
    r = await student_client.patch(f"{BASE}/{uuid4()}", json={"alert_enabled": True})
    assert r.status_code == 404


# ── Service: ownership isolation ─────────────────────────────────────────────
async def _student(db: AsyncSession, *, consent_outreach: bool | None = None) -> StudentProfile:
    user = User(
        id=uuid4(),
        email=f"s-{uuid4().hex[:6]}@example.com",
        cognito_sub=f"sub-{uuid4().hex[:8]}",
        role=UserRole.student,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.flush()
    if consent_outreach is not None:
        db.add(StudentDataConsent(student_id=profile.id, consent_outreach=consent_outreach))
        await db.flush()
    return profile


async def test_ownership_isolation(db_session: AsyncSession):
    a = await _student(db_session)
    b = await _student(db_session)
    svc = SavedSearchService(db_session)

    from unipaith.schemas.saved_search import SavedSearchCreate

    owned = await svc.create(a.user_id, SavedSearchCreate(name="A's search"))
    # B cannot see or fetch A's saved search.
    assert await svc.list(b.user_id) == []
    from unipaith.core.exceptions import NotFoundException

    with pytest.raises(NotFoundException):
        await svc.get(b.user_id, owned.id)


# ── Service: alert loop ──────────────────────────────────────────────────────
def _patch_execute(monkeypatch, total: int):
    async def fake_execute(self, saved_search, *, page_size, student_profile_id=None):
        return total, []

    monkeypatch.setattr(SavedSearchService, "_execute", fake_execute)


async def _alerts_for(db: AsyncSession, user_id) -> int:
    return await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.notification_type == ALERT_NOTIFICATION_TYPE,
        )
    )


async def test_alert_emitted_on_new_matches(db_session: AsyncSession, monkeypatch):
    profile = await _student(db_session)
    db_session.add(
        SavedSearch(user_id=profile.user_id, name="watch", alert_enabled=True, last_match_count=0)
    )
    await db_session.flush()
    _patch_execute(monkeypatch, total=3)

    emitted = await SavedSearchService(db_session).run_alerts()
    assert emitted == 1
    assert await _alerts_for(db_session, profile.user_id) == 1

    row = (await db_session.execute(select(SavedSearch))).scalar_one()
    assert row.last_match_count == 3
    assert row.last_alerted_at is not None


async def test_first_run_seeds_baseline_without_alert(db_session: AsyncSession, monkeypatch):
    profile = await _student(db_session)
    db_session.add(
        SavedSearch(
            user_id=profile.user_id, name="fresh", alert_enabled=True, last_match_count=None
        )
    )
    await db_session.flush()
    _patch_execute(monkeypatch, total=5)

    emitted = await SavedSearchService(db_session).run_alerts()
    assert emitted == 0  # first run only seeds the baseline
    assert await _alerts_for(db_session, profile.user_id) == 0
    row = (await db_session.execute(select(SavedSearch))).scalar_one()
    assert row.last_match_count == 5


async def test_no_alert_when_count_unchanged(db_session: AsyncSession, monkeypatch):
    profile = await _student(db_session)
    db_session.add(
        SavedSearch(user_id=profile.user_id, name="same", alert_enabled=True, last_match_count=4)
    )
    await db_session.flush()
    _patch_execute(monkeypatch, total=4)

    emitted = await SavedSearchService(db_session).run_alerts()
    assert emitted == 0
    assert await _alerts_for(db_session, profile.user_id) == 0


async def test_alert_respects_outreach_consent(db_session: AsyncSession, monkeypatch):
    profile = await _student(db_session, consent_outreach=False)
    db_session.add(
        SavedSearch(user_id=profile.user_id, name="muted", alert_enabled=True, last_match_count=0)
    )
    await db_session.flush()
    _patch_execute(monkeypatch, total=9)

    emitted = await SavedSearchService(db_session).run_alerts()
    assert emitted == 0
    assert await _alerts_for(db_session, profile.user_id) == 0


async def test_alert_respects_daily_cap(db_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(settings, "saved_search_alert_cap_per_day", 1)
    profile = await _student(db_session)
    # One alert already sent today.
    db_session.add(
        Notification(
            user_id=profile.user_id,
            notification_type=ALERT_NOTIFICATION_TYPE,
            title="earlier",
            body="earlier",
            created_at=datetime.now(UTC),
        )
    )
    db_session.add(
        SavedSearch(user_id=profile.user_id, name="capped", alert_enabled=True, last_match_count=0)
    )
    await db_session.flush()
    _patch_execute(monkeypatch, total=7)

    emitted = await SavedSearchService(db_session).run_alerts()
    assert emitted == 0  # already at the daily cap
    # Still only the one pre-existing alert.
    assert await _alerts_for(db_session, profile.user_id) == 1
    # But the baseline is still refreshed so it doesn't re-fire forever.
    row = (await db_session.execute(select(SavedSearch))).scalar_one()
    assert row.last_match_count == 7


async def test_run_now_updates_baseline(db_session: AsyncSession, monkeypatch):
    profile = await _student(db_session)
    row = SavedSearch(user_id=profile.user_id, name="run", last_match_count=None)
    db_session.add(row)
    await db_session.flush()
    _patch_execute(monkeypatch, total=6)

    result = await SavedSearchService(db_session).run(row, student_profile_id=profile.id)
    assert result.count == 6
    assert row.last_match_count == 6
    assert row.last_run_at is not None
