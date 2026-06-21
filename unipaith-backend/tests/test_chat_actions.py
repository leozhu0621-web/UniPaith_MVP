"""Chat template action dispatch — the My-Space link on artifacts.

Covers POST /students/me/chat/templates/action/{action_key}, focusing on the
`link` field added by the 2026-06-20 My-Space chat-strategy lineup (Task 3):
a real, ready artifact carries a deep link back to its My-Space surface; a
pending or not-real action leaves `link` null.
"""

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.models.goals import StudentGoal

BASE = "/api/v1/students/me/chat"


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
async def test_non_real_action_is_pending_with_no_link(
    student_client, db_session, mock_student_user
):
    """A catalog action without a real service (find_events) → pending, link=None."""
    await ensure_profile(db_session, mock_student_user)
    r = await student_client.post(f"{BASE}/templates/action/find_events")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["link"] is None
