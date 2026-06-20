# Uni Widget Library + Comprehensive Prompt Catalog + Session Templates + Airtable Management — Design

> Companion to [`2026-06-19-uni-chat-tab-redesign-design.md`](./2026-06-19-uni-chat-tab-redesign-design.md),
> which deferred widgets, templates, and backend to a follow-on spec (its §9). This is that spec.

**Status:** Design **approved** in brainstorming (visual companion, founder-reviewed mockups —
"the designs themselves are good now"). The mockups are **concept proofs**; the **real catalog and
template library are deliberately much larger** (see §3, §5). Next: implementation plan.

**Date:** 2026-06-19

---

## 1. Goal

Give every Prompt-Library prompt a **branded input widget** the student fills in directly, make the
library **editable by non-engineers**, let students run **guided templates** that produce real
artifacts, and let the **backend keep reading all of it the same way it does today**. Four pieces:

1. **Widget library** — one widget per `ask_kind`, brand-faithful, reusable in **chat, Profile, and My
   Space nudges**. The widget *is* how a student answers a prompt.
2. **Comprehensive prompt catalog** — **every enrichable prompt carries its own question + widget**
   (not a fixed 42 — see §3). Moved out of code into a `prompt_catalog` DB table so it changes without
   a deploy.
3. **Session templates** — guided **work-orders** (ordered prompt + action steps → an artifact) that
   launch a new session; a large library grouped by topic (§5).
4. **Airtable management** — the team curates prompts **and** templates in Airtable; a sync writes them
   into DB tables; the app renders its own widgets and runs matching from the synced copy.

**Why not Qualtrics / Google Forms for the student side:** they render their own pages and store data in
their own systems — they cannot render as in-chat/Profile widgets, write to My Space fields or the
matcher, or be driven by Uni. Wrong for the **runtime**; fine as an **authoring** idea — which is why
Airtable (authoring) is separated from the app (runtime).

---

## 2. The widget library

Each prompt carries an `ask_kind`; the renderer picks one widget. Brand language per
`Spec/01-brand-tokens.md` (Europa / Typekit `spe3ioy`, paper `#FCFAF2`, cobalt `#2A6BD4` workhorse,
gold ≤10% punctuation, `14/10/pill` radii, no gradient bg except the orb). Approved mockups:
`.superpowers/brainstorm/65894-1781912267/content/widget-demo-prompts.html` and `chat-with-widgets.html`.
Apple-OS controls were tried and **rejected** — option cards are the language.

| `ask_kind` | Widget | Behavior |
|---|---|---|
| `choice` | **Option cards** — whole card tappable, trailing cobalt checkmark; 1 col ≤6 options, 2 cols >6, internal scroll >12 | single-select; auto-saves on tap |
| `multi` | **Checkbox cards** — clean filled box check (no glow); same column rules | multi-select; auto-saves |
| `keywords` | **Keyword picker (Workday-style)** — provided keyword chips + dashed "+ Add your own" | multi over a curated vocabulary; for fields where a list beats a blank box |
| `typeahead` | **Quick chips + search** — common values as chips, search for the long tail | single free-categorical (citizenship / residence); reference-backed, not free text |
| `scale` | **Tap-meter** — 5 segments + a plain word; tap, don't drag | 1–5 importance; **stored 0–10** (×2) onto the matcher weight; no visible "stored as" note |
| `number` | **Stepper** — big − / +, typeable, optional unit | numeric (GPA, test score) |
| `range` | **Bands + exact** — tappable band chips; "Set an exact range →" reveals Min/Max | budget; band primary, exact opt-in |
| `date` | **Native date** | DOB; no gray helper line |
| `text` | **Textarea + Save** | narrative answers only (work story, a goal) |

**Cross-cutting rules (locked):** tap-to-save (quiet green "Saved"; explicit Save only for free `text`);
**no gray commentary** (no helper subtitles, no "stored as", no field-key tags); **tap-first** (typing is
always a fallback); **one descriptor** `{key, ask_kind, question, options, current_value}` drives the
**same** component in chat, Profile (`EnrichPanel`), and a My Space nudge.

