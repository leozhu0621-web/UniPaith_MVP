# University-Granularity Enrichment Routine — Full Spec

**Status:** spec for the scheduled routine the user drives (they control cadence). Supersedes the per-profile granularity note in the first `enrich-profile` skill.

**Unit of work:** **one COMPLETE university per run.** Each firing takes a single university and enriches its **entire tree to the gold standard** — the institution page **plus every school plus every program plus all their details** — verified, and ships it as one atomic unit. It is intentionally a large job per run; that is the point.

## 1. Why university-granularity (the rationale)

- **Cross-level dependencies are satisfied atomically.** A school's quick-facts strip is *inherited* from its institution; a program's hero photo is inherited from its institution. Enriching the whole tree in one run means a school/program is never published before its parent is gold — no orphaned children, no half-built universities.
- **No partial-state churn.** One university goes from skeleton → gold in a single shippable PR, instead of dozens of tiny per-field PRs that leave a university visibly inconsistent for weeks.
- **Efficiency of research context.** Researching one university deeply (its org chart, its reports, its pages) amortizes the source-discovery cost across the whole tree — the same official domain, the same employment reports, the same registrar.
- **Clean fleet accounting.** "Universities at gold" is a simple, honest progress metric the human can watch.

## 2. The unit + completion definition

A **university unit** = `{institution} + {all its schools/colleges} + {all programs under each school}`.

A university is **done (gold)** for a `STANDARD_VERSION` when, for every node in its tree, `check_conformance(level, snapshot, profile_version=<the node's `_standard.version`>)` returns `conformant: True` — no `missing_sections`/`missing_fields` (fields legitimately recorded in that node's `_standard.omitted` are verified-unavailable and don't count as missing) **and** not `stale` versus the current `STANDARD_VERSION`. Always pass each node's `profile_version`: after a `STANDARD_VERSION` bump a node with full data is still `stale` (not gold) and must be re-enriched. Every node carries `_standard = {version, enriched_at, omitted:[...]}`.

"Everything" means: institution (rankings · report-card · admissions funnel · diversity · recognition · scale · outcomes · cost & aid · location · campus resources · feeds · sources) + each school (about-detail · feeds) + each program (basics · curriculum/tracks · admissions · costs · outcomes-with-conditions · insights · feeds), all per the manifest (`profile_standard/manifest.py`).

## 3. Per-run algorithm (detailed)

Run exactly one university to completion (or resume one in progress — §6), then ship.

### 3.1 Health check
Confirm the base is healthy and `main` is clean before starting:
```
backend: PYTHONPATH=src AI_MOCK_MODE=true .venv/bin/pytest tests/test_profile_standard.py tests/test_profile_enrichment.py -q
frontend: npm run build
```

### 3.2 Select the target university (§9 prioritization)
Pick the single highest-priority university that is **not yet gold** — either a brand-new university to add, or an existing one with the most/highest-value gaps. If a university is already mid-flight (a prior run shipped a partial tree), prefer **finishing it** before starting a new one. If all universities are gold at the current `STANDARD_VERSION`, report and stop.

### 3.3 Discover the university's full structure (§4)
Establish the canonical tree: the university's official name + UNITID; its **schools/colleges**; and within each school, its **programs** (with degree types). Use official academics/org pages + IPEDS/Scorecard program lists. Dedupe and pick canonical names/slugs. This tree is the worklist.

### 3.4 Enrich the institution first (parent before children)
Fill every required institution-level field from authoritative sources, verify each (§7), write cited values (+ conditions for stats). The institution must reach gold (or honest-omit) before schools/programs are published, so inherited stats resolve.

### 3.5 Enrich each school
For every school in the tree: `about_detail` (founded, leadership, faculty, research centers, named-for) + feeds. Verify; cite; omit-if-unverifiable.

### 3.6 Enrich each program
For every program: basics, curriculum/tracks, admissions (incl. international/recs/fee), costs (breakdown), outcomes (salary distribution + employment + top industries/employers + **conditions/methodology verbatim** + source), insights (class profile, faculty, reviews ≥2 sources), feeds. Verify each value; cite; omit-if-unverifiable.

