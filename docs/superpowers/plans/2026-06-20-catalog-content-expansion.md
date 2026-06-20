# Prompt Catalog Content Expansion + keyword/typeahead widgets — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:test-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** Grow the Prompt Library from 23 to ~40 prompts (the founder's "every prompt needs its question / a lot larger"), add the `keyword` and `typeahead` ask-kinds end-to-end, and fix a latent multi-enrichment bug — all on the now-data-driven catalog.

**Architecture:** The catalog is seeded from `enrichment_planner.CATALOG` (insert-if-absent by `CatalogService.ensure_seeded`). New fields are added to that constant + `CatalogService` section/reference maps; a one-time reset migration clears the seed-managed rows (`airtable_record_id IS NULL`) so the startup seed re-materializes the new wording/ask-kinds. `keyword`/`typeahead` are added to the backend value-typing and the frontend `AskKind` + widgets.

**Tech Stack:** Python 3.12 · SQLAlchemy 2 async · Alembic · pytest-asyncio · React 19 · TS · vitest.

**Scope:** content expansion + keyword/typeahead. **OUT of scope:** the two new *scored* weights (`weight_research`, `weight_campus_life`) and their matcher wiring — a separate unit (they need new `StudentPreference` columns + matcher-blend changes). Do NOT add them here.

**Tiers:** Keep the essentials set unchanged (the original 6: gender, nationality, date_of_birth, country_of_residence, target_degree_level, field_of_interest). **Every new field is `high_value` or `standard` — none essential** (must not change the match gate).

---

## The data (authoritative)

### New fields to ADD to `CATALOG` (each is a dict `{"key","type","tier","ask_kind","question","options"?}`)

```
# Basics
first_generation        categorical standard  choice   "Would you be the first in your family to go to college?"  ["Yes","No","Not sure"]
current_education_level categorical standard  choice   "Where are you in your education right now?"  ["In high school","Finished high school","In a bachelor's degree","Finished a bachelor's","In a graduate degree","Working professional","Taking a gap year"]
# Academics
gpa_scale               categorical high_value choice  "What scale is that GPA on?"  ["4.0","4.3","4.5","5.0","10.0","Percentage (out of 100)","UK honours","Other"]
tests_taken             multi       high_value multi   "Which tests have you taken, or plan to?"  ["SAT","ACT","PSAT","AP exams","IB","A-Levels","TOEFL","IELTS","Duolingo English","GRE","GMAT","LSAT","MCAT","None yet"]
english_proficiency     categorical standard  choice   "How comfortable are you with English?"  ["Native speaker","Fluent","Advanced","Intermediate","Beginner"]
strongest_subjects      multi       standard  keywords "Which subjects are you strongest in?"  ["Math","Physics","Chemistry","Biology","Computer science","Economics","History","English / writing","Foreign languages","Art","Music","Business","Psychology","Political science"]
# Your direction
specialization          multi       standard  keywords "Any specific focus within that?"  ["Machine learning","Artificial intelligence","Cybersecurity","Data analytics","Robotics","Human–computer interaction","Renewable energy","Quantitative finance","Public policy","Neuroscience","Biotech","UX design"]
intended_start          categorical standard  choice   "When do you want to start?"  ["Fall 2026","Spring 2027","Fall 2027","2028 or later","Flexible"]
study_mode              categorical standard  choice   "How do you want to study?"  ["On campus","Online","Hybrid","No preference"]
# Experience
research_experience     categorical standard  choice   "Have you done academic research?"  ["Yes — published","Yes — assisted a project","A little","Not yet"]
# Goals
career_goal             multi       high_value keywords "What kind of work do you see yourself in?"  ["Software / tech","Finance","Consulting","Medicine / healthcare","Research / academia","Law","Engineering","Entrepreneurship","Design / creative","Public service / policy","Education","Marketing","Data / AI","Still exploring"]
goal_after_degree       categorical standard  choice   "After this degree, what's the plan?"  ["Start my career","Go further (PhD / more study)","Start a business","Return to my current job","Still figuring it out"]
# Where & how
preferred_setting       multi       standard  multi    "What kind of place feels right?"  ["Big city","College town","Suburban","Rural","By the coast","No preference"]
school_size             categorical standard  choice   "What size of school suits you?"  ["Small (under 5,000)","Medium (5,000–15,000)","Large (over 15,000)","No preference"]
institution_type        multi       standard  multi    "What kinds of schools interest you?"  ["Public university","Private university","Liberal arts college","Research university","Ivy / highly selective","Technical / specialized","Community college","Online-first","Religiously affiliated"]
climate                 categorical standard  choice   "Any climate preference?"  ["Warm year-round","Mild","Four seasons","Cold is fine","No preference"]
distance_from_home      categorical standard  choice   "How far from home are you open to going?"  ["Stay close to home","Within my country","Within my region","Anywhere in the world"]
```

