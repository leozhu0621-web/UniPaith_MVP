"""AirtableSyncService — upsert Prompt Library + Session Templates from Airtable.

Designed so the constructor receives ``(db, client)`` and tests can inject a
``FakeClient`` without hitting the real Airtable API.

``sync_all()`` is the primary entry point::

    service = AirtableSyncService(db, client)
    result = await service.sync_all()
    # {"prompts": {...}, "templates": {...}}
    # or {"skipped": "airtable not configured"} when credentials are absent

Invalid rows are collected in ``result["rejected"]`` and never raised — the
caller always gets a summary dict, never an exception from a bad Airtable row.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from unipaith.models.prompt_catalog import PromptCatalog
from unipaith.models.session_template import SessionTemplate, SessionTemplateStep
from unipaith.services.chat.template_actions import ACTION_KEYS
from unipaith.services.enrichment_planner import CATALOG as _SEED_CATALOG

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Valid value sets (derived from the in-code CATALOG + model constraints)
# ---------------------------------------------------------------------------

# ask_kinds listed in the spec + present in the CATALOG.
_VALID_ASK_KINDS: frozenset[str] = frozenset(
    ["choice", "multi", "keywords", "typeahead", "scale", "number", "range", "date", "text"]
)

# value_types derived from the seed CATALOG.
_VALID_VALUE_TYPES: frozenset[str] = frozenset(f["type"] for f in _SEED_CATALOG) | frozenset(
    ["categorical", "numeric", "boolean", "text", "date", "range", "multi", "weight"]
)

# ask_kinds whose options list must be non-empty.
_OPTION_BEARING_ASK_KINDS: frozenset[str] = frozenset(["choice", "multi", "keywords"])

# Keys from the seed CATALOG — prompt_keys used in templates must be in the DB.
_SEED_CATALOG_KEYS: frozenset[str] = frozenset(f["key"] for f in _SEED_CATALOG)


# ---------------------------------------------------------------------------
# Row validation helpers
# ---------------------------------------------------------------------------


def validate_prompt_row(fields: dict[str, Any]) -> str | None:
    """Return a rejection reason string, or None if the row is valid."""
    key = (fields.get("key") or "").strip()
    if not key:
        return "missing or empty key"

    ask_kind = (fields.get("ask_kind") or "").strip()
    if ask_kind not in _VALID_ASK_KINDS:
        return f"unknown ask_kind {ask_kind!r}"

    value_type = (fields.get("value_type") or "").strip()
    if value_type not in _VALID_VALUE_TYPES:
        return f"unknown value_type {value_type!r}"

    if ask_kind in _OPTION_BEARING_ASK_KINDS:
        options = _coerce_options(fields.get("options"))
        if not options:
            return f"ask_kind {ask_kind!r} requires non-empty options"

    saves_to = (fields.get("saves_to") or "").strip()
    if not saves_to:
        return "missing or empty saves_to"

    return None


def _normalize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    """Map Airtable column headers to the snake_case keys the sync expects.

    Airtable returns each record's fields keyed by the column's DISPLAY name
    (e.g. "Ask Kind", "Saves To", "Step Order"), while the sync logic reads
    snake_case keys (ask_kind, saves_to, step_order). Normalizing here lets
    editors keep friendly Title-Case headers in Airtable while the sync stays
    stable. Already-snake_case keys (lower-case, no spaces) pass through
    unchanged, so hand-authored fixtures keep working. First writer wins when
    two headers collapse to the same key.
    """
    out: dict[str, Any] = {}
    for key, value in fields.items():
        norm = key.strip().lower().replace(" ", "_")
        out.setdefault(norm, value)
    return out


def _coerce_options(raw: Any) -> list | None:
    """Coerce Airtable options to a Python list (or None).

    Airtable may return a list directly, a JSON string, a newline-separated
    multiline string (the canonical, editor-friendly form), or None/missing.
    """
    if raw is None:
        return None
    if isinstance(raw, list):
        return raw if raw else None
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed if parsed else None
        except (json.JSONDecodeError, ValueError):
            pass
        # Newline-separated (one option per line) is the canonical Airtable form.
        # Split on newlines so commas INSIDE an option (e.g. "Small (under 5,000)")
        # are preserved. Fall back to comma-splitting for single-line lists.
        if "\n" in raw:
            items = [s.strip() for s in raw.splitlines() if s.strip()]
        else:
            items = [s.strip() for s in raw.split(",") if s.strip()]
        return items if items else None
    return None


def _coerce_jsonb(raw: Any) -> list | dict | None:
    """Coerce a JSONB field (display_logic etc.) from Airtable."""
    if raw is None:
        return None
    if isinstance(raw, (list, dict)):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


# ---------------------------------------------------------------------------
# Main service
# ---------------------------------------------------------------------------


class AirtableSyncService:
    def __init__(self, db: AsyncSession, client: Any) -> None:
        """
        Args:
            db: async SQLAlchemy session.
            client: an AirtableClient (or a fake with the same interface).
                    Must expose ``is_configured: bool`` and
                    ``async list_records(table_name) -> list[dict]``.
        """
        self.db = db
        self.client = client

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    async def sync_all(self) -> dict[str, Any]:
        """Run both syncs. Returns a summary dict.

        When the client is not configured, returns immediately with
        ``{"skipped": "airtable not configured"}`` and writes nothing.
        Never raises — bad rows are collected, not propagated.
        """
        if not self.client.is_configured:
            return {"skipped": "airtable not configured"}

        from unipaith.config import settings  # local import to allow test override

        prompts_result = await self.sync_prompts(
            table_name=settings.airtable_prompts_table,
        )
        templates_result = await self.sync_templates(
            templates_table=settings.airtable_templates_table,
            steps_table=settings.airtable_steps_table,
        )
        return {"prompts": prompts_result, "templates": templates_result}

    async def sync_prompts(self, table_name: str = "Prompts") -> dict[str, Any]:
        """Pull prompt records from Airtable and upsert into ``prompt_catalog``.

        Returns::

            {"upserted": <int>, "rejected": [{"key": ..., "reason": ...}, ...]}
        """
        records = await self.client.list_records(table_name)
        upserted = 0
        rejected: list[dict[str, Any]] = []

        # Load current catalog keys from DB (for cross-validation if needed later).
        # Not strictly needed for prompts but useful for consistency.
        for record in records:
            airtable_id: str = record.get("id", "")
            fields: dict[str, Any] = _normalize_fields(record.get("fields", {}))

            reason = validate_prompt_row(fields)
            if reason:
                rejected.append({"key": fields.get("key", ""), "reason": reason})
                logger.warning("airtable_sync: rejected prompt record %s — %s", airtable_id, reason)
                continue

            key = fields["key"].strip()
            options = _coerce_options(fields.get("options"))
            display_logic = _coerce_jsonb(fields.get("display_logic")) or []

            values: dict[str, Any] = {
                "key": key,
                "section": (fields.get("section") or "Basics").strip(),
                "question": (fields.get("question") or "").strip(),
                "ask_kind": fields["ask_kind"].strip(),
                "value_type": fields["value_type"].strip(),
                "options": options,
                "tier": (fields.get("tier") or "standard").strip(),
                "required": bool(fields.get("required", False)),
                "display_logic": display_logic,
                "saves_to": fields["saves_to"].strip(),
                "reference_source": (fields.get("reference_source") or None),
                "sort_order": int(fields.get("sort_order") or 0),
                "active": bool(fields.get("active", True)),
                "airtable_record_id": airtable_id or None,
            }

            await self.db.execute(
                pg_insert(PromptCatalog)
                .values(**values)
                .on_conflict_do_update(
                    index_elements=["key"],
                    set_={
                        "section": values["section"],
                        "question": values["question"],
                        "ask_kind": values["ask_kind"],
                        "value_type": values["value_type"],
                        "options": values["options"],
                        "tier": values["tier"],
                        "required": values["required"],
                        "display_logic": values["display_logic"],
                        "saves_to": values["saves_to"],
                        "reference_source": values["reference_source"],
                        "sort_order": values["sort_order"],
                        "active": values["active"],
                        "airtable_record_id": values["airtable_record_id"],
                    },
                )
            )
            upserted += 1

        await self.db.flush()
        return {"upserted": upserted, "rejected": rejected}

    async def sync_templates(
        self,
        templates_table: str = "Templates",
        steps_table: str = "Template Steps",
    ) -> dict[str, Any]:
        """Pull template + step records from Airtable and upsert.

        Template rows are upserted by ``key``. Steps are replaced per
        template (delete existing → insert new) so step ordering is always
        fresh. Invalid templates or steps are skipped and collected.

        Returns::

            {"upserted": <int>, "rejected": [{"key": ..., "reason": ...}, ...]}
        """
        template_records = await self.client.list_records(templates_table)
        step_records = await self.client.list_records(steps_table)

        # Build lookup: airtable template id → validated fields
        valid_templates: dict[str, dict[str, Any]] = {}
        rejected: list[dict[str, Any]] = []

        # Load the set of valid prompt_keys from prompt_catalog + the seed.
        db_prompt_keys = await self._load_db_prompt_keys()
        all_valid_prompt_keys = _SEED_CATALOG_KEYS | db_prompt_keys

        for record in template_records:
            airtable_id: str = record.get("id", "")
            fields: dict[str, Any] = _normalize_fields(record.get("fields", {}))
            key = (fields.get("key") or "").strip()

            reason = _validate_template_row(fields)
            if reason:
                rejected.append({"key": key, "reason": reason})
                logger.warning(
                    "airtable_sync: rejected template record %s — %s", airtable_id, reason
                )
                continue

            valid_templates[airtable_id] = {"fields": fields, "key": key, "steps": []}

        # Build lookup: airtable template id → steps (from the steps table).
        # Steps reference templates via a "template_key" field (matching template.key)
        # OR a "Template" linked-record field (list of template airtable ids).
        # We support both patterns.
        key_to_airtable_id: dict[str, str] = {v["key"]: k for k, v in valid_templates.items()}

        for record in step_records:
            airtable_id: str = record.get("id", "")
            fields: dict[str, Any] = _normalize_fields(record.get("fields", {}))

            # Resolve which template this step belongs to.
            tmpl_airtable_id = _resolve_step_template_id(fields, key_to_airtable_id)
            if tmpl_airtable_id is None or tmpl_airtable_id not in valid_templates:
                rejected.append(
                    {
                        "key": fields.get("template_key") or fields.get("template") or "",
                        "reason": "step references unknown or invalid template",
                    }
                )
                continue

            reason = _validate_step_row(fields, all_valid_prompt_keys)
            if reason:
                rejected.append(
                    {
                        "key": fields.get("prompt_key") or fields.get("action_key") or "",
                        "reason": reason,
                    }
                )
                logger.warning("airtable_sync: rejected step record %s — %s", airtable_id, reason)
                continue

            valid_templates[tmpl_airtable_id]["steps"].append(
                {"fields": fields, "airtable_id": airtable_id}
            )

        # Upsert templates + their steps.
        upserted = 0
        for tmpl_airtable_id, tmpl_data in valid_templates.items():
            fields = tmpl_data["fields"]
            key = tmpl_data["key"]

            tmpl_values: dict[str, Any] = {
                "key": key,
                "title": (fields.get("title") or "").strip(),
                "topic": (fields.get("topic") or "").strip(),
                "stage": (fields.get("stage") or "").strip(),
                "outcome": (fields.get("outcome") or "").strip(),
                "icon": (fields.get("icon") or "").strip(),
                "sort_order": int(fields.get("sort_order") or 0),
                "active": bool(fields.get("active", True)),
                "airtable_record_id": tmpl_airtable_id or None,
            }

            result = await self.db.execute(
                pg_insert(SessionTemplate)
                .values(**tmpl_values)
                .on_conflict_do_update(
                    index_elements=["key"],
                    set_={
                        "title": tmpl_values["title"],
                        "topic": tmpl_values["topic"],
                        "stage": tmpl_values["stage"],
                        "outcome": tmpl_values["outcome"],
                        "icon": tmpl_values["icon"],
                        "sort_order": tmpl_values["sort_order"],
                        "active": tmpl_values["active"],
                        "airtable_record_id": tmpl_values["airtable_record_id"],
                    },
                )
                .returning(SessionTemplate.id)
            )
            row = result.fetchone()
            if row is None:
                # Fetch the existing row's id after conflict update.
                existing = await self.db.scalar(
                    select(SessionTemplate.id).where(SessionTemplate.key == key)
                )
                template_db_id = existing
            else:
                template_db_id = row[0]

            if template_db_id is None:
                logger.warning("airtable_sync: could not resolve DB id for template %s", key)
                continue

            # Replace steps: delete existing, insert fresh.
            await self.db.execute(
                delete(SessionTemplateStep).where(SessionTemplateStep.template_id == template_db_id)
            )

            sorted_steps = sorted(
                tmpl_data["steps"],
                key=lambda s: int(s["fields"].get("step_order") or 0),
            )
            for step_order, step_data in enumerate(sorted_steps):
                sf = step_data["fields"]
                step_airtable_id = step_data["airtable_id"]
                await self.db.execute(
                    pg_insert(SessionTemplateStep).values(
                        template_id=template_db_id,
                        step_order=step_order,
                        step_type=(sf.get("step_type") or "prompt").strip(),
                        prompt_key=sf.get("prompt_key") or None,
                        action_key=sf.get("action_key") or None,
                        label=(sf.get("label") or "").strip(),
                        airtable_record_id=step_airtable_id or None,
                    )
                )

            upserted += 1

        await self.db.flush()
        return {"upserted": upserted, "rejected": rejected}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_db_prompt_keys(self) -> frozenset[str]:
        """Return the set of active prompt keys currently in the DB."""
        rows = (
            (await self.db.execute(select(PromptCatalog.key).where(PromptCatalog.active.is_(True))))
            .scalars()
            .all()
        )
        return frozenset(rows)


# ---------------------------------------------------------------------------
# Template / step validation helpers
# ---------------------------------------------------------------------------


def _validate_template_row(fields: dict[str, Any]) -> str | None:
    """Return a rejection reason or None."""
    key = (fields.get("key") or "").strip()
    if not key:
        return "missing or empty key"
    if not (fields.get("title") or "").strip():
        return "missing title"
    if not (fields.get("topic") or "").strip():
        return "missing topic"
    if not (fields.get("stage") or "").strip():
        return "missing stage"
    if not (fields.get("outcome") or "").strip():
        return "missing outcome"
    if not (fields.get("icon") or "").strip():
        return "missing icon"
    return None


def _validate_step_row(fields: dict[str, Any], valid_prompt_keys: frozenset[str]) -> str | None:
    """Return a rejection reason or None."""
    step_type = (fields.get("step_type") or "").strip()
    if step_type not in ("prompt", "action"):
        return f"invalid step_type {step_type!r}"

    prompt_key = (fields.get("prompt_key") or "").strip() or None
    action_key = (fields.get("action_key") or "").strip() or None

    if bool(prompt_key) == bool(action_key):
        return "exactly one of prompt_key / action_key must be set"

    if step_type == "prompt":
        if not prompt_key:
            return "step_type='prompt' requires prompt_key"
        if prompt_key not in valid_prompt_keys:
            return f"prompt_key {prompt_key!r} not in catalog"
    elif step_type == "action":
        if not action_key:
            return "step_type='action' requires action_key"
        if action_key not in ACTION_KEYS:
            return f"action_key {action_key!r} not in ACTION_CATALOG"

    return None


def _resolve_step_template_id(
    fields: dict[str, Any],
    key_to_airtable_id: dict[str, str],
) -> str | None:
    """Resolve which template airtable-id this step belongs to.

    Expects *fields* already normalized (snake_case headers). Supports two
    Airtable schema patterns:
    1. A ``template_key`` plain-text field matching template.key.
    2. A ``Template`` linked-record field (normalized to ``template``; a list
       of airtable record ids).
    """
    # Pattern 1: plain text key
    template_key = (fields.get("template_key") or "").strip()
    if template_key:
        return key_to_airtable_id.get(template_key)

    # Pattern 2: Airtable linked record (list of ids) — "Template" → "template".
    linked = fields.get("template")
    if isinstance(linked, list) and linked:
        return linked[0]  # first link wins
    if isinstance(linked, str) and linked.strip():
        return linked.strip()

    return None