### 3.7 Write the data module (§5)
Author/extend `unipaith-backend/src/unipaith/data/<university>_profile.py` (the data + an idempotent `apply(session)`), conforming to the manifest shape and mirroring `mit_profile.py`. Stamp every node's `_standard`.

### 3.8 Migration + scratch-DB validation
Add an idempotent Alembic data migration whose `upgrade()` calls `<university>_profile.apply(Session(bind=op.get_bind()))`. Validate the full chain on a fresh scratch DB (CREATE EXTENSION vector,pgcrypto → `alembic upgrade head`). Single head.

### 3.9 Ship
`ruff check` (changed paths) + the profile tests + `npm run build`; branch off `origin/main` → commit → PR → squash-merge → watch Deploy Backend → **verify live** (query the public API for the institution + a sample school + a sample program; confirm new fields + citations).

### 3.10 Report
Output: university name, #schools, #programs, per-level fields filled (with sources) vs omitted (with reasons), conformance before/after, and the PR link.

## 4. Structure discovery (the hard part for a new university)

For a brand-new university the routine must first learn its real org chart — never invent one.

- **Identity + key:** resolve the official legal name + **UNITID** (College Scorecard / IPEDS key). No UNITID → flag for manual mapping, skip.
- **Schools/colleges:** the university's official "Schools & Colleges" / "Academics" page is authoritative for the list of schools/colleges. Cross-check against IPEDS.
- **Programs:** enumerate degree-granting programs per school from (a) the university's official program/degree catalog, and (b) the **IPEDS / College Scorecard program list by CIP code** for that UNITID (deterministic, complete for the federal view). Prefer the official catalog for naming; use CIP/Scorecard to ensure completeness and to attach FOS outcomes.
- **Canonicalization:** dedupe (a program offered jointly appears once), assign stable `slug`s (`<univ>-<program>-<degree>`), map each program to its owning school by name. Record provenance for the structure itself (which page listed it).
- **Honesty:** if a school or program can't be confirmed from an official source, **do not add it.** The tree only contains verified nodes.

## 5. Data representation (writing a new university)

**Today (works immediately):** mirror `mit_profile.py` — per-university constants (`RANKING_DATA`, `SCHOOL_OUTCOMES`, `SCHOOLS[]`, `PROGRAMS[]`, and per-slug dicts `_OUTCOMES_BY_SLUG`, `_COST_BY_SLUG`, `_REQ_*`, `_TRACKS_BY_SLUG`, `_CLASS_PROFILE_BY_SLUG`, `_FACULTY_BY_SLUG`→`faculty_contacts`, `_REVIEWS_BY_SLUG`→`external_reviews`, school `about_detail`/`content_sources`) + an idempotent `apply(session)` that maps them onto the columns. The existing migration pattern ships it.

**Recommended evolution (machine-friendly, optional build):** a generic `profile_base.apply(profile_data, session)` that maps **manifest-shaped data** (one JSON/dict per university) → the JSONB columns, so the routine writes **data, not code**. This is the spec-§4 shared base from the parent design; it makes machine-generated universities far cleaner and is the recommended first implementation task before scaling past a handful of universities. Until it lands, the routine uses the `mit_profile.py` mirror pattern above.

Either way the written data must conform to the manifest (the conformance check is the gate) and carry citations.

## 6. Scope & resumption for very large universities

The unit is the whole tree, but a large university (100+ programs) may exceed one run. Handle gracefully:

- **Process the whole tree in priority order:** institution → schools → programs (programs ordered by student demand / level). Each field is independently verified-or-omitted, so a partial tree is always internally consistent and shippable.
- **If the run cannot finish the tree,** ship what is verified (a valid partial), record the remaining nodes via conformance (they stay non-gold), and **the next run resumes the SAME university** (because §3.2 prefers finishing in-flight universities) until the whole tree is gold, *then* moves on. For normal-size universities this is one run = one complete university; for giants it's a few consecutive runs on the same university.
- **Idempotent throughout:** re-running re-plans only what's still missing (conformance-driven `plan()`), so resumption and overlapping runs are safe (`replace=True` / dedup keys in the migration).

## 7. Verification & the no-fabrication rule (unchanged, applies to every field)