### EXISTING fields to CHANGE in `CATALOG`

```
nationality           ask_kind choice→typeahead  question "Which country are you a citizen of?"  (options stays None)
country_of_residence  ask_kind choice→typeahead  question "Which country do you live in now?"   (options stays None)
activities            type text→multi  ask_kind text→keywords  question "Which activities are you part of?"
                      options ["Robotics","Debate","Student government","Volunteering","Sports team","Music & arts","Theater / drama","Research","Entrepreneurship","Coding / hackathons","Journalism / writing","Model UN","Tutoring / mentoring","Sustainability","Cultural / religious group"]
identity              type text→multi  ask_kind text→keywords  question "Which values matter most to you?"
                      options ["Curiosity","Integrity","Community","Ambition","Creativity","Resilience","Independence","Compassion","Excellence","Adventure","Fairness","Growth","Faith","Family","Service"]
target_degree_level   options → ["Associate","Bachelor's","Master's","MBA","Ph.D.","Professional (JD / MD / etc.)","Certificate","Diploma","Exchange / non-degree"]
field_of_interest     options → ["Computer science","Data science & AI","Software engineering","Electrical engineering","Mechanical engineering","Civil engineering","Biomedical engineering","Business & management","Finance","Accounting","Marketing","Economics","Biology & life sciences","Chemistry","Physics","Mathematics & statistics","Environmental science","Medicine","Nursing","Public health","Pharmacy","Psychology","Sociology","Political science","International relations","Law","Education","Communications & media","Journalism","English & literature","History","Philosophy","Linguistics & languages","Architecture","Art & design","Music & performing arts","Film & media","Something else"]
funding_requirement   options → ["Need a full scholarship","Need significant aid","Some aid would help","I can mostly self-fund","Loans are an option","Not sure yet"]
```

### `CatalogService` maps to update
`_SECTION_BY_KEY`: add every new key with its section (Basics/Academics/Your direction/Experience/Goals/Where & how). `_REFERENCE_SOURCE` already has nationality+country_of_residence → "countries" (keep). Section names already present: Basics, Academics, Your direction, Experience, Goals, Where & how, What matters most, Money.

---

### Task 1: Expand the catalog (backend)

**Files:** Modify `unipaith-backend/src/unipaith/services/enrichment_planner.py` (CATALOG), `unipaith-backend/src/unipaith/services/catalog_service.py` (_SECTION_BY_KEY). Create `unipaith-backend/alembic/versions/promptcat2_reseed.py`. Test: `unipaith-backend/tests/test_catalog_content.py`.

