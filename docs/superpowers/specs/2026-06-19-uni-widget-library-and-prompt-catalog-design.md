# Uni Widget Library + Data-Driven Prompt Catalog + Airtable Management — Design

> Companion to [`2026-06-19-uni-chat-tab-redesign-design.md`](./2026-06-19-uni-chat-tab-redesign-design.md),
> which deferred widgets, templates, and backend to a follow-on spec (its §9). This is that spec
> for **widgets + the prompt catalog**. New-session templates remain deferred (next design task).

**Status:** Design approved in brainstorming (visual companion, founder-reviewed mockups). Awaiting spec review → implementation plan.

**Date:** 2026-06-19

---

## 1. Goal

Give every Prompt-Library prompt a **branded input widget** that the student fills in directly, make
that library **editable by non-engineers**, and let the **backend keep reading it the same way it does
today**. Three pieces:

1. **Widget library** — one widget per `ask_kind`, brand-faithful, reusable in **chat, Profile, and
   My Space nudges** (not chat-only). The widget *is* how a student answers a prompt.
2. **Data-driven prompt catalog** — move the hard-coded `enrichment_planner.CATALOG` (Python list) into
   a `prompt_catalog` DB table, so the question set can change without a code deploy.
3. **Airtable as the editor** — the team curates every question, option, tier, and display rule in an
   Airtable base; a sync writes it into `prompt_catalog`; the app renders its own widgets and runs
   matching from the synced DB copy.

**Why not Qualtrics / Google Forms for the student side:** those render their own pages and store data
in their own systems — they cannot render as in-chat/Profile widgets, write to My Space fields or the
matcher, or be driven by Uni conversationally. They are wrong for the **runtime**. They (and Airtable)
*can* serve the **authoring** need — which is why the editing surface is deliberately separated from
the runtime.

---

## 2. The widget library

Each prompt carries an `ask_kind`; the renderer picks one widget. Brand language follows
`Spec/01-brand-tokens.md` (Europa / Typekit `spe3ioy`, paper `#FCFAF2`, cobalt `#2A6BD4` workhorse,
gold ≤10% punctuation, `14/10/pill` radii, no gradient bg except the orb). Approved mockups:
`.superpowers/brainstorm/65894-1781912267/content/widget-demo-prompts.html` (all prompts) and
`chat-with-widgets.html` (in-chat). Apple-OS controls were tried and **rejected** — option cards are
the language.

| `ask_kind` | Widget | Behavior |
|---|---|---|
| `choice` | **Option cards** — whole card tappable, trailing cobalt checkmark; 1 col ≤6 options, 2 cols >6, internal scroll >12 | single-select; auto-saves on tap |
| `multi` | **Checkbox cards** — clean filled-circle/box check (no glow); same column rules | multi-select; auto-saves on change |
| `keywords` | **Keyword picker (Workday-style)** — provided keyword chips the student taps + dashed **"+ Add your own"** to type a custom one | multi-select over a curated vocabulary; for fields where a list beats a blank box |
| `typeahead` | **Quick chips + search** — common values as chips, search field for the long tail | single free-categorical (citizenship / residence); backed by reference data, not free text |
| `scale` | **Tap-meter** — 5 segments + a plain word ("Very"); tap, don't drag | 1–5 importance; **stored 0–10** (×2) onto the matcher weight; no visible "stored as" note |
| `number` | **Stepper** — big − / +, typeable value, optional unit | numeric (GPA, test score) |
| `range` | **Bands + exact** — tappable band chips ("$30k–$50k"), "Set an exact range →" reveals Min/Max | budget; band is primary, exact is opt-in |
| `date` | **Native date** | DOB; no gray helper line |
| `text` | **Textarea + Save** | narrative answers only (work story, a goal) |

**Cross-cutting rules (locked):**
- **Tap-to-save.** Selecting/changing saves on the spot; a quiet green **"Saved"** confirms. Explicit
  Save button only for free `text`. (Brand voice: bare "Saved", no manufactured cheer.)
- **No gray commentary.** No helper subtitles, no "stored as", no field-key tags on the widget. The
  question is the only label.
- **Tap-first.** Anything a student would otherwise type has a tap path (bands, chips, keyword picker,
  steppers); typing is the fallback, never the only door.
- **One descriptor drives it.** A widget renders from `{key, ask_kind, question, options, current_value}`
  and writes back through the enrichment API. The same component renders identically in chat, Profile
  (`EnrichPanel`), and a My Space nudge.

---

## 3. The prompt catalog (expanded)

