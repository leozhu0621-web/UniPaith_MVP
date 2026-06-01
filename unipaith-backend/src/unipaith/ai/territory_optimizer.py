"""Spec 40 §5 — TerritoryOptimizer.

Suggests high-yield schools / fairs per territory from historical conversion, so
a recruiter plans travel toward the sources that actually enrol students. Sonnet,
forced tool-use, behind ``ai_recruitment_v2_enabled``; returns ``None`` on any
failure so the service falls back to a deterministic prior-year-yield ranking
(§5: "Falls back to manual sorting"). Planning only — never selection (§5 / 46 §6).
"""

from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.territory_suggestions_schema import SUBMIT_TERRITORY_SUGGESTIONS_TOOL

logger = logging.getLogger("unipaith.territory_optimizer")

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8").rstrip()


def deterministic_suggestions(snapshot: dict) -> list[dict]:
    """Rule-based fallback: rank candidate sources by prior-year yield and nudge
    the obvious territory gaps (unassigned owner, thin pipeline). Always returns
    at least one suggestion so the UI never shows an empty AI panel."""
    out: list[dict] = []
    candidates = sorted(
        (snapshot.get("candidates") or []),
        key=lambda c: c.get("prior_year_yield") or 0,
        reverse=True,
    )
    for c in candidates[:3]:
        y = c.get("prior_year_yield")
        if not y:
            continue
        kind = "visit_fair" if (c.get("kind") == "fair") else "visit_school"
        out.append(
            {
                "kind": kind,
                "label": f"Prioritize {c.get('name')} — {y} enrolled last year.",
                "rationale": "Strongest prior-year yield among this territory's sources.",
                "candidate_name": c.get("name"),
            }
        )
    if not snapshot.get("has_owner"):
        out.append(
            {
                "kind": "assign_owner",
                "label": "This territory has no owner — assign a recruiter.",
                "rationale": "Unowned territories go unworked.",
                "candidate_name": None,
            }
        )
    if (snapshot.get("prospect_count") or 0) < 5:
        out.append(
            {
                "kind": "grow_pipeline",
                "label": "Thin pipeline — import a prospect list or capture leads at a fair.",
                "rationale": "Too few prospects to convert meaningfully yet.",
                "candidate_name": None,
            }
        )
    if not out:
        out.append(
            {
                "kind": "monitor",
                "label": "On track — no high-yield action right now.",
                "rationale": "No standout candidate or gap in this territory.",
                "candidate_name": None,
            }
        )
    return out[:5]


class TerritoryOptimizer:
    AGENT_NAME = "territory_optimizer"
    PROMPT_VERSION = "v1"

    def __init__(self, client: AIClient | None = None, *, system_prompt: str | None = None):
        self.client = client or get_client()
        self.system_prompt = system_prompt or _load_prompt("territory_optimizer.md")

    async def suggest(self, snapshot: dict, *, db: AsyncSession | None = None) -> list[dict] | None:
        """Return up to 5 ranked suggestions, or ``None`` on any failure (caller
        falls back to ``deterministic_suggestions``)."""
        try:
            response = await self.client.message(
                agent=self.AGENT_NAME,
                model="sonnet",
                system=[{"type": "text", "text": self.system_prompt, "cache_control": CACHE_1H}],
                messages=[{"role": "user", "content": self._payload(snapshot)}],
                tools=[{**SUBMIT_TERRITORY_SUGGESTIONS_TOOL, "cache_control": CACHE_1H}],
                tool_choice={"type": "tool", "name": "submit_territory_suggestions"},
                max_tokens=700,
                temperature=0.3,
                student_id=None,  # institution-side aggregate; no student PII
                surface="territory_suggestions",
                db=db,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("territory_optimizer agent call failed: %s", e)
            return None

        for b in response.content_blocks:
            if b.get("type") == "tool_use" and b.get("name") == "submit_territory_suggestions":
                items = (b.get("input") or {}).get("suggestions") or []
                out = [
                    {
                        "kind": str(s.get("kind") or "monitor"),
                        "label": str(s.get("label") or "").strip(),
                        "rationale": str(s.get("rationale") or "").strip(),
                        "candidate_name": (
                            str(s["candidate_name"]).strip() if s.get("candidate_name") else None
                        ),
                    }
                    for s in items
                    if str(s.get("label") or "").strip()
                ]
                return out[:5] or None
        return None

    @staticmethod
    def _payload(s: dict) -> str:
        lines = [
            f"Territory: {s.get('name', 'Unnamed')}",
            f"- Prospects: {s.get('prospect_count', 0)}",
            f"- Converted to applicants: {s.get('applicant_count', 0)}",
            f"- Conversion rate: {round((s.get('conversion_rate') or 0) * 100)}%",
            f"- Has assigned owner: {bool(s.get('has_owner'))}",
            "",
            "Candidate sources (high schools / fairs) with prior-year yield:",
        ]
        candidates = s.get("candidates") or []
        if candidates:
            for c in candidates[:12]:
                lines.append(
                    f"- {c.get('name')} ({c.get('kind', 'fair')}), "
                    f"prior-year yield: {c.get('prior_year_yield', 0)}"
                )
        else:
            lines.append("- (none on file)")
        lines += ["", "Call submit_territory_suggestions with the ranked plan."]
        return "\n".join(lines)


# ── Singleton ────────────────────────────────────────────────────────────────
_optimizer: TerritoryOptimizer | None = None


def get_territory_optimizer() -> TerritoryOptimizer:
    global _optimizer
    if _optimizer is None:
        _optimizer = TerritoryOptimizer()
    return _optimizer


def reset_territory_optimizer() -> None:
    global _optimizer
    _optimizer = None