Every value, at every level, passes the gate (`profile_enrichment/gate.py` rules): `first_party` = one official source; `authoritative_2x` = ≥2 independent (distinct-domain) sources agreeing within ~5%; citation (`source` + resolvable `source_url`) required; numbers cross-checked; re-read the cited text to confirm support (multi-pass for contested numbers). **If a value cannot be verified, OMIT it** (record in `_standard.omitted`) — never guess, infer, or round into a stronger claim. Statistical fields carry the source's **conditions/methodology verbatim**.

## 8. Ordering & cross-level inheritance

Always institution → schools → programs. The institution's stats feed each school's inherited quick-facts; the institution's campus photo feeds each program's hero. Enriching top-down within the single run guarantees children are never gold-published ahead of their parent.

## 9. Target selection & fleet progress

- **Fleet:** all universities in the Postgres catalog + a curated to-add list (by UNITID). Progress metric: **# universities at gold** (per level breakdown available from conformance).
- **Prioritize universities by:** (a) student demand — saved-school / match / page-view counts; (b) presence/size of gaps (a sparse but high-traffic university first); (c) finish-in-flight before starting new.
- **Within a university,** institution first, then schools, then programs by demand/level.
- **Source/field priority within a node:** deterministic federal data (Scorecard/IPEDS/CIP) first (cheap, safe), then first-party official pages, then `authoritative_2x` reviews last.
- **Progress tracking:** each node's `_standard` + a fleet conformance report (extend the `/goal` transparency-hub pattern) is the source of truth for "which universities are done."

## 10. Guardrails (every run)

- **Never fabricate. Omit if unverifiable. Cite everything.**
- **One whole university per run** (or finish an in-flight one) — a clean, atomic, shippable unit.
- **Institution before its schools/programs.**
- **Idempotent migrations** (`replace=True` / dedup) — resumption & repeats are safe.
- **Editorial standard:** content-rich, program-specific, sentence case, numbers with units + reporting window — never generic marketing.
- **Never expose secrets / API keys.**
- **Ship every verified unit** (commit → merge → deploy → verify live); never block the tree on one unverifiable field — omit and continue.
- **Stop condition:** all universities gold at the current `STANDARD_VERSION` → report and end.

## 11. The routine prompt (what the human feeds the schedule)

```
Run the enrich-profile skill at UNIVERSITY granularity.

This run, take ONE whole university and bring its ENTIRE tree to the gold
standard — the institution page + every school + every program + all their
details — then ship it as one unit.

1. Pick the highest-priority university that is not yet gold (finish any
   university already in progress before starting a new one). If all are gold,
   say so and stop.
2. Discover its real structure from official sources: its schools/colleges and
   every program under each (cross-check IPEDS/College Scorecard by UNITID).
   Never invent a school or program.
3. Enrich top-down — institution first (so schools/programs inherit its stats
   and photo), then every school (about-detail + feeds), then every program
   (basics, curriculum, admissions, costs, outcomes-with-conditions, insights,
   feeds), per profile_standard/manifest.py.
4. VERIFY every value (>=2 authoritative sources or one first-party, citation
   required, cross-checked). OMIT anything you cannot verify — never guess.
   Capture stats' conditions/methodology verbatim.
5. Write/extend data/<university>_profile.py (mirror mit_profile.py), stamp each
   node's _standard, add an idempotent data migration, validate on a scratch DB.
6. Run checks (ruff + profile tests + npm run build), then ship: branch → PR →
   squash-merge to main → confirm the deploy → verify live (institution + a
   sample school + a sample program).
7. If the university is too large to finish this run, ship the verified partial;
   the next run will resume the SAME university until its whole tree is gold.
8. Report: university, #schools, #programs, fields filled (with sources) vs
   omitted (with reasons), and the PR link.
```

## 12. Acceptance

- One run produces (or advances) exactly one university toward a fully-gold tree, shipped live.
- Every published field is verified + cited; unverifiable fields are omitted, never guessed.
- The institution is gold before its schools/programs are published.
- Migrations are idempotent; resumption is conformance-driven and safe.
- The routine prompt + the `enrich-profile` skill together are self-sufficient: a fresh scheduled agent can execute a complete university with no additional context.
