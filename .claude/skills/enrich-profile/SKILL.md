---
name: enrich-profile
description: >
  Autonomously develop the UniPaith profile database toward the gold standard,
  one verified unit of work per run. Use when asked to enrich a profile, raise a
  school/program/institution to standard, or as a scheduled routine that keeps
  growing the database. Picks the next-best target by conformance, researches
  missing fields from authoritative sources, VERIFIES (never fabricates — omits
  if unverifiable), writes the data + an idempotent migration, and ships it live.
---

# Enrich a profile to the gold standard

You develop the UniPaith profile database so every institution / school / program
profile reaches the **gold standard** defined by the MIT / Sloan / MBAn reference
instance — with **real, cited data and zero fabrication**. This skill is the
complete operating manual for one run. It is designed to be driven by a scheduled
Claude routine; the human controls the frequency, you do exactly one clean,
shippable unit of work each run.

## The one inviolable rule

**Never fabricate. Ever.** A field ships only when it is verified against
authoritative sources and carries a citation. If you cannot verify it, **omit it**
(record it in the profile's `_standard.omitted`) — an honestly-empty field is
correct; a guessed one is a defect. Extra research tokens are acceptable; a wrong
fact on a student-facing page is not.

## What "the standard" is (read these first)

The standard is machine-checkable and lives in the repo:

- **`unipaith-backend/src/unipaith/profile_standard/manifest.py`** — `STANDARD_VERSION`
  + the ordered `Section`/`Field` blueprint for each level (`institution`, `school`,
  `program`). Each `Field` has a dotted `path` into the profile's persisted shape,
  a `required` flag, a `sourcing` rule, and an `enrich` flag (`False` = inherited
  from a parent or render-only → not this profile's job).
- **`unipaith-backend/src/unipaith/profile_standard/conformance.py`** —
  `check_conformance(level, snapshot, profile_version=) -> {missing_sections, missing_fields, stale}`.
  This tells you exactly what a profile is missing.
- **`unipaith-backend/src/unipaith/profile_standard/playbook.md`** — the per-field
  **authoritative source** + the verification-gate rules. This is your source map.
- **`unipaith-backend/src/unipaith/services/profile_enrichment/gate.py`** — the
  deterministic verification rules you must satisfy (`verify(sourcing, evidence)`).
- **The gold reference:** `unipaith-backend/src/unipaith/data/mit_profile.py`. This
  is what a fully-enriched profile looks like — copy its *shape*, never its values.
- **Design + plans:** `docs/superpowers/specs/2026-06-09-profile-standard-and-enrichment-design.md`,
  `docs/superpowers/specs/2026-06-10-profile-standard-completion.md`,
  `docs/superpowers/plans/2026-06-10-mass-enrichment-plan.md`.

A profile is **gold** when `check_conformance` returns `conformant: True` against
the current `STANDARD_VERSION`.

## Per-run algorithm

Do these in order. Bound the run to **one profile** (or a small set of fields)
so each run is a clean, shippable, reviewable unit.

### 1. Health check (don't build on a broken base)
```bash
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_profile_standard.py tests/test_profile_enrichment.py -q
cd ../frontend && npm run build >/dev/null 2>&1 && echo FE_OK
```
Confirm the working tree is clean and `main` is healthy before starting.

### 2. Pick the target (conformance-driven)
List the fleet and find the highest-value gap. Targets are the institution profile
modules in `unipaith-backend/src/unipaith/data/*_profile.py` (and any institutions
seeded in prod). For each candidate, build a **snapshot** of its persisted shape and
run `check_conformance`. Prioritize, in order:
1. **Parent before child** — never enrich a school/program whose parent institution
   is below standard (schools inherit institution stats; programs inherit the
   institution photo).
2. **Profiles students actually hit** — higher saved-school / match / view counts first.
3. **Lowest conformance first** — biggest gap-closing per unit of work.
4. **Field priority** — deterministic federal-dataset fields first (cheapest,
   safest), then first-party official pages, then `authoritative_2x` reviews last.

Pick **one** target + the specific missing required fields to fill this run. If the
whole fleet is already conformant at the current `STANDARD_VERSION`, report that and
exit — there is nothing to do.

> To build a snapshot for an existing institution module: import it and read the
> same constants its `apply()` writes (e.g. `RANKING_DATA`, `SCHOOL_OUTCOMES`,
> `_OUTCOMES_BY_SLUG[slug]`, `_COST_BY_SLUG[slug]`, `_REQ_*`, `_TRACKS_BY_SLUG`,
> `_CLASS_PROFILE_BY_SLUG`, `_FACULTY_BY_SLUG` → `faculty_contacts`,
> `_REVIEWS_BY_SLUG` → `external_reviews`). See `tests/test_profile_standard.py`
> for the exact snapshot shape per level.

### 3. Research each missing field (authoritative sources only)
Use `playbook.md`'s source map to know **where** each field comes from, then use
your web tools (WebSearch / WebFetch) to find and READ the authoritative source.
Source map (summary):

| Field group | Authoritative source | Gate tier |
|---|---|---|
| Report-card stats, financial aid, demographics, test scores | College Scorecard (by UNITID) + IPEDS; cross-check Common Data Set | `authoritative_2x` / `first_party` |
| Median earnings 10yr; program Field-of-Study outcomes | Scorecard (+ institution outcomes page) | `authoritative_2x` |
| Program career outcomes (salary dist, employers, industries, conditions) | The institution's **career-office Employment Report** (PDF) for the most recent class | `first_party` cited |
| Tuition / cost breakdown / fees | Registrar / bursar / financing page | `first_party` cited |
| Rankings (QS / THE / U.S. News) | Each ranking body's own page | `first_party` per body |
| Carnegie / accreditor | Carnegie listing / regional accreditor | `first_party` |
| Admissions (materials, deadlines, recs, test policy, international/visa/OPT) | Official how-to-apply page | `first_party` cited |
| Class profile (cohort, intl%, GPA/GRE/GMAT, work-exp) | Program Class Profile page | `first_party` cited |
| Faculty roster / tracks-curriculum | Faculty directory / curriculum page | `official_or_curated`, verbatim |
| Recognition / scale (Nobel, endowment, ratio, acres) | Institution Facts / news pages | `first_party` |
| Reviews ("what students say") | ≥2 reputable third-party guides, paraphrased + attributed | `authoritative_2x` |
| Feeds (Updates + Events) | Institution's own RSS / iCal / verified socials | `first_party` |

For statistical fields (outcomes especially), capture the report's **conditions /
methodology** verbatim (knowledge rate, sample size, base-vs-total comp, reporting
window, reporting standard) — students must see the caveats, exactly as the MBAn
outcomes do.

### 4. Verify (the gate — do this for every value)
A value may ship **only if all hold**:
1. `first_party` fields: one designated official source. `authoritative_2x`: **≥2
   independent (distinct-domain) authoritative sources that agree** (numbers within
   ~5%).
2. A **citation** is attached: `source` (label) + a resolvable `source_url`.
3. Numbers **cross-check** across sources.
4. Re-read the cited source text and confirm it actually supports the value (do this
   carefully, more than once for contested numbers — extra tokens are fine).

If any fails → **omit** the field and add its path to the profile's
`_standard.omitted`. Do not guess, round into a stronger claim, or infer.

### 5. Write the data (conform to the manifest shape)
Edit the institution's profile module (`data/<institution>_profile.py`), adding the
verified, cited values in the manifest's shape — mirror `mit_profile.py` exactly
(e.g. add a `_OUTCOMES_BY_SLUG[slug]` entry with `median_salary`, `salary_25th/75th`,
`top_industries`, `conditions`, `source`, `source_url`; or a school `about_detail`
with `founded`, `leadership`, `faculty`, `research_centers`, `source`). For a brand
new institution, create a new `<name>_profile.py` modeled on `mit_profile.py` and an
`apply(session)` that maps the data onto the columns. Stamp `_standard = {"version":
STANDARD_VERSION, "enriched_at": <date>, "omitted": [...]}`.

### 6. Migration (idempotent) + scratch-DB validation
Create an Alembic **data migration** that re-applies the profile, following the
existing pattern (a `revision`/`down_revision` module whose `upgrade()` calls
`<institution>_profile.apply(Session(bind=op.get_bind()))`; idempotent, flush-not-
commit; `replace=True`/dedup so re-runs are safe). Validate the full chain on a
fresh scratch DB before shipping:
```bash
# create scratch DB via the docker pg container, CREATE EXTENSION vector,pgcrypto,
# then: PYTHONPATH=src DATABASE_URL=...scratch... .venv/bin/alembic upgrade head
```
(Note: `apply()` no-ops when the institution isn't already seeded — so on a fresh
scratch DB it validates the migration *runs cleanly*; the data lands in prod where
the institution exists.)

### 7. Ship (the standard pipeline)
```
backend: .venv/bin/ruff check src/<changed> tests/<changed>   (NOT ruff check .)
backend: PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest <relevant tests>
frontend: npm run build           # tsc -b && vite build — the deploy gate
single alembic head, then: branch off origin/main → commit → PR → squash-merge → watch Deploy Backend → verify live
```
Verify live by querying the public API for the enriched profile and confirming the
new fields are present + cited (e.g. `GET https://api.unipaith.co/api/v1/programs/<id>`).

### 8. Log the run
Report: target, fields filled (with sources), fields omitted (with reason), the PR,
and the deploy result. If a `STANDARD_VERSION` bump is warranted (only after a
manifest change — not during routine enrichment), note it; bumping marks the whole
fleet stale so the next runs re-plan only the new/changed fields.

## Guardrails (every run)

- **No fabrication. Omit, never guess. Cite everything.** (The one rule.)
- **Bounded:** one profile (or a few fields) per run → a clean shippable unit. Do not
  try to enrich the whole fleet in one run.
- **Parent before child.** Enrich the institution before its schools/programs.
- **Idempotent migrations** (`replace=True`/dedup keys) so overlapping/repeat runs
  are safe.
- **Match the editorial standard:** content-rich, program-specific, sentence case,
  numbers with units + reporting window — never generic marketing.
- **Never expose secrets / API keys.** Do not enter credentials anywhere.
- **Ship every time** a unit is verified (commit → merge → deploy → verify live), per
  the project's standing rule; if a value can't be verified, leave it omitted and move on.
- **Stop condition:** if the chosen target is already conformant (or the fleet is),
  say so and end the run cleanly.

## Using this as a scheduled routine

The human schedules this skill (e.g. via `/schedule`) at whatever cadence they want;
each firing runs the algorithm above once and ships one verified unit. Suggested
prompt to schedule: *"Run the enrich-profile skill: pick the next-best target by
conformance and bring it one verified step closer to the gold standard, then ship."*
Because every run is bounded, idempotent, and verified, the database grows safely and
continuously without ever shipping a fabricated fact.
