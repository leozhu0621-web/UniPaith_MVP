"""Host-side custom tools for the Uni managed agent."""

import pytest

from tests._uni_helpers import ensure_profile
from unipaith.services.uni_tools import (
    dispatch_tool,
    tool_get_matches,
    tool_save_signals,
    tool_search_programs,
)


@pytest.mark.asyncio
async def test_save_signals_writes_goal_and_returns_completion(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    tool_input = {
        "goals": [
            {
                "category": "academic",
                "specific": "Earn a funded CS PhD",
                "measurable": "Admitted with full funding",
                "achievable": "Strong research background",
                "relevant": "Career in ML research",
                "time_bound": "2027",
                "completeness": 1.0,
                "evidence": "I want a fully funded CS PhD by 2027.",
            }
        ],
        "confidence": {"goals": 0.9},
    }
    out = await tool_save_signals(db_session, mock_student_user.id, tool_input)
    assert "completion" in out and set(out["completion"]) >= {"profile", "goals", "needs"}
    assert "handoff_ready" in out
    assert out["written"]["goals_written"] >= 0


@pytest.mark.asyncio
async def test_search_programs_returns_compact_facts(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    out = await tool_search_programs(
        db_session, mock_student_user.id, {"query": "computer science"}
    )
    assert "programs" in out and isinstance(out["programs"], list)
    assert "total" in out
    if out["programs"]:
        p = out["programs"][0]
        assert {"program_name", "institution_name", "degree_type"} <= set(p)


@pytest.mark.asyncio
async def test_get_matches_gates_on_handoff(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    out = await tool_get_matches(db_session, mock_student_user.id, {})
    # Fresh student is not handoff-ready → tool reports not-ready + what's missing.
    assert out["ready"] is False
    assert "completion" in out


@pytest.mark.asyncio
async def test_dispatch_unknown_tool_returns_error(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    out = await dispatch_tool(db_session, mock_student_user.id, "nope", {}, session_id=None)
    assert out["error"]


@pytest.mark.asyncio
async def test_dispatch_get_profile_snapshot(db_session, mock_student_user):
    await ensure_profile(db_session, mock_student_user)
    out = await dispatch_tool(
        db_session, mock_student_user.id, "get_profile_snapshot", {}, session_id=None
    )
    assert "completion" in out  # snapshot shape
