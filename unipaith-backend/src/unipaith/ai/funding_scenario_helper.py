"""Spec 41 §2.3 / §5 — FundingScenarioHelper.

Advises the funding-package builder: projects each package component's draw
against its source pool's budget, flags over-commitment, and suggests a viable
re-mix (shift an over-budget amount to a pool with headroom). MVP fidelity is a
deterministic budget calculator — no model needed to add up dollars — but it is
registered as an agent (``workhorse`` tier, the future "suggest viable mixes"
LLM) so the AI surface is consistent and gated by ``ai_graduate_v2_enabled``.

The *hard* over-commit block (a package may not exceed a pool budget, §9) lives in
``graduate_service`` and is always enforced regardless of this flag — this helper
only produces the human-facing warnings + suggestions. Pure and deterministic;
never 5xxes.
"""

from __future__ import annotations


def _money(value) -> float:
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def _fmt(amount: float, currency: str = "USD") -> str:
    sym = {"USD": "$", "GBP": "£", "EUR": "€"}.get(currency, "")
    return f"{sym}{amount:,.0f}"


def analyze(components: list[dict], pools: list[dict]) -> dict:
    """Project package ``components`` against ``pools`` budgets.

    ``components``: ``[{kind, amount, source_pool_id, years}]`` — the draft package.
    ``pools``:      ``[{id, name, kind, total_budget, committed_other, currency}]``
                    where ``committed_other`` is the amount already committed by
                    *other* packages (this package excluded), so the projection is
                    idempotent when re-analyzing an existing package.

    Returns ``{per_pool, over_commit, warnings, suggestions}``.
    """
    pool_by_id = {str(p.get("id")): p for p in pools}

    # Sum this package's draw per pool.
    this_draw: dict[str, float] = {}
    for c in components:
        pid = c.get("source_pool_id")
        if pid is None:
            continue
        this_draw[str(pid)] = this_draw.get(str(pid), 0.0) + _money(c.get("amount"))

    per_pool: list[dict] = []
    warnings: list[str] = []
    over_commit = False

    for pid, draw in this_draw.items():
        pool = pool_by_id.get(pid)
        if pool is None:
            continue
        budget = _money(pool.get("total_budget"))
        committed_other = _money(pool.get("committed_other"))
        projected = round(committed_other + draw, 2)
        remaining = round(budget - projected, 2)
        over = projected > budget + 1e-6
        currency = pool.get("currency") or "USD"
        per_pool.append(
            {
                "pool_id": pid,
                "name": pool.get("name"),
                "budget": budget,
                "committed": projected,
                "this_package": round(draw, 2),
                "remaining": remaining,
                "over": over,
            }
        )
        if over:
            over_commit = True
            warnings.append(
                f"{pool.get('name') or 'Pool'} exceeds budget by "
                f"{_fmt(projected - budget, currency)}."
            )

    suggestions = _suggestions(per_pool, pool_by_id)
    return {
        "per_pool": per_pool,
        "over_commit": over_commit,
        "warnings": warnings,
        "suggestions": suggestions,
    }


def _suggestions(per_pool: list[dict], pool_by_id: dict[str, dict]) -> list[str]:
    """For each over-budget pool, suggest shifting the overage to the pool with
    the most headroom (a viable re-mix)."""
    out: list[str] = []
    headroom = sorted(
        (p for p in per_pool if not p["over"] and p["remaining"] > 0),
        key=lambda p: p["remaining"],
        reverse=True,
    )
    for pool in per_pool:
        if not pool["over"]:
            continue
        overage = round(pool["committed"] - pool["budget"], 2)
        currency = (pool_by_id.get(pool["pool_id"]) or {}).get("currency") or "USD"
        target = next((h for h in headroom if h["remaining"] >= overage), None)
        if target:
            out.append(
                f"Shift {_fmt(overage, currency)} from {pool['name']} to "
                f"{target['name']} ({_fmt(target['remaining'], currency)} remaining)."
            )
        else:
            out.append(
                f"Reduce {pool['name']} by {_fmt(overage, currency)} or raise its budget — "
                "no other pool has enough headroom to absorb it."
            )
    return out


class FundingScenarioHelper:
    """Budget projection + over-commit warnings + re-mix suggestions."""

    AGENT_NAME = "funding_scenario_helper"
    PROMPT_VERSION = "v1"

    def analyze(self, components: list[dict], pools: list[dict]) -> dict:
        return analyze(components, pools)


# ── Singleton ────────────────────────────────────────────────────────────────
_helper: FundingScenarioHelper | None = None


def get_funding_scenario_helper() -> FundingScenarioHelper:
    global _helper
    if _helper is None:
        _helper = FundingScenarioHelper()
    return _helper


def reset_funding_scenario_helper() -> None:
    global _helper
    _helper = None
