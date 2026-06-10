---
name: enrich-profile
description: >
  Autonomously develop the UniPaith profile database toward the gold standard,
  ONE COMPLETE UNIVERSITY per run — the institution page + every school + every
  program + all their details — verified and shipped as one atomic unit. Use as a
  scheduled routine that keeps growing the database. Discovers a university's real
  structure, researches every field from authoritative sources, VERIFIES (never
  fabricates — omits if unverifiable), writes the data + an idempotent migration,
  and ships it live. Full spec:
  docs/superpowers/specs/2026-06-10-university-enrichment-routine.md.
---

# Enrich a whole university to the gold standard

You develop the UniPaith profile database so every institution / school / program
reaches the **gold standard** defined by the MIT / Sloan / MBAn reference instance
— with **real, cited data and zero fabrication**. This skill is the complete
operating manual for one run. The human drives it on a schedule and controls the
frequency; you do exactly **one whole university** each run.

**Unit of work = one complete university** = the institution + **all** its schools
+ **all** their programs + every detail, enriched to gold, verified, shipped as one
PR. It is a large job per run, and that is intentional — it satisfies the
cross-level dependencies (schools inherit institution stats; programs inherit the
campus photo) atomically, so you never publish a half-built university or an
orphaned child.

## The one inviolable rule

