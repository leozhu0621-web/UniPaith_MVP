# Airtable Prompt Library Setup

This document describes the Airtable base that holds the **entire Prompt Library** (questions, options, session templates, and their steps) and the env vars that connect it to the live app. Once configured, `POST /api/v1/ops/airtable/sync` (X-Ops-Token guarded) pulls records from Airtable and upserts them into `prompt_catalog` and `session_templates` / `session_template_steps`.

> **The base already exists — you do not need to create it.**
> Base: **"UniPaith Prompt Library"** → `https://airtable.com/appWT0yIT31IJu01R`
> It is fully populated: **Prompts (42) · Actions (9) · Templates (8) · Template Steps (24)**.
> Skip to [§2 Set environment variables](#2-set-environment-variables) to go live. §1 documents the schema for reference / future edits.

---

## 1. Base schema (already built)

Four tables. **Column headers are friendly Title-Case** (e.g. `Ask Kind`, `Saves To`, `Sort Order`) — the sync normalizes them to the snake_case keys below automatically, so you can keep editing in readable columns. (Lower-case snake_case headers also work, so older bases keep syncing.)

### Table: Prompts

Maps to `prompt_catalog`. Header → field key:

| Column header | Field key | Type | Notes |
|---|---|---|---|
| `Key` | `key` | Single line text | **Required. Unique.** Snake_case, e.g. `career_goal` |
| `Section` | `section` | Long text | Display group: `Basics`, `Academics`, `Your direction`, `Experience`, `Goals`, `Where & how`, `What matters most`, `Money` |
| `Question` | `question` | Long text | The counselor-voiced question shown to the student |
| `Ask Kind` | `ask_kind` | Single select | One of: `choice`, `multi`, `keywords`, `typeahead`, `scale`, `number`, `range`, `date`, `text` |
| `Value Type` | `value_type` | Single select | One of: `categorical`, `numeric`, `boolean`, `text`, `date`, `range`, `multi`, `weight` |
| `Options` | `options` | Long text | **One option per line** (newline-separated) for `choice`/`multi`/`keywords`. Commas inside an option (e.g. `Small (under 5,000)`) are preserved. A JSON array string also works. Leave blank for other ask_kinds |
| `Tier` | `tier` | Single select | `essential`, `high_value`, or `standard` |
| `Saves To` | `saves_to` | Single line text | **Required.** The My Space field key this answer writes to (usually same as `Key`) |
| `Sort Order` | `sort_order` | Number | Display ordering (integer) |
| `Active` | `active` | Checkbox | Unchecked = hidden from the student UI |

*(Optional snake_case-only columns the sync also reads if present: `required` (checkbox), `display_logic` (JSON array), `reference_source` (e.g. `countries`). They are omitted from the current base — `required` defaults false, `display_logic` empty.)*

**Validation rules enforced by the sync:**
- `key` must not be empty
- `ask_kind` must be one of the valid values above
- `value_type` must be one of the valid values above
- `choice`, `multi`, and `keywords` rows must have a non-empty `options` list
- `saves_to` must not be empty
- Invalid rows are skipped and returned in the `rejected` list — they do not block the sync

**Important:** The seeded rows (from the in-code `CATALOG`) already exist in the DB. Airtable edits to those rows (same `key`) will update them on sync. Rows seeded from code that Airtable has never touched are left as-is by the seed — only Airtable can change them once it has written `airtable_record_id`.

---

### Table: Templates

Maps to `session_templates`. Header → field key:

| Column header | Field key | Type | Notes |
|---|---|---|---|
| `Key` | `key` | Single line text | **Required. Unique.** Snake_case, e.g. `sharpen_strategy` |
| `Title` | `title` | Single line text | **Required.** Human-readable title |
| `Topic` | `topic` | Single select | **Required.** `profile`, `goals`, `needs`, `strategy`, `schools`, `connect`, `manage` |
| `Stage` | `stage` | Single select | **Required.** `discovery`, `recommendation`, or `application` |
| `Outcome` | `outcome` | Single line text | **Required.** One-line description of what the template produces |
| `Icon` | `icon` | Single line text | **Required.** lucide icon name, e.g. `pen`, `flag`, `compass`, `list` |
| `Sort Order` | `sort_order` | Number | Integer sort order in the template picker |
| `Active` | `active` | Checkbox | Unchecked = hidden from students |

---

### Table: Template Steps

Maps to `session_template_steps`. Each row is one step in a template. Header → field key:

| Column header | Field key | Type | Notes |
|---|---|---|---|
| `Template` | `template` | Linked record → Templates | The parent template. (A plain-text `template_key` column also works as an alternative.) |
| `Step Order` | `step_order` | Number | Integer ordering within the template (0-indexed) |
| `Step Type` | `step_type` | Single select | **Required.** `prompt` or `action` |
| `Prompt Key` | `prompt_key` | Single line text | Required when `Step Type = prompt`. Must match a `Key` in the Prompts table |
| `Action Key` | `action_key` | Single line text | Required when `Step Type = action`. Must match a `Key` in the Actions table |
| `Label` | `label` | Single line text | Short label shown on the step card |
| `Step` | — | Single line text | Primary cell, human-readable id (`<template> · <order> · <label>`). Not synced |

**Exactly one** of `Prompt Key` / `Action Key` must be set per row.

**Steps replace on every sync:** when a template is synced, its existing steps in the DB are deleted and replaced with the Airtable rows. This keeps ordering clean. The template itself is upserted (no data loss to template metadata).

---

### Table: Actions (reference)

A read-only reference of the **code-backed capabilities** a template step can run (mirrors `ACTION_CATALOG` in `services/chat/template_actions.py`). Editors pick an `Action Key` from this list when authoring a step — a NEW action requires an engineer to implement it, so this table is documentation, not a sync source.

| Column header | Notes |
|---|---|
| `Key` | The action key referenced by a step's `Action Key` |
| `Label` | Human-readable label |
| `Status` | `live` (wired to a real artifact) or `coming soon` (honest placeholder) |

**Live actions:** `build_school_list`, `generate_strategy`, `compare_schools`.
**Coming soon:** `draft_feedback`, `interview_practice`, `build_checklist`, `find_events`, `generate_needs_map`, `generate_goal_stack`.

---

## 2. Set environment variables

Add these to AWS Secrets Manager (or your `.env` for local dev):

```
AIRTABLE_API_KEY=pat...                 # Personal access token, created at airtable.com/create/tokens
AIRTABLE_BASE_ID=appWT0yIT31IJu01R      # The "UniPaith Prompt Library" base (already created)
# Table name defaults below already match the base — only override if you rename a table:
# AIRTABLE_PROMPTS_TABLE=Prompts
# AIRTABLE_TEMPLATES_TABLE=Templates
# AIRTABLE_STEPS_TABLE=Template Steps
```

**Create the token** at https://airtable.com/create/tokens with scopes `data.records:read` + `schema.bases:read`, granted access to the **UniPaith Prompt Library** base.

In `infra/ecs.tf`, add them to the ECS task definition environment block (same pattern as other secrets). Both `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID` should go in Secrets Manager; the table name overrides (if any) can be plain env vars.

When either `AIRTABLE_API_KEY` or `AIRTABLE_BASE_ID` is empty, the sync endpoint is fully inert — it returns `{"skipped": "airtable not configured"}` and writes nothing.

---

## 3. Trigger a sync

```bash
curl -X POST https://api.unipaith.co/api/v1/ops/airtable/sync \
  -H "X-Ops-Token: <CRAWLER_OPS_TOKEN>"
```

The response is a summary:

```json
{
  "prompts": { "upserted": 42, "rejected": [] },
  "templates": { "upserted": 8, "rejected": [] }
}
```

`rejected` entries have the shape `{"key": "...", "reason": "..."}` and describe rows that were skipped due to validation failures — the sync always completes, it never aborts on a bad row.

---

## 4. Notes on the seed / Airtable ownership split

- **Seed (in-code CATALOG):** runs on boot via `CatalogService.ensure_seeded()`. Uses `INSERT ... ON CONFLICT DO NOTHING` — it never overwrites existing rows.
- **Airtable:** the sync uses `ON CONFLICT DO UPDATE`, so it does overwrite. Once Airtable has synced a row (setting `airtable_record_id`), the seed will never touch that row again.
- **Net effect:** you can start with the in-code defaults, then gradually move prompts into Airtable one at a time. Only the rows you put in Airtable get Airtable-managed; the rest stay as-is.
