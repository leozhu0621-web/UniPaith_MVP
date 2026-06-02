"""Spec 45 — AI agent catalog + public `/ai/agents` endpoint.

These tests pin the catalog as a faithful mirror of the live registry:
- every `AGENT_TIERS` agent is catalogued (no agent goes undocumented),
- no phantom agents (every catalog entry is a real, registered agent),
- tier / consent are the live registry values (catalog can't contradict),
- all spec-45 sections §2–§19 are represented,
- model ids resolve to real Claude models,
- named prompt files actually exist on disk (§21 versioning is real),
- `enabled` tracks the gating settings flag,
- the public endpoint returns the full contract shape.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from unipaith.ai.agent_registry import AGENT_TIERS, tier_for
from unipaith.ai.catalog import (
    CATALOG,
    PROMPTS_DIR,
    TIER_META,
    build_catalog,
    resolve_model,
)
from unipaith.ai.client import MODEL_PRICES
from unipaith.ai.consent import AGENT_REQUIRES
from unipaith.config import settings

_CATALOG_NAMES = {e.name for e in CATALOG}


# ── Catalog ⇆ registry fidelity ─────────────────────────────────────────


def test_catalog_covers_every_registered_agent():
    """Every agent in the tier registry must appear in the catalog so the
    transparency page never silently omits a live agent."""
    missing = set(AGENT_TIERS) - _CATALOG_NAMES
    assert not missing, f"AGENT_TIERS agents missing from the catalog: {missing}"


def test_catalog_has_no_phantom_agents():
    """Every catalog entry must be a real, tier-registered agent."""
    extra = _CATALOG_NAMES - set(AGENT_TIERS)
    assert not extra, f"Catalog lists agents not in AGENT_TIERS: {extra}"


def test_catalog_entry_names_are_unique():
    names = [e.name for e in CATALOG]
    assert len(names) == len(set(names)), "Duplicate agent name in CATALOG"


def test_catalog_tier_matches_live_registry():
    """The tier shown for an agent is resolved live — it must equal tier_for."""
    payload = build_catalog()
    for a in payload["agents"]:
        assert a["tier"] == tier_for(a["name"]), (
            f"{a['name']} catalogued tier {a['tier']} != registry {tier_for(a['name'])}"
        )


def test_catalog_consent_matches_live_registry():
    """Consent lever is resolved live from AGENT_REQUIRES (None if unmapped)."""
    payload = build_catalog()
    for a in payload["agents"]:
        assert a["consent"] == AGENT_REQUIRES.get(a["name"])


# ── Spec-45 section coverage ────────────────────────────────────────────


def test_all_spec45_sections_present():
    """Sections §2–§19 (the per-agent definitions) are each represented by at
    least one catalog entry."""
    covered: set[str] = set()
    for e in CATALOG:
        covered |= set(e.spec_sections)
    needed = {f"§{n}" for n in range(2, 20)}
    missing = needed - covered
    assert not missing, f"Spec-45 sections not represented in the catalog: {missing}"


# ── Model resolution ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "tier,expected",
    [
        ("flagship", "claude-opus-4-8"),
        ("workhorse", "claude-sonnet-4-6"),
        ("batch", "claude-haiku-4-5-20251001"),
    ],
)
def test_resolve_model_returns_real_claude_model_per_tier(tier, expected):
    model = resolve_model(tier)
    assert model is not None
    assert model["model_id"] == expected
    assert model["model_id"] in MODEL_PRICES
    assert model["price"] == MODEL_PRICES[expected]


def test_rule_based_tier_has_no_model():
    assert resolve_model("rule_based") is None


def test_every_llm_agent_resolves_to_a_priced_model():
    payload = build_catalog()
    for a in payload["agents"]:
        if a["tier"] == "rule_based":
            assert a["model_id"] is None
            continue
        assert a["model_id"] in MODEL_PRICES, f"{a['name']} → unpriced {a['model_id']}"


# ── Summary roll-up ─────────────────────────────────────────────────────


def test_tier_counts_sum_to_agent_count():
    payload = build_catalog()
    summary = payload["summary"]
    assert sum(summary["tier_counts"].values()) == summary["agent_count"]
    assert summary["agent_count"] == len(CATALOG)
    assert summary["llm_agent_count"] == summary["agent_count"] - summary["tier_counts"].get(
        "rule_based", 0
    )
    assert summary["fallback_coverage"] == "100%"


def test_tiers_block_only_lists_nonempty_tiers():
    payload = build_catalog()
    for t in payload["tiers"]:
        assert t["agent_count"] > 0
        assert t["label"] == TIER_META[t["tier"]]["label"]


# ── §21 prompt versioning is real (named files exist) ───────────────────


def test_named_prompt_files_exist():
    for e in CATALOG:
        if e.prompt_file is None:
            continue
        assert (PROMPTS_DIR / e.prompt_file).is_file(), (
            f"{e.name} references missing prompt file {e.prompt_file}"
        )


# ── enabled reflects the live gating flag ───────────────────────────────


def test_enabled_reflects_settings_flag(monkeypatch):
    """rationale is gated by ai_match_rationale_v2_enabled — flipping the flag
    flips the catalogued `enabled`."""
    monkeypatch.setattr(settings, "ai_match_rationale_v2_enabled", True)
    on = {a["name"]: a for a in build_catalog()["agents"]}
    assert on["rationale"]["enabled"] is True

    monkeypatch.setattr(settings, "ai_match_rationale_v2_enabled", False)
    off = {a["name"]: a for a in build_catalog()["agents"]}
    assert off["rationale"]["enabled"] is False


def test_flagless_agents_are_always_enabled():
    """Agents with no gating flag (pipeline / role-gated) report enabled=True."""
    payload = {a["name"]: a for a in build_catalog()["agents"]}
    matcher = payload["matcher"]
    assert matcher["flag"] is None
    assert matcher["enabled"] is True


# ── Public endpoint ─────────────────────────────────────────────────────


async def test_endpoint_returns_catalog(client: AsyncClient):
    resp = await client.get("/api/v1/ai/agents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["agents"], "expected a non-empty agent list"
    assert body["summary"]["agent_count"] == len(CATALOG)
    # The contract blocks the page renders are all present.
    for key in ("tiers", "principles", "fallback_flow", "cache_strategy", "validation"):
        assert key in body and body[key]


async def test_endpoint_agent_shape(client: AsyncClient):
    resp = await client.get("/api/v1/ai/agents")
    agent = resp.json()["agents"][0]
    for key in (
        "name",
        "title",
        "surface",
        "group",
        "purpose",
        "tier",
        "consent_label",
        "mode",
        "cache",
        "fallback",
        "enabled",
    ):
        assert key in agent, f"agent payload missing {key}"