The library grows from today's 23 fields to **~42 prompts across 8 sections**. New prompts and expanded
option sets are a **proposed catalog expansion** — reconciled to the backend during implementation
(see §6 boundary). Sections are the student-facing grouping; tiers (`essential` / `high_value` /
`standard`) still drive ask/confirm/skip ordering.

| Section | Prompts |
|---|---|
| **Basics** | gender · date_of_birth · nationality(typeahead) · country_of_residence(typeahead) · first_generation · current_education_level |
| **Academics** | gpa(number) · gpa_scale(choice) · tests_taken(multi) · test_scores(number) · english_proficiency(choice) · strongest_subjects(keywords) |
| **Your direction** | target_degree_level(choice) · field_of_interest(choice, ~38) · specialization(keywords) · intended_start(choice) · study_mode(choice) |
| **Experience** | activities(keywords) · work_experience(text) · research_experience(choice) · languages(multi) |
| **Goals** | career_goal(keywords) · goal_after_degree(choice) · goals(text) |
| **Where & how** | preferred_countries(multi) · preferred_setting(multi) · school_size(choice) · institution_type(multi) · climate(choice) · distance_from_home(choice) |
| **What matters most** | weight_cost · weight_outcomes · weight_location · weight_support · weight_flexibility · weight_time_to_degree · weight_research* · weight_campus_life* (all `scale`) · needs(multi) · identity(keywords) |
| **Money** | budget_band(range) · funding_requirement(choice) |

\* `weight_research` and `weight_campus_life` are **new scored weights** — they require new
`StudentPreference.weight_*` columns before they can affect matching (see §6).

Wording changes locked this pass: `country_of_residence` → "Which country do you live in now?",
`nationality` → "Which country are you a citizen of?", `activities` → "Which activities are you part
of?", `identity` → "Which values matter most to you?". Two former `text` fields (`activities`,
`identity`) became `keywords` pickers; `work_experience` and `goals` stay `text` (narrative).

---

## 4. Widgets in context (the runtime)

A widget is the same component everywhere; only the host frame differs.

- **In chat** — Uni leads with the question in her turn; the widget renders **inline in her column** as
  a card. The student answers in place, it saves, Uni continues. (`chat-with-widgets.html`.)
- **In Profile** — the existing `EnrichPanel` (`GET /me/enrichment/next?section=`) renders the same
  widget per scoped field.
- **In a My Space nudge** — a single widget card surfaced where a gap matters.

The descriptor and write path already exist: `GET /me/enrichment/next` and
`POST /me/enrichment/{field}/value` (see the chat-tab spec + `enrichment_service`). Widgets are a
frontend layer over that contract; no new student-facing endpoint is required for rendering/answering.

---

## 5. Data-driven catalog (`prompt_catalog`)