---

## 3. The prompt catalog — comprehensive

The library is **not a fixed 42**. The principle: **every enrichable prompt carries its own curated,
counselor-voiced question + widget** — one question for every field the profile, My Space, and matcher
can hold. The ~42 in `widget-demo-prompts.html` is an **illustrative slice** that proves the `ask_kind`s
and the 8 sections; the **real catalog is much larger** and is assembled, during implementation, from
every existing source of prompt-able fields, then maintained/expanded by the team in Airtable:

| Source | Contributes |
|---|---|
| `enrichment_planner.CATALOG` (today's 23) | the essentials + high-value + standard baseline |
| This session's expansion (the §3.1 table) | ~42 across 8 sections, with the new scored weights |
| `profile_standard` manifest (MIT / Sloan / MBAn 3-level canonical) | the full profile field set + per-level depth — see [[project_profile_standard_enrichment]] |
| All My Space / profile fields | demographics · **each** academic record field · **each** test · activities · work history · languages · goals (academic/social/personal) · needs (Maslow 5) · identity (values/worldview/self-awareness) · strategy inputs |
| `StudentPreference` weights | every `weight_*` dimension as a `scale` prompt |
| Behavioral Prompt Library + Story Bank (Spec 42) | behavioral / story prompts |
| Major-specific catalog (Spec 43, 15 tracks) | discipline-specific prompts surfaced by `field_of_interest` |

At full coverage this is **hundreds** of prompts (per-record and major-specific multiply it). The build
produces a `prompt_catalog` row — `question · ask_kind · options · value_type · tier · saves_to` — for
**every** such field; the team then curates/expands in Airtable. The 8 sections
(Basics · Academics · Your direction · Experience · Goals · Where & how · What matters most · Money)
are the student-facing grouping and hold as the catalog grows.

### 3.1 Illustrative slice (the demo's ~42)

| Section | Prompts |
|---|---|
| **Basics** | gender · date_of_birth · nationality(typeahead) · country_of_residence(typeahead) · first_generation · current_education_level |
| **Academics** | gpa · gpa_scale · tests_taken(multi) · test_scores · english_proficiency · strongest_subjects(keywords) |
| **Your direction** | target_degree_level · field_of_interest(~38) · specialization(keywords) · intended_start · study_mode |
| **Experience** | activities(keywords) · work_experience(text) · research_experience · languages(multi) |
| **Goals** | career_goal(keywords) · goal_after_degree · goals(text) |
| **Where & how** | preferred_countries · preferred_setting · school_size · institution_type · climate · distance_from_home |
| **What matters most** | weight_cost · weight_outcomes · weight_location · weight_support · weight_flexibility · weight_time_to_degree · weight_research\* · weight_campus_life\* · needs(multi) · identity(keywords) |
| **Money** | budget_band(range) · funding_requirement |

\* new scored weights — need new `StudentPreference.weight_*` columns before they affect matching (§10).
Wording locked: `country_of_residence`="Which country do you live in now?", `nationality`="Which country
are you a citizen of?". `activities` and `identity` became `keywords`; `work_experience`/`goals` stay `text`.

---

## 4. Widgets in context (the runtime)

Same component everywhere; only the host frame differs.

- **In chat** — Uni leads with the question; the widget renders **inline in her turn** as a card; the
  student answers in place, it saves, Uni continues. (`chat-with-widgets.html`.)
- **In Profile** — the existing `EnrichPanel` (`GET /me/enrichment/next?section=`) renders the widget.
- **In a My Space nudge** — a single widget card where a gap matters.

Write path exists: `GET /me/enrichment/next` + `POST /me/enrichment/{field}/value`. Widgets are a
frontend layer over that contract; no new student-facing endpoint is needed to render/answer.

---

## 5. Session templates (guided work-orders)

A template is a **guided work-order**: Uni runs an ordered set of steps — some are **widget-fills** (a
prompt from the catalog), some are **actions** (a code-backed thing Uni does) — ending in an **artifact
saved to My Space**. Not a rigid wizard; counselor-led, with a visible **per-session work-order spine**.
Mockup: `session-templates.html` (gallery + a run); fit and odds render as **separate word tags** (a
reach can still be a great fit), per the chat-tab spec.

**Comprehensive, grouped by topic.** Templates group by the **8 white-paper topics** (= the
session-browser folders): Profile · Goals · Needs · Strategy · Schools · Connect · Prepare · Manage. The
mockup shows **~19 as a concept proof**; the **real library is much larger** — several per topic, plus
**context-spawned** templates (e.g. "Explore *this* school" launched from a Discover card → a session
filed under Schools). Free starts still work and are auto-categorized.

**Anatomy (data, not code):**
- **Template** — `key · title · topic · stage · outcome · icon · sort_order · active`
- **Template Step** (ordered, linked to a template) — `type ∈ {prompt, action} · prompt_key | action_key · short label`
- **Action** — a code-backed capability a step can run: `build_school_list`, `generate_strategy`,
  `compare_schools`, `draft_feedback`, `find_events`, `build_checklist`, … Read-only catalog; **a new
  action needs engineering**, then editors can use it.

**Runtime:** picking a template opens a session (filed under its topic folder), renders the spine, and
walks the steps — `prompt` steps render the inline widget, `action` steps run the capability and render
the artifact. Artifacts land in My Space.

---

## 6. Data-driven tables

Move the catalog and templates out of code into tables; the backend consumers
(`enrichment_planner`, Uni's tools, the matcher, the template runner) read via thin cached loaders —
same shapes they consume today, so their logic is unchanged. Hand-written Alembic migrations; data
migration seeds `prompt_catalog` from the current `CATALOG` (behavior-identical on day one).

**`prompt_catalog`** — `id · key(unique) · section · question · ask_kind · value_type · options(jsonb) ·
tier · required · display_logic(jsonb) · saves_to · reference_source · sort_order · active ·
airtable_record_id · timestamps`.

**`session_template`** — `id · key(unique) · title · topic · stage · outcome · icon · sort_order ·
active · airtable_record_id · timestamps`.

**`session_template_step`** — `id · template_id(fk) · step_order · step_type('prompt'|'action') ·
prompt_key(null) · action_key(null) · label · airtable_record_id`. Exactly one of `prompt_key` /
`action_key` set.

**`action_catalog`** — code-registered list of runnable actions (key + handler); the sync validates
template steps against it but it is **not** Airtable-editable.

**Loaders:** `CatalogService.load()` and `TemplateService.load()` (cached, invalidated on sync) return
the shapes the planner / template runner expect. `enrichment_planner` is refactored to take the catalog
as input instead of importing a module-level constant; planner-parity test vs the old constant.

---

## 7. Airtable as the editor + sync

**Airtable base — linked tables:**
- **Prompts** — one row per prompt, columns mirroring `prompt_catalog`.
- **Actions** — read-only list of code-backed capabilities (editors pick from these).
- **Templates** — one row per template (title · topic · stage · outcome · icon · active).
- **Template Steps** — one row per step, **linked** to a Template and to a Prompt **or** an Action,
  with order + label. Editing a template = reorder/add/remove its linked steps; each step picks a Prompt
  or an Action from a dropdown.

**Sync (Airtable → DB):**
```
Airtable (team edits) → "Publish/Sync" → validate → upsert prompt_catalog + session_template(_step)
                                                          → invalidate loader caches
                                                                  ↓
        enrichment_planner · Uni tools · matcher · template runner · widgets all read the DB copy
```
- Backend job (webhook on publish + slow poll backstop) pulls rows, **validates**, upserts by `key`.
- **Validation rejects bad edits before students see them:** unknown `ask_kind`/`value_type`;
  option-kinds with empty `options`; duplicate `key`; `saves_to` mapping to no known handler; a template
  step referencing an unknown prompt-key or action-key; display-logic referencing an unknown field.
- **Runtime never calls Airtable** — reliability, speed, a validation gate.

**Content-vs-wiring boundary (honest limit):**
- **No-code in Airtable:** prompt wording / options / order / tier / `required` / `active` / display
  logic; template title / topic / outcome / step order / step labels / which prompts a template uses /
  which **existing** actions it runs.
- **Needs an engineer:** a brand-new *scored* field (new matcher column) and a brand-new **action**
  (new code capability). Airtable holds the question / the flow; the scoring + capabilities stay
  validated in code. The sync **flags** an unknown `saves_to` / `action_key` rather than shipping a
  dead prompt or step.

---

## 8. Logic, tiers, and saves-to

- **Display logic** — `display_logic` is a list of `{field, op, value}` rules
  (`op ∈ {is, is not, includes, is answered}`); shown when all pass; evaluated against the student's
  current signal state. Empty = always shown.
- **Tier** keeps its role (ask/confirm/skip ordering; essentials gate matching — Spec 3 prerequisite).
- **`saves_to`** binds a prompt to the My Space field it writes (usually the `key`) — the contract point
  validation checks and why a prompt can be re-worded without breaking the matcher.

---

## 9. Non-goals / deferred

- **The custom in-app builder** — the Qualtrics-style surface was mocked (`prompt-library-builder.html`)
  and is **superseded by Airtable for now**; revisit only if live preview + in-app branching is wanted
  in-house later.
- **LLM/agent behavior changes** — Uni's prompts/flow are unchanged; she reads the same descriptors.
- **Reference-data editing** (the `countries` list behind `typeahead`) — managed as reference data.

---

## 10. Open questions / reconciliation

1. **Scored-weight columns** — add `weight_research`, `weight_campus_life` (and future weights) to
   `StudentPreference` + matcher, or hold those prompts inactive until then? (Recommend: land the
   columns so the prompts are live.)
2. **Full-catalog assembly** — confirm the source priority when the same field appears in more than one
   source (e.g. `CATALOG` vs `profile_standard`); the canonical question wins, dedup by `key`.
3. **Sync cadence + versioning** — webhook-on-publish + slow poll; keep a per-publish snapshot for
   audit/rollback?
4. **Essentials parity** — the expanded essentials must not over-gate matching; confirm the essentials
   set that blocks matching stays the true minimum (direction + basic identity).
5. **Action surface** — finalize the initial `action_catalog` (which capabilities exist) so templates
   have a complete vocabulary to compose from.

---

## 11. Implementation outline (for the plan)

1. `prompt_catalog` model + migration + seed-from-`CATALOG` data migration (behavior-identical).
2. `CatalogService.load()` (cached) + refactor `enrichment_planner` to take the catalog as input;
   repoint Uni tools + matcher reads through it. Test: planner parity vs the old constant.
3. **Full-catalog assembly** — generate `prompt_catalog` rows (question + ask_kind + options + saves_to)
   for every field across the §3 sources; dedup by `key`; seed.
4. Frontend widget components per `ask_kind` (the approved language), driven by the descriptor; adopt in
   the chat thread, `EnrichPanel`, and My Space nudge.
5. `session_template` / `session_template_step` / `action_catalog` models + migrations; `TemplateService`
   loader; the template runner (spine + step walk + artifact) in the chat tab; seed the initial library.
6. Airtable base (Prompts · Actions · Templates · Template Steps) + sync endpoint/job + validation +
   cache invalidation. Tests: validation rejects malformed rows/steps; upsert idempotent by `key`.
7. `display_logic` evaluation in the planner/renderer. Test: show/hide rules.
8. Backend reconciliation for the new scored weights (columns + matcher) per §10.1.
