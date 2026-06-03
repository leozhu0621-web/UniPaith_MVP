"""Spec 71 §3 — prospect→ambassador tag-matching (deterministic).

The Handshake/Unibuddy mechanic: auto-match a prospect to current-student / alumni
ambassadors by shared course / country / interest tags (`Competition`:2343). Pure
tag overlap — deterministic, fairness-clean (no protected attributes enter the
match, `46` §6), never 5xx. An optional Claude "why this ambassador" rationale
enriches it (`63` §3); this is the floor the live ambassador layer ranks on.
"""

from __future__ import annotations

from typing import Any


def _jaccard(a: Any, b: Any) -> float:
    sa, sb = set(a or []), set(b or [])
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / max(1, len(sa | sb))


def ambassador_match_score(prospect: dict, ambassador: dict) -> float:
    """Weighted tag overlap in [0,1]: field 0.4, country 0.3, interest 0.3."""
    field = _jaccard(prospect.get("fields"), ambassador.get("fields"))
    country = _jaccard(prospect.get("countries"), ambassador.get("countries"))
    interest = _jaccard(prospect.get("interests"), ambassador.get("interests"))
    return round(0.4 * field + 0.3 * country + 0.3 * interest, 4)


def match_ambassadors(
    prospect: dict, ambassadors: list[dict], *, limit: int = 10, min_score: float = 0.01
) -> list[dict]:
    """Rank accepting ambassadors by tag overlap. Skips non-accepting ones and
    those below min_score; deterministic tie-break on id for stable ordering."""
    scored: list[dict] = []
    for a in ambassadors:
        if a.get("accepting_chats") is False:
            continue
        score = ambassador_match_score(prospect, a)
        if score >= min_score:
            scored.append(
                {
                    "ambassador_id": a.get("id"),
                    "score": score,
                    "role": a.get("role", "ambassador"),
                }
            )
    scored.sort(key=lambda x: (x["score"], str(x["ambassador_id"])), reverse=True)
    return scored[:limit]
