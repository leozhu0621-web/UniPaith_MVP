# Airtable Prompt Library Setup

This document tells you exactly what Airtable base to create and what env vars to set so the sync endpoint goes live. Once configured, `POST /api/v1/ops/airtable/sync` (X-Ops-Token guarded) pulls records from Airtable and upserts them into `prompt_catalog` and `session_templates` / `session_template_steps`.

---

## 1. Create the Airtable base

Create a new base in your Airtable account. Name it anything you like (e.g. "UniPaith Prompt Library"). It needs **three tables**:

### Table: Prompts

Maps to `prompt_catalog`. Column names must match exactly (case-sensitive):

| Column name | Type | Notes |
|---|---|---|
| `key` | Single line text | **Required. Unique.** Snake_case, e.g. `career_goal` |
| `section` | Single line text | Display group, e.g. `Goals`, `Basics` |
| `question` | Long text | The counselor-voiced question shown to the student |
| `ask_kind` | Single line text | One of: `choice`, `multi`, `keywords`, `typeahead`, `scale`, `number`, `range`, `date`, `text` |
| `value_type` | Single line text | One of: `categorical`, `numeric`, `boolean`, `text`, `date`, `range`, `multi`, `weight` |
| `options` | Long text | JSON array string for `choice`/`multi`/`keywords`, e.g. `["Option A","Option B"]`. Leave blank for other ask_kinds |
| `tier` | Single line text | `essential`, `high_value`, or `standard` |
| `required` | Checkbox | Whether the field is required |
| `display_logic` | Long text | JSON array of display conditions. Leave blank for always-shown |
| `saves_to` | Single line text | **Required.** The My Space field key this answer writes to (usually same as `key`) |
| `reference_source` | Single line text | Optional. `countries` for nationality/country fields; blank otherwise |
| `sort_order` | Number | Display ordering within the section (integer) |
| `active` | Checkbox | Unchecked = hidden from the student UI |

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

Maps to `session_templates`:

| Column name | Type | Notes |
|---|---|---|
| `key` | Single line text | **Required. Unique.** Snake_case, e.g. `sharpen_strategy` |
| `title` | Single line text | **Required.** Human-readable title |
| `topic` | Single line text | **Required.** e.g. `profile`, `goals`, `strategy`, `schools` |
| `stage` | Single line text | **Required.** `discovery`, `recommendation`, or `application` |
| `outcome` | Single line text | **Required.** One-line description of what the template produces |
| `icon` | Single line text | **Required.** Icon key, e.g. `pen`, `flag`, `compass`, `list` |
| `sort_order` | Number | Integer sort order in the template picker |
| `active` | Checkbox | Unchecked = hidden from students |

---

### Table: Template Steps

Maps to `session_template_steps`. Each row is one step in a template:

| Column name | Type | Notes |
|---|---|---|
| `template_key` | Single line text | The `key` of the parent template (e.g. `sharpen_strategy`). **OR** use the Airtable linked-record field `Template` (see below) |
| `Template` | Linked record → Templates | Alternative to `template_key`. The sync supports either pattern |
| `step_type` | Single line text | **Required.** `prompt` or `action` |
| `prompt_key` | Single line text | Required when `step_type = prompt`. Must match a key in `prompt_catalog` |
| `action_key` | Single line text | Required when `step_type = action`. Must be one of the registered action keys (see `services/chat/template_actions.py`) |
| `label` | Single line text | Short label shown on the step card |
| `step_order` | Number | Integer ordering within the template |

**Exactly one** of `prompt_key` / `action_key` must be set per row.

**Valid action keys** (from `ACTION_CATALOG`):
`build_school_list`, `generate_strategy`, `compare_schools`, `draft_feedback`, `interview_practice`, `build_checklist`, `find_events`, `generate_needs_map`, `generate_goal_stack`

**Steps replace on every sync:** when a template is synced, its existing steps in the DB are deleted and replaced with the Airtable rows. This keeps ordering clean. The template itself is upserted (no data loss to template metadata).

---

## 2. Set environment variables

Add these to AWS Secrets Manager (or your `.env` for local dev):

```
AIRTABLE_API_KEY=pat...          # Your personal access token from airtable.com/account
AIRTABLE_BASE_ID=app...          # Found in the API URL: airtable.com/app.../...
AIRTABLE_PROMPTS_TABLE=Prompts   # Default — change if you named the table differently
AIRTABLE_TEMPLATES_TABLE=Templates
AIRTABLE_STEPS_TABLE=Template Steps
```

In `infra/ecs.tf`, add them to the ECS task definition environment block (same pattern as other secrets). Both `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID` should go in Secrets Manager; the table name overrides can be plain env vars.

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