**Never fabricate. Ever.** A field ships only when verified against authoritative
sources and carrying a citation. If you cannot verify it, **omit it** (record it in
that node's `_standard.omitted`). An honestly-empty field is correct; a guessed one
is a defect. Extra research tokens are acceptable; a wrong fact on a student-facing
page is not.

## What "the standard" is (read these first)

- **`unipaith-backend/src/unipaith/profile_standard/manifest.py`** — `STANDARD_VERSION`
  + the ordered `Section`/`Field` blueprint per level (`institution`, `school`,
  `program`); each `Field` has a dotted `path`, a `required` flag, a `sourcing`
  rule, and an `enrich` flag (`False` = inherited-from-parent or render-only).
- **`profile_standard/conformance.py`** — `check_conformance(level, snapshot,
  profile_version=)` → `{missing_sections, missing_fields, stale}`.
- **`profile_standard/playbook.md`** — the per-field authoritative-source + gate rules.
- **`services/profile_enrichment/gate.py`** — the deterministic verify rules.
- **`unipaith-backend/src/unipaith/data/mit_profile.py`** — the gold reference and the
  data-module template (copy its *shape*, never its values).
- **Full routine spec:** `docs/superpowers/specs/2026-06-10-university-enrichment-routine.md`.
  Parent design: `docs/superpowers/specs/2026-06-09-profile-standard-and-enrichment-design.md`.

A node is **gold** when `check_conformance` returns no missing required fields
(except fields legitimately in its `_standard.omitted`). A **university is gold**
when every node in its tree is gold.

## Per-run algorithm (one whole university)

### 1. Health check
```bash
cd unipaith-backend && PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_profile_standard.py tests/test_profile_enrichment.py -q
cd ../frontend && npm run build >/dev/null 2>&1 && echo FE_OK
```
Confirm the working tree is clean and `main` is healthy.

### 2. Select the target university
Pick the single highest-priority university **not yet gold** — a new one to add, or
an existing under-conformant one. **Finish any university already in progress before
starting a new one.** Prioritize by: student demand (saved-school / match / view
counts) → size of gaps → finish-in-flight. If every university is gold at the current
`STANDARD_VERSION`, report and stop.

### 3. Discover the university's real structure (never invent it)
- Resolve the official name + **UNITID** (College Scorecard / IPEDS key). No UNITID →
  flag for manual mapping and skip.
- **Schools/colleges:** the university's official "Schools & Colleges" / "Academics"
  page; cross-check IPEDS.
- **Programs:** enumerate degree programs per school from the official catalog **and**
  the IPEDS / College Scorecard program list (by CIP for that UNITID) for completeness.
- Dedupe; assign stable slugs (`<univ>-<program>-<degree>`); map each program to its
  owning school by name. If a school/program can't be confirmed officially, **do not
  add it.**

### 4. Enrich the institution FIRST (parent before children)
Fill every required institution-level field (rankings · report-card · admissions
funnel · diversity · recognition · scale · outcomes · cost & aid · location · campus
resources · feeds · sources) from authoritative sources. Verify each (§Verify); cite;
omit-if-unverifiable. The institution must reach gold first so schools/programs
inherit its stats + photo.

### 5. Enrich every school
For each school: `about_detail` (founded, leadership, faculty, research centers,
named-for) + feeds. Verify; cite; omit-if-unverifiable.

### 6. Enrich every program
For each program: basics, curriculum/tracks, admissions (incl. international / recs /
fee), costs (breakdown), outcomes (salary distribution + employment + top industries
/ employers + **conditions/methodology verbatim** + source), insights (class profile,
faculty, reviews from ≥2 sources), feeds. Verify each; cite; omit-if-unverifiable.

### Verify (the gate — every value, every level)
Ships only if: `first_party` = one official source; `authoritative_2x` = **≥2
independent (distinct-domain) sources agreeing** within ~5%; a **citation** (`source`
+ resolvable `source_url`) is attached; numbers cross-check; and a careful re-read of
the cited text confirms it (multi-pass for contested numbers — extra tokens are fine).
Else → **omit** (add the path to that node's `_standard.omitted`). Never guess, infer,
or round into a stronger claim. Capture stats' conditions verbatim.

### 7. Write the data module
Author/extend `unipaith-backend/src/unipaith/data/<university>_profile.py`, mirroring
`mit_profile.py`: per-university constants (`RANKING_DATA`, `SCHOOL_OUTCOMES`,
`SCHOOLS[]`, `PROGRAMS[]`) + per-slug dicts (`_OUTCOMES_BY_SLUG`, `_COST_BY_SLUG`,
`_REQ_*`, `_TRACKS_BY_SLUG`, `_CLASS_PROFILE_BY_SLUG`, `_FACULTY_BY_SLUG` →
`faculty_contacts`, `_REVIEWS_BY_SLUG` → `external_reviews`, school `about_detail` /
`content_sources`) + an idempotent `apply(session)`. Stamp every node's `_standard =
{"version": STANDARD_VERSION, "enriched_at": <date>, "omitted": [...]}`.

### 8. Migration + scratch-DB validation
Add an Alembic data migration whose `upgrade()` calls
`<university>_profile.apply(Session(bind=op.get_bind()))` (idempotent, flush-not-
commit, `replace=True`/dedup). Validate the full chain on a fresh scratch DB
(CREATE EXTENSION vector,pgcrypto → `alembic upgrade head`). Single head.

### 9. Ship
`ruff check src/<changed> tests/<changed>` (NOT `ruff check .`) + the profile tests +
`npm run build`; branch off `origin/main` → commit → PR → squash-merge → watch Deploy
Backend → **verify live** (query the public API for the institution + a sample school
+ a sample program; confirm new fields + citations).

### 10. Report
University name · #schools · #programs · per-level fields filled (with sources) vs
omitted (with reasons) · conformance before/after · PR link.

## Scope & resumption for very large universities

The unit is the whole tree, but a giant (100+ programs) may exceed one run. Each field
is independently verified-or-omitted, so a partial tree is always consistent and
shippable. If a run can't finish, **ship the verified partial**; because step 2 prefers
finishing in-flight universities, the next run **resumes the SAME university** (re-plans
only what's missing — conformance-driven) until its whole tree is gold, *then* moves on.
Idempotent migrations make resumption and overlap safe.

## Guardrails (every run)

- **Never fabricate. Omit if unverifiable. Cite everything.**
- **One whole university per run** (or finish an in-flight one) — atomic + shippable.
- **Institution before its schools/programs.**
- **Idempotent migrations** (`replace=True` / dedup).
- **Editorial standard:** content-rich, program-specific, sentence case, numbers with
  units + reporting window — never generic marketing.
- **Never expose secrets / API keys.**
- **Ship every verified unit** (commit → merge → deploy → verify live); never block the
  tree on one unverifiable field — omit and continue.
- **Stop condition:** all universities gold at the current `STANDARD_VERSION` → report
  and end.

## Using this as a scheduled routine

The human schedules this skill at any cadence they choose; each firing enriches one
whole university (or advances an in-flight one) and ships it. See §11 of the spec for
the exact prompt to schedule. Because every run is whole-tree, idempotent, and verified,
the database grows one complete university at a time, safely, without ever shipping a
fabricated fact.