- [ ] **Step 1 — failing test** (`test_catalog_content.py`): after `CatalogService.ensure_seeded` on a fresh DB, `load()` returns ≥ 40 prompts; assert specific new keys present (e.g. `institution_type`, `gpa_scale`, `career_goal`) with the right `ask_kind`; assert `activities`/`identity` are now `ask_kind == "keywords"`; assert `nationality` is `ask_kind == "typeahead"`; assert `essentials_present` still keyed on exactly the original 6 essentials.
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement:** add the new dicts to `CATALOG` (in their section order), apply the existing-field changes, extend `_SECTION_BY_KEY` for all keys. Keep all new fields `high_value`/`standard`.
- [ ] **Step 4 — reset migration** `promptcat2_reseed` (down_revision = current head `bupromptmerge1`; re-point if a newer head landed): `op.execute("DELETE FROM prompt_catalog WHERE airtable_record_id IS NULL")` so the startup `ensure_seeded` re-materializes the new content. `_has("prompt_catalog")`-guard the delete; `downgrade` = pass. Pragma-allowlist the revision lines.
- [ ] **Step 5 — run the test + `tests/test_catalog_service.py` + `tests/test_enrichment_planner.py`; all green. `alembic heads` single.** Commit.

### Task 2: keyword/typeahead value typing (backend)

**Files:** Modify `unipaith-backend/src/unipaith/services/enrichment_service.py`. Test: `unipaith-backend/tests/test_enrichment_write_typing.py` (extend).

- [ ] **Step 1 — failing tests:** `set_value(student, "strongest_subjects", ["Math","Custom topic"])` SUCCEEDS (keywords allow custom values beyond the suggestion list) and stores a list; `set_value(student, "nationality", "Canada")` SUCCEEDS (typeahead = free string, no taxonomy rejection); `set_value(student, "needs", "not a list")` still 400 (choice/multi taxonomy unchanged).
- [ ] **Step 2 — run, expect fail** (keywords currently rejects custom via taxonomy).
- [ ] **Step 3 — implement:** gate taxonomy validation on `ask_kind in ("choice","multi")` (NOT on `options` presence), so `keywords` skips taxonomy (curated suggestions + custom) while still being a list, and `typeahead` (options None) stays free. Keep weight + choice/multi behavior identical.
- [ ] **Step 4 — run the typing tests + catalog tests; green.** Commit.

### Task 3: keyword + typeahead widgets (frontend) + fix multi-as-list

**Files:** Modify `frontend/src/api/enrichment.ts` (AskKind), `frontend/src/components/student/EnrichWidget.tsx`, `frontend/src/pages/student/discover/AnswerChoices.tsx`. Test: `frontend/src/test/answerChoices.test.tsx` (extend) + a new `enrichKeyword.test.tsx`.

- [ ] **Step 1 — failing tests:** (a) a keyword widget renders the suggestion chips + an "add your own" input, lets you pick chips + add a custom one, and submits a **string array**; (b) a typeahead widget renders quick country chips + a search and submits the chosen string; (c) **multi enrichment submits an array, not a joined string** (the latent bug — backend `is_multi` expects a list).
- [ ] **Step 2 — run, expect fail.**
- [ ] **Step 3 — implement:** add `"keywords" | "typeahead"` to `AskKind`. In `EnrichWidget.SignalInput`, render `keywords` → a keyword picker (chips from `item.options` toggling selection + a text input to add custom → submit `string[]`), `typeahead` → quick chips (a small bundled common-countries set) + a search input over a bundled countries list → submit the chosen `string`. For **multi**, submit a `string[]` to the backend (not the conversation's joined string): give `AnswerChoices` an `asList` prop (mirrors `numeric` for scale) and have `EnrichWidget` pass it for `multi`; the conversation path keeps the joined string. Use the locked brand tokens (secondary=cobalt, the chip styles from Plan 2).
- [ ] **Step 4 — run `vitest run` (full), `tsc -p tsconfig.app.json --noEmit`, `eslint --max-warnings=0`; all green.** Commit.

---

## Self-review
- **Spec coverage:** §3 (comprehensive catalog — this lands the designed ~40 slice + the keyword/typeahead kinds), §2 (the two remaining widgets). The two scored weights + matcher are explicitly deferred.
- **No essentials drift:** new fields are all high_value/standard; Task-1 test pins essentials to the original 6.
- **Behavior:** reset migration + insert-if-absent seed keeps the data-driven contract; keyword allows custom, typeahead free, choice/multi taxonomy unchanged.