Today the catalog is a Python literal. Move it into a table so any editor can drive it. The backend
consumers (`enrichment_planner`, the Uni agent's tools, the matcher) read from the table via a thin
loader — **same shape they consume today**, so their logic is unchanged.

**Table `prompt_catalog`:**

| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | |
| `key` | text unique | stable field key (e.g. `weight_cost`) |
| `section` | text | student-facing grouping |
| `question` | text | counselor-voiced prompt |
| `ask_kind` | text | choice/multi/keywords/typeahead/scale/number/range/date/text |
| `value_type` | text | categorical/numeric/weight/range/boolean/date/text (drives quantify + write typing) |
| `options` | jsonb | array of labels; null for non-option kinds |
| `tier` | text | essential/high_value/standard |
| `required` | bool | |
| `display_logic` | jsonb | show/hide rules (§7), default `[]` |
| `saves_to` | text | the My Space handler/field the value writes to (usually `key`) |
| `reference_source` | text null | for `typeahead`: which reference list (e.g. `countries`) |
| `sort_order` | int | within section |
| `active` | bool | soft on/off without delete |
| `airtable_record_id` | text null | sync mapping |
| `created_at`/`updated_at` | timestamptz | |

**Loader:** a cached `CatalogService.load()` returns the same list-of-dicts the planner expects
(`key, type, tier, ask_kind, question, options`). `enrichment_planner` keeps its pure functions but
takes the catalog as input instead of importing a module-level constant. Cache invalidates on sync.

**Migration + seed:** hand-written Alembic migration creates `prompt_catalog`; a data migration seeds
it from the current `CATALOG` so behavior is identical on day one (the expansion in §3 lands as
subsequent Airtable edits, gated per the §6 boundary).

---

## 6. Airtable as the editor + sync

**Airtable base — one table, one row per prompt**, columns mirroring `prompt_catalog`
(`key`, `section`, `question`, `ask_kind`, `value_type`, `options` (multi-line / linked), `tier`,
`required`, `display_logic`, `saves_to`, `reference_source`, `sort_order`, `active`). The team edits
here — spreadsheet + form UI, no code.

**Sync (Airtable → `prompt_catalog`):**
```
Airtable (team edits) → "Publish/Sync" → validate → upsert prompt_catalog → invalidate loader cache
                                                              ↓
            enrichment_planner · Uni tools · matcher · widgets all read from the DB copy
```
- A backend job (scheduled poll and/or an Airtable automation webhook → a system-guarded endpoint,
  `X-Ops-Token`) pulls rows, **validates**, and upserts by `key` (+ `airtable_record_id`).
- **Validation rejects a bad edit before it reaches students:** unknown `ask_kind`/`value_type`,
  option-bearing kinds with empty `options`, duplicate `key`, `saves_to` that maps to no known handler,
  display-logic referencing an unknown field.
- **Runtime never calls Airtable** — reliability, speed, and a validation gate. Airtable can be down
  and the app is unaffected.

**The content-vs-wiring boundary (honest limit):**
- **Editable in Airtable, no engineer:** wording, options, order, tier, `required`, `active`,
  display logic — for prompts whose `value_type` already has a backend handler.
- **Still needs an engineer:** a brand-new *scored* field (e.g. `weight_diversity`) needs a new
  `StudentPreference` column + matcher wiring before its value can affect matching. Airtable can hold
  the question; the scoring binding is validated in code. The sync **flags** an unknown `saves_to`
  rather than silently shipping a dead prompt.

---

## 7. Logic, tiers, and saves-to

- **Display logic** — `display_logic` is a list of rules `{field, op, value}` with
  `op ∈ {is, is not, includes, is answered}`; a prompt shows when all rules pass. Evaluated against the
  student's current signal state by the planner/renderer. Example: `institution_type` shows only if
  `study_mode is not Online`. Empty list = always shown.
- **Tier** keeps its current role (ask/confirm/skip ordering; essentials gate matching — Spec 3
  prerequisite). Tier is per-prompt and Airtable-editable.
- **`saves_to`** binds a prompt to the My Space field it writes (usually the `key`). It is the contract
  point validation checks and the reason a prompt can be re-worded without breaking the matcher.

---

## 8. Non-goals / deferred

- **New-session templates** (structured guided flows) — separate design task, founder will sequence.
- **The custom in-app builder** — the Qualtrics-style surface was mocked
  (`prompt-library-builder.html`) and is **superseded by Airtable for now**; revisit only if live
  preview + in-app branching is wanted in-house later.
- **LLM/agent behavior changes** — Uni's prompts/flow are unchanged; she reads the same descriptors.
- **Reference-data editing** (the `countries` list behind `typeahead`) — managed as reference data, not
  in the prompt base.

---

## 9. Open questions / reconciliation

1. **Scored-weight columns** — add `weight_research`, `weight_campus_life` (and any future weights) to
   `StudentPreference` + matcher, or hold those two prompts inactive until then? (Recommend: land the
   columns so the prompts are live.)
2. **Sync cadence** — webhook-on-publish (instant) vs scheduled poll (simple). Recommend webhook +
   a slow poll as backstop.
3. **Versioning / rollback** — keep a `prompt_catalog_versions` snapshot per publish for audit/rollback?
4. **Essentials parity** — the expanded essentials (added `first_generation`,
   `current_education_level`) must not over-gate matching; confirm the essentials set that blocks
   matching stays the true minimum (direction + basic identity).
5. **Typeahead reference source** — confirm `countries` reference list location and that residence /
   citizenship resolve against it (not free text), per the catalog note.

---

## 10. Implementation outline (for the plan)

1. `prompt_catalog` model + migration + seed-from-`CATALOG` data migration (behavior-identical).
2. `CatalogService.load()` (cached) + refactor `enrichment_planner` to take catalog as input; repoint
   Uni tools + matcher reads through it. Tests: planner parity vs the old constant.
3. Frontend widget components per `ask_kind` (the approved language), driven by the descriptor; adopt in
   chat thread, `EnrichPanel`, My Space nudge.
4. Airtable base schema + sync endpoint/job + validation + cache invalidation. Tests: validation
   rejects malformed rows; upsert is idempotent by `key`.
5. `display_logic` evaluation in the planner/renderer. Tests: show/hide rules.
6. Backend reconciliation for the new scored weights (columns + matcher) per §9.1.
