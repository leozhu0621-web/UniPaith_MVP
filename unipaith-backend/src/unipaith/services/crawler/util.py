"""Spec 60 — small shared helpers for the crawler pipeline."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal


def to_jsonable(obj):
    """Recursively coerce a value into something the JSONB serializer accepts —
    dates/datetimes → ISO strings, Decimal → float. Used wherever a raw extracted
    value (which may be a date, e.g. a scholarship deadline) is stored into a
    JSONB column (knowledge_documents.extracted_facts, entity_enrichments,
    change_events)."""
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return obj
