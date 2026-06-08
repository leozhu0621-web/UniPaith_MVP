"""Uni guided-journey stage math (deterministic, no DB/LLM)."""

from __future__ import annotations

from unipaith.ai.journey import STAGES, current_stage, stage_label


def test_current_stage_is_first_incomplete() -> None:
    assert current_stage({"profile": 0.8, "goals": 0.2, "needs": 0.0}) == "goals"


def test_current_stage_none_when_all_ready() -> None:
    assert current_stage({"profile": 0.6, "goals": 0.7, "needs": 0.9}) is None


def test_current_stage_handles_missing_keys_and_none() -> None:
    assert current_stage(None) == "profile"
    assert current_stage({}) == "profile"
    assert current_stage({"profile": 0.9}) == "goals"


def test_stages_order() -> None:
    assert STAGES == ("profile", "goals", "needs")


def test_stage_label() -> None:
    assert stage_label("profile") == "About you"
    assert stage_label("goals") == "your goals"
    assert stage_label(None) == "your matches"


def _ctx(**kw):
    from unipaith.ai.orchestrator import TurnContext

    base = dict(
        track="discovery",
        layer=None,
        completion_pct=0.3,
        verdict=None,
        known_profile_summary="likes marine bio",
    )
    base.update(kw)
    return TurnContext(**base)


def test_guided_header_leads_current_stage() -> None:
    from unipaith.ai.orchestrator import Orchestrator

    header = Orchestrator._render_state_header(
        _ctx(guided=True, completion_breakdown={"profile": 0.8, "goals": 0.1, "needs": 0.0})
    )
    assert "your goals" in header  # current stage is goals
    assert "Stage coverage" in header
    assert "one stage at a time" in header


def test_guided_header_ready_for_matches_when_all_covered() -> None:
    from unipaith.ai.orchestrator import Orchestrator

    header = Orchestrator._render_state_header(
        _ctx(guided=True, completion_breakdown={"profile": 0.7, "goals": 0.7, "needs": 0.7})
    )
    assert "first look at their matches" in header


def test_unguided_header_keeps_open_discovery_fallback() -> None:
    from unipaith.ai.orchestrator import Orchestrator

    header = Orchestrator._render_state_header(
        _ctx(guided=False, completion_breakdown={"profile": 0.8, "goals": 0.1, "needs": 0.0})
    )
    assert "one open discovery conversation" in header
    assert "Stage coverage" not in header


def test_grounding_block_appended_when_present() -> None:
    from unipaith.ai.orchestrator import Orchestrator

    header = Orchestrator._render_state_header(
        _ctx(
            guided=True,
            completion_breakdown={"profile": 0.6, "goals": 0.2, "needs": 0.0},
            knowledge_summary="## From your knowledge base\n- Marine Biology BS at U Maine",
        )
    )
    assert "From your knowledge base" in header
    assert "prefer" in header.lower()


def test_no_grounding_block_when_absent() -> None:
    from unipaith.ai.orchestrator import Orchestrator

    header = Orchestrator._render_state_header(
        _ctx(guided=True, completion_breakdown={"profile": 0.6, "goals": 0.2, "needs": 0.0})
    )
    assert "From your knowledge base" not in header


def test_grounding_block_in_open_mode_too() -> None:
    from unipaith.ai.orchestrator import Orchestrator

    header = Orchestrator._render_state_header(
        _ctx(guided=False, knowledge_summary="## From your knowledge base\n- X at Y")
    )
    assert "From your knowledge base" in header
