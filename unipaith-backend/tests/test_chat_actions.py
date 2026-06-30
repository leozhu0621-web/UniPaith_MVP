"""Chat template action dispatch — the My-Space link on artifacts.

Covers POST /students/me/chat/templates/action/{action_key}, focusing on the
`link` field added by the 2026-06-20 My-Space chat-strategy lineup (Task 3):
a real, ready artifact carries a deep link back to its My-Space surface; a
pending or not-real action leaves `link` null.
"""

from datetime import UTC, datetime, timedelta

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.models.goals import StudentGoal
from unipaith.models.institution import Event, Institution

BASE = "/api/v1/students/me/chat"


async def _seed_upcoming_event(db, mock_student_user) -> Event:
    """Seed one published upcoming event so find_events returns a real list.
    Reuses the student's user id as the institution admin FK (no uniqueness
    constraint) — we only need a valid `institution_id` for the event."""
    inst = Institution(
        admin_user_id=mock_student_user.id,
        name="Test University",
        type="university",
        country="United States",
    )
    db.add(inst)
    await db.flush()
    now = datetime.now(UTC)
    event = Event(
        institution_id=inst.id,
        event_name="Grad School Info Session",
        event_type="webinar",
        location="Online",
        start_time=now + timedelta(days=5),
        end_time=now + timedelta(days=5, hours=1),
        status="upcoming",
    )
    db.add(event)
    await db.commit()
    return event


async def _seed_academic_goal(db, profile) -> None:
    """Give the profile one active academic goal so the rule-based strategy
    generator (used in AI_MOCK_MODE) succeeds instead of raising."""
    db.add(
        StudentGoal(
            student_id=profile.id,
            category="academic",
            specific="Earn a master's in data science to become an ML engineer.",
            status="active",
            source="manual",
        )
    )
    await db.commit()


@pytest.mark.asyncio
async def test_generate_strategy_ready_carries_strategy_link(
    student_client, db_session, mock_student_user
):
    """With an active academic goal the rule-based strategy is produced
    (status=ready) and the artifact links to the Strategy profile tab."""
    profile = await ensure_profile(db_session, mock_student_user)
    await _seed_academic_goal(db_session, profile)

    r = await student_client.post(f"{BASE}/templates/action/generate_strategy")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["action_key"] == "generate_strategy"
    assert body["kind"] == "strategy"
    # The rule-based generator runs in AI_MOCK_MODE → ready, with the link.
    assert body["status"] == "ready", body
    assert body["link"] == "/s/profile?tab=strategy"


@pytest.mark.asyncio
async def test_generate_strategy_pending_has_no_link(student_client, db_session, mock_student_user):
    """A bare profile (no academic goal) degrades to pending with link=None."""
    await ensure_profile(db_session, mock_student_user)

    r = await student_client.post(f"{BASE}/templates/action/generate_strategy")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["action_key"] == "generate_strategy"
    assert body["kind"] == "strategy"
    assert body["status"] == "pending", body
    assert body["link"] is None


@pytest.mark.asyncio
async def test_unknown_action_key_returns_400(student_client, db_session, mock_student_user):
    """An action key that isn't in the catalog → 400."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/templates/action/not_a_real_action")
    assert r.status_code == 400, r.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("action_key", "expected_link"),
    [
        ("generate_goal_stack", "/s/profile?tab=goals"),
        ("generate_needs_map", "/s/profile?tab=needs"),
        ("build_checklist", "/s/applications"),
        ("draft_feedback", "/s/prep?tab=workshops"),
        ("interview_practice", "/s/prep?tab=interviews"),
    ],
)
async def test_handoff_action_returns_ready_with_my_space_link(
    student_client, db_session, mock_student_user, action_key, expected_link
):
    """A catalog action without a one-shot service hands the student off to its
    My Space (or Discover) home — a real, honest link, not a dead placeholder."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/templates/action/{action_key}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ready", body
    assert body["kind"] == "handoff", body
    assert body["link"] == expected_link
    assert body["summary"]


@pytest.mark.asyncio
async def test_find_events_returns_event_list_with_items(
    student_client, db_session, mock_student_user
):
    """With a seeded upcoming event, find_events is a REAL artifact — an event
    list (not a handoff) whose item carries the real event name, plus the
    Discover events link."""
    await ensure_profile(db_session, mock_student_user)
    await _seed_upcoming_event(db_session, mock_student_user)

    r = await student_client.post(f"{BASE}/templates/action/find_events")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["action_key"] == "find_events"
    assert body["kind"] == "event_list", body
    assert body["status"] == "ready", body
    assert body["link"] == "/s/explore?tab=events"
    names = [item["name"] for item in (body["items"] or [])]
    assert "Grad School Info Session" in names, body


@pytest.mark.asyncio
async def test_find_events_empty_is_ready_with_honest_summary(
    student_client, db_session, mock_student_user
):
    """No upcoming events → still ready (never a 5xx), no items, an honest
    summary, and the same Discover events link."""
    await ensure_profile(db_session, mock_student_user)

    r = await student_client.post(f"{BASE}/templates/action/find_events")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["action_key"] == "find_events"
    assert body["kind"] == "event_list", body
    assert body["status"] == "ready", body
    assert not body["items"]
    assert body["summary"]
    assert body["link"] == "/s/explore?tab=events"
