"""DocumentParseTriage — Spec 24 §9 / 45 §19.

Haiku-tier triage of an uploaded institution dataset's parse health. Given the
*aggregate* validation counts (never the PII rows), it returns a short
human-readable status + recommended action that the upload UI can show above the
deterministic validation report.

The calling :class:`DatasetService` always has the rule-based report to fall back
on, so any failure here (consent/parse/provider) returns ``None`` and the upload
proceeds with the deterministic report unchanged (Plan-2 integration invariant —
never raise to the caller).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from unipaith.ai.client import AIClient, get_client
from unipaith.ai.prompt_cache import CACHE_1H
from unipaith.ai.tools.document_parse_triage_schema import SUBMIT_TRIAGE_TOOL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_PROMPT = (PROMPTS_DIR / "document_parse_triage.md").read_text(encoding="utf-8").rstrip()

AGENT_NAME = "document_parse_triage"


def _aggregate_payload(file_name: str, dataset_type: str, size_bytes: int, report: dict) -> str:
    """Compact, PII-free payload — only metadata and issue counts."""
    return json.dumps(
        {
            "file_name": file_name,
            "dataset_type": dataset_type,
            "size_bytes": size_bytes,
            "total_rows": report.get("total_rows", 0),
            "valid_rows": report.get("valid_rows", 0),
            "rows_missing_required": len(report.get("missing_required", [])),
            "duplicate_rows": len(report.get("duplicates", [])),
            "invalid_dates": len(report.get("invalid_dates", [])),
            "unmappable_programs": len(report.get("unmappable_programs", [])),
        },
        ensure_ascii=False,
    )


def _parse(blocks: list[dict[str, Any]]) -> dict | None:
    for b in blocks:
        if b.get("type") == "tool_use" and b.get("name") == "submit_triage":
            data = b.get("input") or {}
            status = data.get("status")
            summary = data.get("summary")
            if status and summary:
                return {
                    "triage_status": str(status),
                    "triage_summary": str(summary),
                    "triage_recommended_action": str(data.get("recommended_action") or "proceed"),
                }
    return None


async def triage_parse(
    *,
    file_name: str,
    dataset_type: str,
    size_bytes: int,
    report: dict,
    client: AIClient | None = None,
) -> dict | None:
    """Return a triage dict to merge into the validation report, or ``None`` to
    keep the deterministic report (fallback). Best-effort; never raises."""
    try:
        cl = client or get_client()
        payload = _aggregate_payload(file_name, dataset_type, size_bytes, report)
        response = await cl.message(
            agent=AGENT_NAME,
            model="haiku",
            system=[{"type": "text", "text": _PROMPT, "cache_control": CACHE_1H}],
            messages=[{"role": "user", "content": payload}],
            tools=[{**SUBMIT_TRIAGE_TOOL, "cache_control": CACHE_1H}],
            tool_choice={"type": "tool", "name": "submit_triage"},
            max_tokens=400,
            temperature=0.0,
            surface="data_upload",
        )
        return _parse(response.content_blocks)
    except Exception as exc:  # noqa: BLE001 — triage is best-effort
        logger.info("DocumentParseTriage fell back to rule-based report: %s", exc)
        return None
