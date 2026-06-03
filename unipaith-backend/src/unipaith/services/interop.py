"""Spec 74 §1/§2 — CRM interop (wrap-around-Slate) + i18n locale (deterministic).

The doc's hard constraint: integrate with Slate, don't rip-replace
(`Competition`:2175); Slate ingests leads via weekly SFTP CSV (`Competition`:1759).
This serializes a normalized prospect/lead into Slate's standard lead row + a CSV
for delivery, and negotiates the student-facing locale (`74` §2; Studyportals 20+
languages, `Competition`:2095). Deterministic + PII-safe (the caller filters by
consent); the live SFTP/REST connector is the integration step, this is the
format/negotiation core.
"""

from __future__ import annotations

import csv
import io

# Our normalized field → Slate's standard inbound lead column.
_SLATE_LEAD_MAP: dict[str, str] = {
    "first_name": "first",
    "last_name": "last",
    "email": "email",
    "country": "country",
    "field_of_interest": "program",
    "degree_level": "level",
    "source": "source",
    "external_id": "ref",
}

SLATE_LEAD_COLUMNS: list[str] = list(_SLATE_LEAD_MAP.values())


def to_slate_lead_row(prospect: dict) -> dict:
    """Map a normalized prospect to a Slate lead row — only mapped, present keys
    (consent-filtered upstream); unknown/absent fields are omitted."""
    return {
        col: prospect.get(src)
        for src, col in _SLATE_LEAD_MAP.items()
        if prospect.get(src) is not None
    }


def serialize_leads_csv(prospects: list[dict]) -> str:
    """CSV for Slate SFTP ingestion — stable column order + header row."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=SLATE_LEAD_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for p in prospects:
        writer.writerow(to_slate_lead_row(p))
    return buf.getvalue()


def resolve_locale(
    accept_language: str | None, supported: list[str], *, default: str = "en"
) -> str:
    """Deterministic Accept-Language negotiation for the multilingual surfaces
    (`74` §2). Honors quality order, falls back from a region tag (en-US) to its
    base language (en), then to the default. Never machine-translates by itself —
    it only selects the locale; legal/consent copy stays human-reviewed (`74` §2)."""
    if not accept_language:
        return default
    supported_set = {s.lower() for s in supported}
    for chunk in accept_language.split(","):
        tag = chunk.split(";")[0].strip().lower()
        if not tag:
            continue
        if tag in supported_set:
            return tag
        base = tag.split("-")[0]
        if base in supported_set:
            return base
    return default
