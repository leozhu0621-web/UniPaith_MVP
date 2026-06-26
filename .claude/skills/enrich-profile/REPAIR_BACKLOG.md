# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / **EMPTY description shipped live** /
wrong-program content shipped live, **OR a merged repair STRANDED NOT-LIVE** / the backend deploy
pipeline itself blocked) · **high** (residual fabricated NAMES on an otherwise-rich catalog,
exact-duplicate REAL rows shipped fleet-wide, OR a matcher-core field STARVED / MIS-SIGNALED — a
whole master's / professional tier null, a catalog-wide 0% `tuition` or `cip_code`, a public's
resident-rate scalar the budget veto reads too low) · **medium** (a UNIVERSAL deep field —
`who_its_for` — shipped 0% catalog-wide / REGRESSED to 0%, institution-level seed below gold, or
dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured THIS run by a direct
full-fleet crawl: all **300 LIVE institutions** fetched (campus-photo gallery length + posts-feed
count, threaded) + the **40 program-bearing catalogs fully paginated (7,639 programs)** and run
through a per-catalog description-NON-EMPTINESS scan, an exact-duplicate `(program_name,
degree_type)` scan, a name-realness scan (CIP-rollup TITLE / "…and Related Sciences/Services" /
", General/Other" / `(CIP NN.NN)` / possessive "Bachelor's in" / bare-abbreviation / federal
comma-and tells), a per-`degree_type` tuition COVERAGE measure, and a grad==undergrad tuition-VALUE
copy-down scan. Over 12 program DETAILS/catalog (`GET /programs/{id}`) I probed `cip_code` /
`who_its_for` / `external_reviews` coverage and the public-vs-private bachelor `tuition`-scalar-vs-
`cost_data.breakdown` resident/non-resident axis. The merged-PR list + `who_its_for = None`
hard-null grep + the fresh-migration `backfill_program_preferences` / `content_sources` calls were
read via `git` over `origin/main`. Gold MIT (n=65) is the description 0-control AND a `who_its_for`
reference (100%) — but NOT a tuition or `cip_code` control (it ships null cert/PhD tiers, grad rows
at its own undergrad sticker, and null `cip_code`; its lone `name_prefixed` row — a one-line "Master
in City Planning (MCP) from DUSP." — is a pre-existing thin description on the reference, not a class).

_Last graded: 2026-06-26 (grader **run 88**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **0 rule changes** — after the full-fleet sweep, NO new
gap-class survived: structure / descriptions(pattern + NON-EMPTINESS) / NAMES / exact-dups /
tuition-VALUE-copy-down are all gold-clean fleet-wide, and EVERY residual live defect is a VIOLATION
of an existing rule (a compliance gap), so per the default-flipped doctrine + anti-churn rail it is
queued + logged, NOT re-added. **🟢 BIG PROGRESS since run 87 — all 3 CRITICAL entries CLEARED LIVE:**
(a) the run-87 **UNC stranded-deploy** (89-program catalog served 5 empty seeds) is now **LIVE & GOLD**
(89 real-named programs · field-specific descriptions · `cip_code` · `who_its_for` · non-resident
tuition) — the self-skipping data migration finally applied on a later redeploy (no re-apply PR was
needed), VALIDATING the run-87 "non-deterministic skip" diagnosis; (b) the run-87 **2 empty-desc seeds**
(UC-Davis #1178 → 151 programs, UC-Irvine #1179 → 160 programs) are **LIVE & GOLD** (0 empty descriptions
fleet-wide now, 0/7,639); (c) the run-87 **UCLA `who_its_for` regression** (100%→0%) is **REPAIRED LIVE**
(#1181 → who 100% + non-resident tuition scalar). The worst tier is now all HIGH-tier matcher-core
COMPLIANCE gaps: `cip_code` starvation (#1) → public-resident scalar (#2) → master's/professional-tier
tuition (#3) → then MEDIUM `who_its_for` 0% (#4) → reviews depth (#5) → bulk seeds (#6). NO critical
entries remain. See CHANGELOG run 88._

## Fleet at a glance (run 88, live `api.unipaith.co/api/v1` + `origin/main`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (7,639 total); 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**, 50 more at 1–3 photos, 177 at 4+). Seeding is **external**;
  the routine ENRICHES + REPAIRS only.
- **🟢 NO CRITICAL DEFECTS — the run-87 critical tier is fully CLEARED LIVE.** UNC (89), UC-Davis (151), UC-Irvine
  (160) all serve real-named, field-specific, matcher-core-complete catalogs. **0 empty descriptions across all
  7,639 programs.** Deploy pipeline healthy (migrations applying in prod). The self-skipping-migration mechanism
  remains a latent risk (FLAG #1) but produced no stranded enrichment this run.
- **🔴 matcher-core `cip_code` STARVATION (19 mature catalogs null + MIT control):** `cip_code` (the CIP join key to
  `ref_majors` + the field-66 vocabulary — the matcher's interest/field signal) is 100%-in-sample on **15 mature
  catalogs + the fresh seeds** (Caltech · Princeton · Notre Dame · Chicago · Columbia · Dartmouth · Georgia Tech ·
  UT-Austin · Berkeley · UCLA · UCSD · UNC · UVA · UW-Seattle · Penn · Vanderbilt · WashU · Georgetown · UC-Davis ·
  UC-Irvine) but **NULL on 19 mature catalogs** — Brown · BU · CMU · Cornell · Duke · Emory · Harvard · JHU · NYU ·
  Northwestern · Purdue · Rice · Stanford · UF · UIUC · Michigan · USC · UW-Madison · Yale (+ MIT control) — so the
  matcher scores those ~4,800 programs field-blind. The module already holds the IPEDS CIP per row (it gates breadth);
  ~15 of 35 modules skip the one assignment. One assignment, no research, highest matcher leverage in the fleet.
  Entry #1. Rule EXISTS (run 82) → COMPLIANCE GAP, queued; durable enforcement is FLAG #2.
- **🔴 PUBLIC-university resident-tuition scalar MIS-SIGNAL (matcher budget veto under-fires — 5 publics still in-state
  + UIUC special):** the CPEF budget feature reads the FLAT `program.tuition` scalar (`fits.py fit_range` + the
  `matching.py` budget breaker `p_tuition > s_budget`), NOT the residency-aware net-price OUTPUT estimator. **CORRECT
  (out-of-state scalar) now on 9 publics: Georgia Tech · UT-Austin · Berkeley · UC-Davis[NEW] · UC-Irvine[NEW] ·
  UCLA · UNC · UVA · UW-Seattle.** **STILL ship the IN-STATE rate** while `cost_data.breakdown` carries the higher
  out-of-state: **UCSD 16,758 (oos 50,958)** · **Michigan 17,864 (63,480)** · **Florida 6,381 (28,659)** ·
  **Wisconsin 12,186 (44,210)** · **Purdue 9,992 (28,794)**. ⚠️ **UIUC 12,992 = in_state and its breakdown has NO
  `tuition_out_of_state`** — research UIUC's published non-resident sticker (~$36k) rather than leaving the in-state
  default. An out-of-state / international applicant (the majority at a flagship public; ALL international pay
  non-resident) is scored affordable at 2.5–3.5× too low. Entry #2. Rule EXISTS (run 83) → COMPLIANCE GAP. Durable
  fix is FLAG #6 (residency-aware budget matching, CODE).
- **🔴 master's / professional-tier tuition residual (matcher grad-budget signal) — incl. on FRESH gold catalogs:**
  bachelor's tier ~100% everywhere (only UW-Seattle 113/114), but the MASTER'S (and some PROFESSIONAL) tier ships a
  material null fraction. Worst by master's null count (live run 88): **Georgetown master's 6/79 (73 null!) + prof
  10/17 (7)** [FRESH #1169 shipped 92% of its master's tier null] · **UW-Seattle 138/152 (14)** + prof 6/7 ·
  **USC 249/261 (12)** · **UC-Irvine 10/21 (11)** [FRESH] + prof 3/4 · **Yale 30/38 (8)** + cert 0/3 ·
  **UT-Austin 121/128 (7)** + prof 2/5 (3) · **UVA 8/15 (7)** [FRESH] · **BU 160/167 (7)** + prof 20/25 (flat-rate
  context below) · **Cornell 79/85 (6)** + prof 4/5 · **Penn 57/63 (6)** + cert 0/15 · **WashU 4/10 (6)** [FRESH] ·
  **Harvard 85/90 (5)** · **UCSD 54/59 (5)** · **NYU 227/232 (5)** + prof 4/6 · **UC-Davis 15/19 (4)** [FRESH] ·
  **Brown 1/5 (4)** · **Dartmouth 13/16 (3)** · small (Columbia prof 6/8, Vanderbilt 24/25, Notre Dame 23/24, UCLA
  144/145, Michigan 98/99). These publish a per-program / per-credit rate, rarely funded → stamp the published rate.
  Entry #3. **PhD / certificate nulls EXCLUDED — largely legitimate** (funded research doctorates / per-credit
  certificates → omit-with-reason; e.g. Harvard cert 0/58, Stanford cert 0/53, every catalog's PhD tier near-0%).
- **🟡 `who_its_for` UNIVERSAL-depth STARVATION (20 mature catalogs at 0%) — ROOT CAUSE = the literal `p.who_its_for
  = None`:** filled on **100% of EVERY program of 20 gold-complete catalogs** (MIT · Princeton · Caltech · Harvard ·
  Yale · Columbia · Cornell · Stanford · Chicago · Penn · Berkeley · Vanderbilt · Dartmouth · Georgetown · UVA · WashU ·
  UCLA[REPAIRED] · UC-Davis[NEW] · UC-Irvine[NEW] · UNC[NEW]) yet **0% on 20 others** — BU · Brown · CMU · Duke · Emory ·
  Georgia Tech · JHU · NYU · Northwestern · Purdue · Rice · UT-Austin · UCSD · UF · UIUC · Michigan · Notre Dame · USC ·
  UW-Seattle · Wisconsin. **Mechanism (run 86, re-confirmed by `git grep` this run):** 12 of these modules' `apply()`
  loops contain the literal `p.who_its_for = None` (brown · duke · emory · georgia_tech · michigan · nyu · rice ·
  uiuc · usc · ut_austin · uw · **ucla**), which hard-nulls the field on every `replace=True` re-apply. ⚠️ **UCLA is a
  LATENT regression:** it reads who 100% LIVE only because a LATER sibling module (#1181) overwrites the hard-null —
  `ucla_profile.py` STILL carries `p.who_its_for = None`, so a future re-apply of the base module re-nulls it; the
  durable fix removes the `= None` from the base module, not just the sibling overwrite. Derivable for EVERY program
  from its own published audience/fit material, so 0% is un-done depth, not an honest omission. Entry #4. Rule EXISTS
  (run 84 + the run-86 hard-null rule) → COMPLIANCE GAP. Durable enforcement is FLAG #4.
- **🟢 EXACT-DUPLICATE REAL rows CLEAN fleet-wide:** the raw `(program_name, degree_type)` scan returns **ZERO** on all
  40 catalogs. FLAG #5 (build-union dedup + name-uniqueness CI gate) remains the durable guard.
- **🟢 STRUCTURE + DESCRIPTIONS(pattern + NON-EMPTINESS) + NAMES + TUITION-VALUE-COPY-DOWN clean on the whole fleet
  (LIVE):** 0 empty/whitespace `description_text` across all 7,639 programs; the name-realness scan finds ZERO
  CIP-rollup TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other" / possessive "Bachelor's in"
  / bare-abbreviation names on all 40 catalogs — every multi-clause "comma-and" hit is a VERIFIED real interdisciplinary
  major (MIT's "Science, Technology, and Society"; "Speech, Language, and Hearing Sciences"; Yale "Ethics, Politics,
  and Economics"; "Molecular, Cell, and Developmental Biology") = the documented run-77 false-positive, NOT a defect.
  Tuition-VALUE copy-down clean: **BU (154 grad rows at $69,870) and USC (189 grad rows at $73,260) both match the
  VERIFIED-FLAT-RATE signature** (general-graduate flat + PROFESSIONAL tier carried DISTINCT — BU MD/DMD/SSW, USC prof
  rows ≠ undergrad sticker), the run-87 discriminator that separates a real flat rate from an indiscriminate copy-down;
  no whole-grad-tree undergrad-sticker stamp anywhere. (NOTE the one residual to VERIFY: BU's 15 LL.M./JD professional
  rows also sit at the $69,870 flat rate — within BU's documented flat-rate exception, but spot-check Law against BU
  Law's published JD tuition next deepening pass.)
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):** sampled 12
  details/catalog — richest Cornell 9/12 · Princeton 8/12 · Caltech/Penn/Purdue 6/12 · BU/Duke/JHU/Chicago 5/12;
  thinnest NYU 0/12, and 1/12 on Brown · Columbia · Emory · Georgetown · Harvard(4) · Northwestern · Notre Dame · Rice ·
  UCLA · UNC. Coverage-gated (many programs honestly have no third-party coverage; even gold MIT is 4/12) → a depth-pass
  priority on structurally-clean catalogs, NOT a fabrication mandate. Entry #5. (miss #8 + STRUCTURE-BEFORE-DEPTH order.)
- **🟡 WATCH (NOT a defect) — UC-Irvine dead feed is ingest-TIMING, not data.** UC-Irvine (#1179, ~1 day live) reads
  posts=0, but `uci_profile.py` DOES set `content_sources` (3 occurrences — real `news_rss` + `events_feed`, confirmed
  via `git`), and its sibling fresh builds Georgetown / UVA / WashU (run-87 dead-feed watches) ALL came alive this
  cycle — so the daily ingest simply has not populated UC-Irvine yet. Per step 3 (confirm data-vs-render, don't guess)
  this is NOT a miss-#1 violation — re-check next run; if STILL dead next run with `content_sources` set, escalate.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The "deploy-safe" self-skipping data migration remains the latent cause of stranded enrichments.** A heavy
   per-program data migration wraps `<uni>_profile.apply(session)` in a `lock_timeout`-bounded SAVEPOINT, SKIPS the
   apply rather than hanging container boot, and STILL records as applied so the chain advances — so Deploy Backend
   goes GREEN, the head advances, and the migration reads "applied" while the data may NEVER RUN in prod. This run it
   produced NO stranded enrichment (UNC's #1176 skip self-resolved on a later redeploy), but the mechanism is
   non-deterministic, so the next one may strand again. Durable fix: give the data-stamping a prod execution path that
   ACTUALLY RUNS (a one-off job / management command, or a migration that retries/blocks until applied and FAILS the
   deploy if it cannot), instead of a boot-time migration that records-as-applied-while-skipping. App/deploy code.
   **(highest-priority code lever; the run-87 verify-live-on-CONTENT rule is the enricher-side stopgap.)**
2. **`cip_code` is serialized but populated on only ~15 of 35 modules — NO enforced coverage gate.** Durable fix =
   a `cip_code` coverage metric in the profile test (~100% non-null per mature catalog). (carried.)
3. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES and is BLIND to EMPTY descriptions.**
   Names + non-emptiness are clean THIS run, but a future verbatim CIP-ROLLUP name or an EMPTY `description_text` would
   ship undetected (an empty string scores 0/clean on every pattern metric). Durable fix = add a name-realness metric
   AND a `description_text` NON-EMPTINESS coverage assertion (~100% non-empty per catalog) to the profile test. (carried.)
4. **No `who_its_for` / hard-null regression gate.** The 12 modules hard-coding `p.who_its_for = None` (and
   `p.tracks` / `p.highlights = None`) are invisible to CI — incl. `ucla_profile.py`, whose hard-null is currently
   MASKED by a sibling module (latent re-apply regression). Durable fix = a profile-test metric asserting
   `who_its_for` ~100% per mature catalog AND a lint/grep gate FAILING on a literal `p.<coverable_field> = None` in a
   `*_profile.py` `apply()` loop. App/test code. (carried — sharpened with the UCLA sibling-mask case.)
5. **The catalog build dedups on `slug`, not the rendered `(program_name, degree_type)`, and `_catalog_errors` never
   asserts name uniqueness.** Class is CLEAN this run (0 dups) but the gate gap remains. Durable fix: dedup the build
   UNION on `(program_name, degree_type)` + a uniqueness assertion in `test_anti_stub_gate.py`. (carried.)
6. **The CPEF budget feature is RESIDENCY-BLIND:** `matching.py` reads the single `program.tuition` scalar with no
   in-state/out-of-state branch on the student's residency. The non-resident-scalar default (entry #2) is the stopgap;
   the durable fix is residency-aware matching reading `tuition_in_state` vs `tuition_out_of_state` from the breakdown
   by the student's residency/country. App code. (carried.)
7. **No enforced gate on tuition VALUE or COVERAGE.** Durable fix = a `tuition_value_artifacts` metric + per-tier
   coverage, keying the copy-down FAIL on a professional row at the flat undergrad sticker ONLY when that school
   publishes a distinct higher rate (must NOT fail `grad==undergrad` unconditionally — false-flags BU's + USC's
   verified flat rates). A public-scalar sub-check (FAIL when the bachelor `tuition` scalar == `breakdown.tuition_in_state`
   while a higher `tuition_out_of_state` exists) makes entry #2 durable. (carried.)
8. **The `test_alembic_has_single_head` gate asserts single-head on the PR branch, not on the post-merge `origin/main`
   result.** Heads kept FORKING across prior cycles. Durable fix: assert single-head on the rebased merge result /
   `origin/main` POST-MERGE, blocking auto-merge — not just on the PR branch. (carried, lower priority — single head clean.)

---

# HIGH — matcher-core `cip_code` STARVATION (clear FIRST — highest matcher leverage, one assignment)

## 1. The 19 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 — 2026-06-26
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the field-66
vocabulary (the interest/field signal alongside the `description_text` embedding). 100%-in-sample on **15 mature
catalogs (Caltech · Princeton · Notre Dame · Chicago · Columbia · Dartmouth · Georgia Tech · UT-Austin · Berkeley ·
UCLA · UCSD · UW-Seattle · Penn · Vanderbilt + UNC) + the fresh seeds (Georgetown · UVA · WashU · UC-Davis ·
UC-Irvine)** but **NULL on 19 mature catalogs** — Brown · BU · CMU · Cornell · Duke · Emory · Harvard · JHU · NYU ·
Northwestern · Purdue · Rice · Stanford · UF · UIUC · Michigan · USC · UW-Madison · Yale (+ MIT control) — so the
matcher scores those ~4,800 programs field-blind. Only ~15 of 35 profile modules assign `p.cip_code`. **Fix (one fleet
sweep, or per catalog):** stamp `p.cip_code = spec.get("cip")` (the IPEDS CIP already used for the breadth cross-check),
exactly as the fillers do — never a guess, omit-with-reason only for a genuinely uncodeable program. Re-measure LIVE
per catalog to ~100%. (One assignment per module, no new research — highest matcher leverage in the fleet.) Rule EXISTS
(run 82) → compliance/repair, not a new rule. Durable enforcement = FLAG #2.

---

# HIGH — PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 2. The 5 public catalogs (+ UIUC) still shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 — 2026-06-26
The CPEF budget feature reads the FLAT `program.tuition` scalar (`fits.py fit_range` + the `matching.py` budget breaker
`p_tuition > s_budget`), NOT the residency-aware net-price OUTPUT estimator. **CORRECT (out-of-state scalar) now on 9
publics: Georgia Tech · UT-Austin · Berkeley · UC-Davis[NEW] · UC-Irvine[NEW] · UCLA · UNC · UVA · UW-Seattle.** STILL
in-state while `cost_data.breakdown` carries the higher non-resident rate:
- **UCSD** 16,758 vs **50,958** · **Michigan** 17,864 vs **63,480** · **Florida** 6,381 vs **28,659** · **Wisconsin**
  12,186 vs **44,210** · **Purdue** 9,992 vs **28,794** (Purdue's grad rows also ride the in-state rate).
- ⚠️ **UIUC** 12,992 = in_state, and its breakdown has **NO `tuition_out_of_state`** — research UIUC's published
  non-resident sticker (~$36k) rather than leaving the in-state default.
**Fix (per public catalog, one PR — or a single fleet sweep):** stamp the NON-RESIDENT (out-of-state) sticker into the
scalar `tuition` (the value already in `cost_data.breakdown.tuition_out_of_state` — no new research, except UIUC),
keeping BOTH rates in the breakdown. Re-measure LIVE. (A choice between two PUBLISHED numbers, never a guess.) See
FLAG #6 — durable fix is residency-aware matching. Rule EXISTS (run 83) → compliance/repair.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 3. Georgetown · UW-Seattle · USC + residuals — partial master's/professional tuition null — severity: high — first seen run 74 — 2026-06-26
Structurally + description clean catalogs whose bachelor's tier is ~100% but whose MASTER'S (and some PROFESSIONAL)
tier ships a material null fraction (the matcher scores those graduate programs' budget-fit BLIND). Worst-first by
master's null count (live run 88): **Georgetown master's 6/79 (73!) + prof 10/17 (7)** [the FRESH #1169 catalog
shipped 92% of its master's tier null] · **UW-Seattle** 138/152 (14) + prof 6/7 · **USC** 249/261 (12) · **UC-Irvine**
10/21 (11) [FRESH] + prof 3/4 · **Yale** 30/38 (8) + cert 0/3 · **UT-Austin** 121/128 (7) + prof 2/5 (3) · **UVA** 8/15
(7) [FRESH] · **BU** 160/167 (7) + prof 20/25 · **Cornell** 79/85 (6) + prof 4/5 · **Penn** 57/63 (6) + cert 0/15 ·
**WashU** 4/10 (6) [FRESH] · **Harvard** 85/90 (5) · **UCSD** 54/59 (5) · **NYU** 227/232 (5) + prof 4/6 · **UC-Davis**
15/19 (4) [FRESH] · **Brown** 1/5 (4) · **Dartmouth** 13/16 (3) · small (Columbia prof 6/8, Vanderbilt 24/25, Notre
Dame 23/24, UCLA 144/145, Michigan 98/99). **Fix (per university, one PR):** group coverage by `degree_type`; stamp the
published per-program / per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded).
For a PhD or per-credit certificate, record `tuition` in `_standard.omitted` with a reason — never a silent blanket
null, and never the undergrad sticker copied onto a professional school that bills its own higher rate (BU's + USC's
flat-rate context is verified, but spot-check BU Law's JD). **PhD / certificate nulls EXCLUDED (largely funded /
per-credit → legitimate omit-with-reason).** Re-measure LIVE per tier. (The FRESH seed-repairs — Georgetown / UVA /
WashU / UC-Davis / UC-Irvine — filled bachelor's + cip + who but under-filled their master's tuition; close that tier
in the same pass the matcher reads.)

---

# MEDIUM — `who_its_for` universal-depth starvation (root cause found) · reviews depth pass · bulk seeds

## 4. The 20 catalogs shipping `who_its_for` 0% — universal deep field un-done; ROOT CAUSE = `p.who_its_for = None`; UCLA latent-masked — severity: medium — first seen run 84 — 2026-06-26
`who_its_for` ("Who it's for", a manifest field) is filled on **100% of EVERY program of 20 gold-complete catalogs**
(MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell · Stanford · Chicago · Penn · Berkeley · Vanderbilt ·
Dartmouth · Georgetown · UVA · WashU · **UCLA[REPAIRED #1181]** · **UC-Davis[NEW]** · **UC-Irvine[NEW]** · **UNC[NEW]**)
yet **0% on 20 others** — BU · Brown · CMU · Duke · Emory · Georgia Tech · JHU · NYU · Northwestern · Purdue · Rice ·
UT-Austin · UCSD · UF · UIUC · Michigan · Notre Dame · USC · UW-Seattle · Wisconsin. **ROOT CAUSE (run 86, re-confirmed
via `git grep` this run):** 12 modules' `apply()` loops contain the literal `p.who_its_for = None` (brown · duke ·
emory · georgia_tech · michigan · nyu · rice · uiuc · usc · ut_austin · uw · **ucla**), which hard-nulls the field on
every `replace=True` re-apply. ⚠️ **UCLA is a LATENT regression:** it reads who 100% LIVE only because the later
`ucla_catalogue_descriptions` module (#1181) overwrites the hard-null — `ucla_profile.py` STILL carries
`p.who_its_for = None`, so a future re-apply of the base module re-nulls who_its_for; remove the `= None` from the base
module, do not rely on the sibling overwrite. The who-COMPLETE catalogs instead assign `p.who_its_for =
_WHO_BY_SLUG.get(slug) or _WHO_BY_TYPE.get(degree_type)`. Unlike the coverage-gated deep fields
(`external_reviews`/`class_profile`/`faculty_contacts`/`tracks`), `who_its_for` is derivable for EVERY program from its
own published audience / fit material, so 0% is un-done depth. **Fix (per catalog, in the SAME pass that fills
`cip_code`/tuition):** REPLACE `p.who_its_for = None` with a real per-slug dict (`_WHO_BY_SLUG`) of field-specific 1–2
sentence statements of the applicant each program fits — gold-contrast bar, never a classification stub ("for students
interested in {field}"), never `= None`. Re-measure LIVE to ~100%, and re-check it did not regress the catalog's OTHER
live fields. Rule EXISTS (run 84 + the run-86 hard-null rule) → compliance/repair. Durable enforcement = FLAG #4.

## 5. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 — 2026-06-26
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass. Sampled 12
details/catalog: 0/12 on NYU; 1/12 on Brown · Columbia · Emory · Georgetown · Northwestern · Notre Dame · Rice · UCLA ·
UNC; richest are Cornell 9/12 · Princeton 8/12 · Caltech/Penn/Purdue 6/12 · BU/Duke/JHU/Chicago 5/12. **Calibrate —
reviews are coverage-gated; do NOT fabricate (even gold MIT is 4/12).** **Enrich:** on a structurally-clean catalog,
run the reviews depth pass over programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports /
program outcomes reports) — program-specific summary + themes (incl. cautions) + resolvable sources, no CIP-rollup
strings, no synthesized-from-metadata reviews (miss #8) — and record `external_reviews` in `_standard.omitted` with a
reason where a program genuinely has no coverage.

## 6. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first: Air Force Institute of Technology ·
Arizona State (Campus + Digital) · Azusa Pacific · Colorado State-Fort Collins · James Madison · Keiser-Ft Lauderdale ·
Loyola Marymount · Loyola-Chicago · Miami-Oxford · Michigan Tech · Montclair State · Northcentral · Oakland · Oregon
State · SUNY-ESF · Sacred Heart · Stephen F Austin · Texas A&M (Commerce + Corpus Christi) · Thomas Jefferson · Univ Ana
G Mendez-Gurabo · UAB · Dayton · Houston · Kentucky · Louisville · Maryland-Baltimore · Missouri-St Louis ·
Nebraska-Lincoln · Oklahoma-Norman · Utah · Virginia Commonwealth), plus 50 more at 1–3 photos. **Enrich (per
university, one PR — after the HIGH tier clears):** a full real-named catalog with **field-specific `description_text`
on every program** + `who_its_for` (never `= None`) + real departments + published tuition (non-resident scalar for
publics) + `cip_code` · a working feed · a ≥4-photo verified gallery · reviews on coverable programs · `_standard`.
Pick a 0-photo seed once the higher tiers clear.

---

# CLEAN (structure + descriptions(pattern + NON-EMPTINESS) + names + tuition-value-copy-down + exact-dup + deploy; no action) — verified LIVE run 88
- **Gold (description 0-control + `who_its_for` reference):** MIT (n=65, real "Science, Technology, and Society" major;
  `who_its_for` 100%; cert/PhD tiers null + grad rows at its own undergrad sticker AND `cip_code` null — MIT is NOT a
  tuition or `cip_code` reference, the fillers are; its lone `name_prefixed` one-liner is a pre-existing thin row, not a class).
- **CLEARED LIVE & GOLD since run 87 (all 3 run-87 CRITICAL entries resolved):** **UNC-Chapel Hill (89 programs)** —
  the stranded self-skipping migration finally applied on a later redeploy (real names · field-specific descriptions ·
  `cip_code` 100% · `who_its_for` 100% · non-resident tuition); **UC-Davis (151)** [#1178] · **UC-Irvine (160)** [#1179]
  — empty-desc seeds → full gold catalogs (0 empty descriptions fleet-wide now); **UCLA** [#1181] — `who_its_for`
  regression repaired 0%→100% + non-resident tuition scalar. (Their master's-tuition tier + reviews are the residual
  depth — entries #3/#5.)
- **`cip_code`-COMPLETE (the model for entry #1):** Caltech · Princeton · Notre Dame · Chicago · Columbia · Dartmouth ·
  Georgia Tech · UT-Austin · Berkeley · UCLA · UCSD · UNC · UW-Seattle · Penn · Vanderbilt + Georgetown · UVA · WashU ·
  UC-Davis · UC-Irvine (100% in-sample).
- **`who_its_for`-COMPLETE (the model for entry #4):** MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell ·
  Stanford · Chicago · Penn · Berkeley · Vanderbilt · Dartmouth · Georgetown · UVA · WashU · **UCLA[REPAIRED]** ·
  **UC-Davis[NEW]** · **UC-Irvine[NEW]** · **UNC[NEW]** (100% on every sampled program).
- **PUBLIC non-resident scalar CORRECT:** Georgia Tech · UT-Austin · Berkeley · UCLA · UNC · UVA · UW-Seattle ·
  **UC-Davis[NEW]** · **UC-Irvine[NEW]** (bachelor `tuition` = oos).
- **EXACT-DUPLICATE class CLEAN fleet-wide:** 0 raw `(program_name, degree_type)` repeats on all 40 catalogs.
- **Name-realness CLEAN fleet-wide:** ZERO CIP-rollup TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" /
  ", General/Other" / possessive "Bachelor's in" / bare-abbreviation names on all 40 catalogs (the multi-clause
  "comma-and" hits are all VERIFIED real interdisciplinary majors — the documented run-77 false-positive).
- **EMPTY-description class CLEAN fleet-wide:** 0 empty/whitespace `description_text` across all 7,639 programs.
- **Tuition-VALUE-copy-down CLEAN:** BU ($69,870) + USC ($73,260) grad-flat rows match the VERIFIED-flat-rate signature
  (professional tier DISTINCT); no indiscriminate undergrad-sticker copy-down anywhere.
- **DEPLOY PIPELINE HEALTHY:** migrations applying in prod (the run-87 13-head block and UNC strand both cleared).
