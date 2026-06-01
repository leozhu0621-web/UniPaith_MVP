"""CountryRequirementAdvisor — Spec 38 §2.3 / §5.

Suggests the country-specific document pack that auto-attaches to an
international applicant's checklist based on nationality / country of birth.

Two layers:
- :data:`DEFAULT_COUNTRY_PACKS` + :func:`default_pack_for` — the platform's
  in-code default packs (always available; the source of truth for tests and
  the fallback). A generic pack covers any country not listed.
- :func:`advise_country_pack` — the optional Haiku-tier agent (gated by
  ``ai_international_v2_enabled``) that proposes a richer pack. On any failure it
  returns ``None`` and the caller keeps the default pack — AI structures data
  for a human; it never marks anything received.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.country_requirement_advisor_schema import SUBMIT_COUNTRY_PACK_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_PROMPT = (PROMPTS_DIR / "country_requirement_advisor.md").read_text(encoding="utf-8").rstrip()

AGENT_NAME = "country_requirement_advisor"


def _req(item: str, description: str = "") -> dict:
    return {"item": item, "description": description} if description else {"item": item}


# Sensible platform defaults (Spec 38 §8: default packs need legal review before
# launch; these are conservative document-only starting points). Keyed by ISO
# 3166-1 alpha-2. A country not listed gets ``_GENERIC_PACK``.
DEFAULT_COUNTRY_PACKS: dict[str, dict] = {
    "CN": {
        "country_name": "China",
        "requirements": [
            _req("Credential evaluation (WES/ECE)", "Course-by-course evaluation of transcript"),
            _req("Certified English translation", "Of degree certificate and transcript"),
            _req("Degree verification (CHSI/CDGDC)", "Online verification report of the degree"),
            _req("Notarized graduation certificate"),
        ],
    },
    "IN": {
        "country_name": "India",
        "requirements": [
            _req("Credential evaluation (WES/ECE)", "Especially for 3-year bachelor's degrees"),
            _req("Official consolidated marksheets", "All semesters/years"),
            _req("Provisional or final degree certificate"),
            _req("Medium-of-instruction certificate", "If claiming an English waiver"),
        ],
    },
    "NG": {
        "country_name": "Nigeria",
        "requirements": [
            _req("Credential evaluation", "Course-by-course evaluation"),
            _req("NYSC certificate", "Or exemption letter"),
            _req("Notarized degree certificate"),
            _req("Certified academic transcript", "Sent directly from the institution"),
        ],
    },
    "BR": {
        "country_name": "Brazil",
        "requirements": [
            _req("Apostille (Hague Convention)", "On the diploma and transcript"),
            _req("Certified English translation"),
            _req("Histórico escolar", "Official transcript"),
            _req("Diploma de graduação", "Degree certificate"),
        ],
    },
    "GB": {
        "country_name": "United Kingdom",
        "requirements": [
            _req("Degree certificate and transcript"),
            _req("Classification confirmation", "First / Upper Second, etc."),
        ],
    },
}

_GENERIC_PACK: dict = {
    "country_name": "",
    "requirements": [
        _req("Credential evaluation", "Evaluate the foreign transcript to the program scale"),
        _req("Certified English translation", "Of academic documents not in English"),
        _req("Notarized / attested degree certificate"),
        _req("Official academic transcript", "Sent directly from the issuing institution"),
    ],
}


def default_pack_for(country_code: str | None, country_name: str | None = None) -> dict:
    """Return the platform default pack for a country, with statuses set to
    ``pending`` for an applicant's checklist. Always returns a usable pack."""
    code = (country_code or "").strip().upper()[:2]
    base = DEFAULT_COUNTRY_PACKS.get(code)
    if base is None:
        base = {**_GENERIC_PACK, "country_name": country_name or code or "International"}
    return {
        "country_code": code or None,
        "country_name": base["country_name"] or country_name or code or "International",
        "requirements": [dict(r) for r in base["requirements"]],
    }


def _payload(country_code: str | None, country_name: str | None, degree_type: str | None) -> str:
    return json.dumps(
        {
            "country_code": (country_code or "").upper()[:2] or None,
            "country_name": country_name or None,
            "degree_level": degree_type or "unknown",
        },
        ensure_ascii=False,
    )


def _parse(blocks: list[dict[str, Any]]) -> dict | None:
    for b in blocks:
        if b.get("type") == "tool_use" and b.get("name") == "submit_country_pack":
            data = b.get("input") or {}
            items = data.get("requirements") or []
            clean = [
                {
                    "item": str(it.get("item")).strip()[:160],
                    "description": str(it.get("description") or "").strip()[:300],
                }
                for it in items
                if isinstance(it, dict) and it.get("item")
            ]
            if not clean:
                return None
            return {
                "country_name": str(data.get("country_name") or "").strip()[:120] or None,
                "requirements": clean,
            }
    return None


async def advise_country_pack(
    *,
    country_code: str | None,
    country_name: str | None = None,
    degree_type: str | None = None,
    client: AIClient | None = None,
) -> dict | None:
    """Return a suggested pack dict, or ``None`` to keep the default pack.
    Best-effort; never raises."""
    try:
        cl = client or get_client()
        payload = _payload(country_code, country_name, degree_type)
        response = await cl.message(
            agent=AGENT_NAME,
            model="haiku",
            system=[{"type": "text", "text": _PROMPT, "cache_control": CACHE_1H}],
            messages=[{"role": "user", "content": payload}],
            tools=[{**SUBMIT_COUNTRY_PACK_TOOL, "cache_control": CACHE_1H}],
            tool_choice={"type": "tool", "name": "submit_country_pack"},
            max_tokens=600,
            temperature=0.0,
            surface="international",
        )
        return _parse(response.content_blocks)
    except Exception as exc:  # noqa: BLE001 — advisory is best-effort
        logger.info("CountryRequirementAdvisor fell back to default pack: %s", exc)
        return None
