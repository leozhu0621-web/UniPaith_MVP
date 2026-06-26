# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / **EMPTY description shipped live** /
wrong-program content shipped live, **OR the backend deploy pipeline itself blocked** so no
repair can land / a merged repair stranded NOT-LIVE) · **high** (residual fabricated NAMES on
an otherwise-rich catalog, exact-duplicate REAL rows shipped fleet-wide, OR a matcher-core
field STARVED / MIS-SIGNALED — a whole master's / professional tier null, a catalog-wide 0%
`tuition` or `cip_code`, a public's resident-rate scalar the budget veto reads too low) ·
**medium** (a UNIVERSAL deep field — `who_its_for` — shipped 0% catalog-wide / REGRESSED to 0%,
institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions) + a direct
full-catalog crawl: `analyze`, `template_slot_artifacts`, `scrape_debris`,
`machine_artifacts`, and `frame_stripped_shared_body(..., abs_chars=150)` over the
fully-paginated `/programs` list of every program-bearing catalog (**7,300 programs across
40 catalogs**), plus a per-catalog description-NON-EMPTINESS scan (the anti_stub gate is blind
to EMPTY text), per-`degree_type` tuition COVERAGE (from the `tuition` scalar on every row), a
per-program `cip_code` / `who_its_for` / `external_reviews` coverage probe (10 program
DETAILS/catalog on `GET /programs/{id}`, 5 for the flagship seeds), an exact-duplicate
`(program_name, degree_type)` scan, a name-realness scan (federal CIP rollup TITLE +
"…and Related Sciences/Services" / ", General/Other" / `(CIP NN.NN)` tells), a
public-vs-private bachelor `tuition`-scalar-vs-`cost_data.breakdown` resident/non-resident
probe on every public catalog, and a campus-photo + posts-feed fetch on every one of the **300
LIVE institutions**. The matcher's tuition + cip consumption was read DIRECT from
`match/fits.py` + `derive_preferences.py`; the **regression root cause** was traced to the
`apply()` program loops in `src/unipaith/data/*_profile.py`. **The alembic graph was AST-parsed
over `origin/main` (520 revisions) and the merged-PR list read via `git` — this run it found
THIRTEEN concurrent heads (deploy pipeline BLOCKED).** Gold MIT (n=65) is the description
0-control AND a `who_its_for` reference (100%) — but NOT a tuition or `cip_code` control (it
ships null cert/PhD tiers, grad rows at its own undergrad sticker, AND null `cip_code`).

_Last graded: 2026-06-26 (grader **run 86**). **FULL-FLEET sweep: all 300 LIVE institutions +
all 40 catalogs re-measured via the live API + the alembic graph parsed on `origin/main`.**
**1 rule change** — the destructive HARD-NULL / re-apply REGRESSION class: a coverable field
hard-assigned to a literal `None` in a module's `apply()` loop (`p.who_its_for = None`) is NOT
an omission — it bakes the starvation in AND blanks the field on every `replace=True` re-apply
(the live ROOT CAUSE of the `who_its_for` 0% class and of UCLA's 100%→0% regression). **🔴
CRITICAL (recurring + WORSE) — the deploy pipeline is BLOCKED: `origin/main` carries 13
concurrent alembic heads (was 8 last run), so `alembic upgrade head` fails and the freshly
MERGED Georgetown full-catalog repair (#1169, `georgetownprof1`) is STRANDED NOT-LIVE
(production still serves its 5 empty-description seed programs).** **🟢 PROGRESS since run 85:**
the enricher landed `cip_code` + `who_its_for` LIVE on **Columbia, Vanderbilt, Dartmouth**
(stranded last run, now 100%) and `who_its_for` + non-resident scalar + `cip_code` on
**Berkeley**. The worst tier is the deploy BLOCK (entry #1) → EMPTY-description seeds (#2) →
`cip_code` STARVATION (#3) → public-resident scalar (#4) → master's-tier tuition (#5) →
`who_its_for` 0%+regression (#6). Structure / descriptions(pattern) / NAMES / exact-dups /
tuition-VALUE-copy-down remain gold-clean fleet-wide on the mature catalogs. See CHANGELOG run 86._

## Fleet at a glance (run 86, live `api.unipaith.co/api/v1` + `origin/main` alembic graph)

- **Fleet = 300 institutions LIVE.** **40 carry programs (7,300 total); 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**, ~53 more at 1–3 photos). Seeding is **external**; the
  routine ENRICHES + REPAIRS only.
- **🔴 DEPLOY PIPELINE BLOCKED — 13 concurrent alembic heads on `origin/main`** (`c25a1b2c3d4e` · `d4e5f6a7b8c9`
  · `f24da7a0c1b3` · `dartfinish1` · `f1a9c0d2e3b4` · `georgetownprof1` · `l2m3n4o5p6q7` · `nyuprof4` ·
  `pennnames1` · `r40a1b2c3d4e` · `scoredweights1` · `uiucmrg1` · `uiucuwmrg1` · `uscprof3` · `utaprof1` — 13
  leaves after the AST de-dup of multi-line tuples). `alembic upgrade head` errors "Multiple head revisions are
  present", so NO new migration applies in prod. **Direct live proof:** Georgetown PR #1169 (`georgetownprof1`,
  the latest commit on main — a full 190-program real catalog with `description_text` on every program) MERGED,
  yet the live API still returns Georgetown's **5 empty-description seed programs** — the migration is
  merged-but-not-executed. Several heads are NON-enrichment feature migrations (spec24/25/32/40, claim-fields,
  confidence-pairs, drop-crawler, scored-weights), so the fixup merge must unify ALL 13. CLAUDE.md mandates a
  fixup merge migration BEFORE any further backend ship; rules EXIST (SKILL.md §8 head-sync + step 5 +
  `test_alembic_has_single_head` + §9 verify-live). This is a COMPLIANCE GAP (queued, not re-added) + the deploy
  mechanism is FLAGGED for a human. Entry #1. **Until this clears, EVERY queued repair below cannot land live.**
- **🔴 EMPTY `description_text` on ALL 6 flagship seeds (30 programs) — blank student pages + zero matcher
  embedding, INVISIBLE to the anti_stub gate:** Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA ·
  Washington U-St Louis each ship every one of their 5 programs with a BLANK `description_text` + NULL
  `department` (e.g. WashU "Business Administration and Management" [MBA], UVA "Systems Engineering" [BS],
  Georgetown "Nursing" [BS], UC-Davis "Computer Science" [BS]). Each scores 0 on every anti_stub metric (the
  pattern gate flags stub PATTERNS, not ABSENCE). They ALSO ship **0% tuition** (incl. the knowable bachelor's
  sticker), **0% `who_its_for`**, a **DEAD FEED** (posts=0 — the only enriched dead feeds in the fleet), and
  **partial galleries** (UC-Davis 3 · UNC 3 · WashU 3 photos — below ≥4; Georgetown 4 · UC-Irvine 4 · UVA 5).
  `cip_code` IS populated 5/5 on these seeds. **Georgetown's full repair is already WRITTEN (#1169) but stranded
  by entry #1** — clearing #1 lands it; the other 5 are unbuilt. Entry #2.
- **🔴 matcher-core `cip_code` STARVATION (20 mature catalogs null):** `cip_code` (the CIP join key to
  `ref_majors` + the field-66 vocabulary — the matcher's interest/field signal) is 100%-in-sample on **14 mature
  catalogs + the 6 seeds** but **NULL on 20 mature catalogs** — MIT(control) · Brown · BU · CMU · Cornell · Duke ·
  Emory · Harvard · JHU · NYU · Northwestern · Purdue · Rice · Stanford · UF · UIUC · Michigan · USC ·
  UW-Madison · Yale — so the matcher scores those ~4,800 programs field-blind. Confirmed in repo: only **15 of 35
  profile modules assign `p.cip_code`** — the rest skip the line though every module already holds the IPEDS CIP
  per row (it gates breadth). One-assignment, no-research fill, highest matcher leverage in the fleet. Entry #3.
  Rule EXISTS (run 82) → COMPLIANCE GAP, queued; durable enforcement is FLAG #3.
- **🔴 PUBLIC-university resident-tuition scalar MIS-SIGNAL (matcher budget veto under-fires — 6 publics still
  in-state + UIUC special):** the CPEF budget feature reads the FLAT `program.tuition` scalar (`fits.py
  fit_range` + the `matching.py` budget breaker `p_tuition > s_budget`), NOT the residency-aware net-price OUTPUT
  estimator. **CLEARED (now out-of-state): UW-Seattle 44,460 · UT-Austin 44,908 · Berkeley 50,547 · Georgia Tech
  32,938.** **STILL ship the IN-STATE rate** while `cost_data.breakdown` carries the higher out-of-state:
  **UCLA 15,202 (oos 49,402)** · **UCSD 16,758 (50,958)** · **Michigan 17,864 (63,480)** · **Florida 6,381
  (28,659)** · **Wisconsin 12,186 (44,210)** · **Purdue 9,992 (28,794)**. ⚠️ **UIUC 12,992 = in_state and its
  breakdown has NO `tuition_out_of_state`** — research UIUC's published non-resident sticker rather than leaving
  the in-state default. An out-of-state / international applicant (the majority at a flagship public; ALL
  international pay non-resident) is scored affordable at 2.5–3.5× too low. Entry #4. Rule EXISTS (run 83) →
  COMPLIANCE GAP. Durable fix is FLAG #7 (residency-aware budget matching, CODE).
- **🟡 master's / professional-tier tuition residual (matcher grad-budget signal):** bachelor's tier 100%
  everywhere, but the MASTER'S (and some PROFESSIONAL) tier ships a material null fraction. Worst (live run 86):
  **UW-Seattle master's 138/152 (14)** + prof 6/7 · **USC 249/261 (12)** · **Yale 30/38 (8)** · **BU 160/167
  (7)** + prof 20/25 (5) · **UT-Austin 121/128 (7)** + prof 2/5 (3) · **Cornell 79/85 (6)** + prof 4/5 ·
  **Penn 57/63 (6)** · **Harvard 85/90 (5)** · **UCSD 54/59 (5)** · **NYU 227/232 (5)** + prof 4/6 (2) ·
  **Brown 1/5 (4)** · **Dartmouth 13/16 (3)** · small (Columbia prof 6/8, Notre Dame 23/24, UCLA 144/145,
  Michigan 98/99, Vanderbilt 24/25). These publish a per-program / per-credit rate, rarely funded → stamp the
  published rate. Entry #5. **PhD / certificate nulls EXCLUDED — largely legitimate** (funded research doctorates
  / per-credit certificates → omit-with-reason; e.g. Harvard cert 0/58, Stanford cert 0/53, MIT cert 0/10).
- **🟡 `who_its_for` UNIVERSAL-depth STARVATION (21 mature catalogs at 0% + UCLA REGRESSED) — ROOT CAUSE FOUND:**
  filled on **100% of EVERY program of 13 gold-complete catalogs (MIT · Princeton · Caltech · Harvard · Yale ·
  Columbia · Cornell · Stanford · Chicago · Penn · Berkeley · Vanderbilt · Dartmouth)** yet **0% on 21 others** —
  BU · Brown · CMU · Duke · Emory · Georgia Tech · JHU · NYU · Northwestern · Purdue · Rice · UT-Austin ·
  **UCLA(REGRESSED 100%→0%)** · UCSD · UF · UIUC · Michigan · Notre Dame · USC · UW-Seattle · Wisconsin. **The
  mechanism is now nailed:** these modules' `apply()` loop contains the literal line **`p.who_its_for = None`**
  (verified in 12 module files: brown · duke · emory · georgia_tech · michigan · nyu · rice · ucla · uiuc · usc ·
  ut_austin · uw), which hard-nulls the field on every `replace=True` re-apply — so UCLA's `cip_code` follow-up
  (#1141/#1142) re-applied the hard-nulling module and REVERTED who from 100% to 0%. The who-COMPLETE catalogs
  instead assign `_WHO_BY_SLUG.get(slug) or _WHO_BY_TYPE.get(degree_type)`. Derivable for EVERY program from its
  own published audience/fit material, so 0% is un-done depth, not an honest omission. Entry #6. Rule EXISTS
  (run 84) + the NEW hard-null rule this run.
- **🟢 EXACT-DUPLICATE REAL rows CLEAN fleet-wide:** the raw `(program_name, degree_type)` scan returns **ZERO**
  on all 40 catalogs. FLAG #6 (build-union dedup + name-uniqueness CI gate) remains the durable guard.
- **🟢 STRUCTURE + DESCRIPTIONS(pattern) + NAMES + TUITION-VALUE-COPY-DOWN clean on the mature fleet (LIVE):**
  every mature catalog scores 0 on `machine_artifacts` / `template_slot_artifacts` / `scrape_debris` /
  `frame_abs150` / `classification` / `verbatim_shared`; the name-realness scan finds ZERO federal CIP-rollup
  TITLEs / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other" / possessive "Bachelor's in" /
  bare-abbreviation names (the only flags were FALSE-POSITIVE legit slashed/combined names — "Radio/Television/
  Film", MD/PhD, JD/LLM, joint majors); no NEW undergrad-sticker copy-down (BU's verified flat $69,870 grad rate
  remains the only grad==undergrad exception). (NOTE: "anti_stub 0" does NOT cover the EMPTY-description seeds —
  entry #2 — which the pattern gate cannot see.)
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):** 0/10 sampled on
  USC · NYU · UIUC · Michigan · UCLA · UT-Austin · Georgia Tech · Vanderbilt · Dartmouth · Emory + the seeds;
  ≤6/10 on the rest (Cornell 6, Purdue 5, BU/Caltech/CMU/MIT 4 the richest). Coverage-gated (many programs
  honestly have no third-party coverage) → a depth-pass priority on structurally-clean catalogs, NOT a fabrication
  mandate. Entry #7. (miss #8 + STRUCTURE-BEFORE-DEPTH order.)

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **13 concurrent alembic heads on `origin/main` block `alembic upgrade head` (deploy BLOCKED) — RECURRING and
   WORSE (8 → 13 since run 85), and the `test_alembic_has_single_head` CI gate did NOT prevent it.** Each
   enrichment + feature PR is single-head against ITS base, so the gate passes per-PR, but parallel PRs each
   chained to the then-current head and squash-merged, leaving main with 13 divergent leaves (the squash-skew
   CLAUDE.md warns about; SKILL.md §8 step 5 predicts exactly this). Durable fix: ship ONE fixup merge migration
   unifying all 13 heads (session-unique rev id) NOW, and strengthen the gate to assert single-head on
   `origin/main` POST-MERGE / on the rebased merge result, blocking auto-merge — not just on the PR branch.
   App/workflow code. **(blocking — highest priority; the fixup PRs keep landing but new heads accrue faster.)**
2. **Heavy per-program DATA migrations are still "stamped-not-run" in prod to stop them hanging container boot
   (#1153/#1157 last cycle), so a cip/who/tuition-stamping migration MERGES but never EXECUTES** — Berkeley needed
   an explicit re-apply (#1156); Georgetown #1169 is stranded the same way. The data-stamping needs an execution
   path that actually runs in prod (a one-off job / management command) rather than a boot-time migration that gets
   skipped. App/deploy code. **(the mechanism behind every stranded enrichment repair, compounding FLAG #1.)**
3. **`cip_code` is serialized but populated on only 15 of 35 modules — NO enforced coverage gate.** Durable fix =
   a `cip_code` coverage metric in the profile test (~100% non-null per mature catalog). (carried.)
4. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES and is BLIND to EMPTY
   descriptions.** Names clean THIS run; but (a) a future verbatim CIP-ROLLUP name would ship undetected, and (b)
   the 6 seeds prove an EMPTY `description_text` scores 0/clean. Durable fix = add to the profile test a
   name-realness metric AND a `description_text` NON-EMPTINESS coverage assertion (~100% non-empty per catalog).
   App/test code. (carried.)
5. **No `who_its_for` / hard-null regression gate.** The 12 modules hard-coding `p.who_its_for = None` (and
   `p.tracks` / `p.highlights = None`) are invisible to CI. Durable fix = a profile-test metric asserting
   `who_its_for` ~100% per mature catalog AND a lint/grep gate FAILING on a literal `p.<coverable_field> = None`
   in a `*_profile.py` `apply()` loop. App/test code. **(NEW — the enforcement teeth for this run's new rule.)**
6. **The catalog build dedups on `slug`, not the rendered `(program_name, degree_type)`, and `_catalog_errors`
   never asserts name uniqueness.** Class is CLEAN this run (0 dups) but the gate gap remains. Durable fix: dedup
   the build UNION on `(program_name, degree_type)` + a uniqueness assertion in `test_anti_stub_gate.py`. (carried.)
7. **The CPEF budget feature is RESIDENCY-BLIND:** `matching.py` reads the single `program.tuition` scalar with no
   in-state/out-of-state branch on the student's residency. The non-resident-scalar default (entry #4) is the
   stopgap; the durable fix is residency-aware matching. App code. (carried.)
8. **No enforced gate on tuition VALUE or COVERAGE.** Durable fix = a `tuition_value_artifacts` metric + per-tier
   coverage, keying the copy-down FAIL on a professional row at the flat undergrad sticker ONLY when that school
   publishes a distinct higher rate (must NOT fail `grad==undergrad` unconditionally — false-flags BU's verified
   flat rate). A public-scalar sub-check (FAIL when the bachelor `tuition` scalar == `breakdown.tuition_in_state`
   while a higher `tuition_out_of_state` exists) makes entry #4 durable. (carried.)

---

# CRITICAL — the deploy pipeline is BLOCKED — clear FIRST (nothing below can land until it is)

## 1. 13 concurrent alembic heads on `origin/main` → `alembic upgrade head` fails → Georgetown (+others) stranded NOT-LIVE — severity: critical — first seen run 85 (8 heads) · recurring/worse run 86 (13) · 2026-06-26
`origin/main` carries **13 alembic leaf-heads** (`c25a1b2c3d4e`, `d4e5f6a7b8c9`, `f24da7a0c1b3`, `dartfinish1`,
`f1a9c0d2e3b4`, `georgetownprof1`, `l2m3n4o5p6q7`, `nyuprof4`, `pennnames1`, `r40a1b2c3d4e`, `scoredweights1`,
`uiucmrg1`, `uiucuwmrg1`, `uscprof3`, `utaprof1` — 13 after AST-resolving multi-line down_revision tuples), so
`alembic upgrade head` errors and no new migration applies in production. **Direct live proof of the stranding:**
Georgetown PR #1169 (`georgetownprof1`, down_revision `sixheadmerge1`) — a full 190-program real catalog —
MERGED as the latest commit on `main`, yet the live API still serves Georgetown's **5 empty-description seed
programs** (the migration is merged-but-not-executed, the same "stamped-not-run" failure mode as Berkeley #1156).
Several of the 13 heads are NON-enrichment feature migrations (spec24 data-upload, spec25 campaigns, spec32
review-assist, spec40 recruitment-crm, claim-fields, confidence-outcome-pairs, drop-crawler-tables,
scored-weights), so the fixup must unify ALL 13, not just the enrichment leaves. **Fix (repair-first, before ANY
new university and before any other backlog entry):** re-fetch `origin/main` first (SKILL.md anti-fix-race),
check the OPEN PRs for an existing in-flight merge migration, then author ONE fixup merge migration
(session-unique revision id) whose `down_revision` is the tuple of all current heads, confirm `alembic heads` →
single head, merge it, drive Deploy Backend GREEN, then re-run / re-apply the stranded Georgetown data and VERIFY
the live API now returns its real descriptions + departments + tuition. Rules EXIST (§8 head-sync + step 5 +
`test_alembic_has_single_head` + §9 verify-live) → COMPLIANCE GAP, queued not re-added; the deploy mechanism is
FLAG #1 + #2.

---

# CRITICAL — EMPTY descriptions shipped live (blank student pages + zero matcher embedding)

## 2. The 6 flagship seeds — EMPTY `description_text` on all 30 programs (+ 0% tuition · 0% who · dead feed · partial gallery) — severity: critical — first seen run 85 (empty-desc axis) / run 57 (seed tier) · 2026-06-26
**Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Washington U-St Louis** each ship 5 flagship programs,
and **every one of the 30 has a BLANK `description_text` + NULL `department`** (e.g. WashU "Business Administration
and Management" [MBA], UVA "Systems Engineering" [BS], Georgetown "Nursing" [BS], UC-Davis "Computer Science" [BS]).
`description_text` is the matcher's dense-embedding input AND the primary student-facing blurb — empty means the
matcher scores those programs on nothing and the student sees a blank page. The anti_stub gate cannot see this (it
flags stub PATTERNS, not ABSENCE), so these seeds have been certified "structurally clean" while shipping nothing.
They ALSO ship **0% tuition** across all tiers (incl. the knowable bachelor's sticker), **0% `who_its_for`**, a
**DEAD FEED** (posts=0 — the only enriched dead feeds in the fleet), and **partial galleries** (UC-Davis 3 · UNC 3 ·
WashU 3 photos — below the ≥4 gold gate; Georgetown 4 · UC-Irvine 4 · UVA 5). (`cip_code` IS populated 5/5 on these
seeds; `degree_type` is the raw `BA`/`BS`/`PhD`/`MBA` form — the matcher's `_program_target_level` handles both, so
not a defect, but normalize to the catalog convention when you rebuild.) **⚠️ Georgetown's full repair is ALREADY
WRITTEN (#1169, `georgetown_profile.py` carries `description_text` + `who_its_for` + `cip_code` on every program) but
STRANDED by entry #1 — clearing #1 lands it; do NOT re-author it.** The other 5 are unbuilt. **Enrich (per university,
one PR — after entry #1 unblocks the pipeline):** a full real-named catalog with **researched, field-specific
`description_text` on every program** + `who_its_for` (never `= None`) + real departments + published tuition (per
credential level, non-resident scalar for the public ones) + `cip_code` per row + a working feed + a ≥4-photo verified
gallery + reviews on coverable programs, then deepen.

---

# HIGH — matcher-core `cip_code` STARVATION

## 3. The 20 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 · 2026-06-26
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the field-66
vocabulary (the interest/field signal alongside the `description_text` embedding). 100%-in-sample on **14 mature
catalogs (Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD · Georgia Tech · UT-Austin · UW-Seattle · Penn ·
Berkeley · Columbia · Vanderbilt · Dartmouth) + the 6 flagship seeds** but **NULL on 20 mature catalogs** —
MIT(control) · Brown · BU · CMU · Cornell · Duke · Emory · Harvard · JHU · NYU · Northwestern · Purdue · Rice ·
Stanford · UF · UIUC · Michigan · USC · UW-Madison · Yale — so the matcher scores those ~4,800 programs field-blind.
Confirmed in repo: only **15 of 35 profile modules assign `p.cip_code`**. **Fix (one fleet sweep, or per catalog):**
stamp `p.cip_code = spec.get("cip")` (the IPEDS CIP already used for the breadth cross-check), exactly as the 15
fillers do — never a guess, omit-with-reason only for a genuinely uncodeable program. Re-measure LIVE per catalog to
~100%. (One assignment per module, no new research — highest matcher leverage in the fleet.) Rule EXISTS (run 82) →
compliance/repair, not a new rule.

---

# HIGH — PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 4. The 6 public catalogs (+ UIUC) still shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 · 2026-06-26
The CPEF budget feature reads the FLAT `program.tuition` scalar (`fits.py fit_range` + the `matching.py` budget breaker
`p_tuition > s_budget`), NOT the residency-aware net-price OUTPUT estimator. **CLEARED: UW-Seattle · UT-Austin ·
Berkeley · Georgia Tech (now out-of-state).** STILL in-state while `cost_data.breakdown` carries the higher
non-resident rate:
- **UCLA** 15,202 vs **49,402** · **UCSD** 16,758 vs **50,958** · **Michigan** 17,864 vs **63,480** · **Florida** 6,381
  vs **28,659** · **Wisconsin** 12,186 vs **44,210** · **Purdue** 9,992 vs **28,794**.
- ⚠️ **UIUC** 12,992 = in_state, and its breakdown has **NO `tuition_out_of_state`** — research UIUC's published
  non-resident sticker rather than leaving the in-state default.
**Fix (per public catalog, one PR — or a single fleet sweep):** stamp the NON-RESIDENT (out-of-state) sticker into the
scalar `tuition` (the value already in `cost_data.breakdown.tuition_out_of_state` — no new research, except UIUC),
keeping BOTH rates in the breakdown. Re-measure LIVE. (A choice between two PUBLISHED numbers, never a guess.) See
FLAG #7 — durable fix is residency-aware matching. Rule EXISTS (run 83) → compliance/repair.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 5. UW-Seattle · USC · Yale + residuals — partial master's/professional tuition null — severity: high — first seen run 74 · 2026-06-26
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S (and some PROFESSIONAL) tier
ships a material null fraction (the matcher scores those graduate programs' budget-fit BLIND). Worst-first (live run 86):
**UW-Seattle** master's 138/152 (14) + prof 6/7 · **USC** 249/261 (12) · **Yale** 30/38 (8) · **BU** 160/167 (7) + prof
20/25 (5) · **UT-Austin** 121/128 (7) + prof 2/5 (3) · **Cornell** 79/85 (6) + prof 4/5 · **Penn** 57/63 (6) ·
**Harvard** 85/90 (5) · **UCSD** 54/59 (5) · **NYU** 227/232 (5) + prof 4/6 (2) · **Brown** 1/5 (4) · **Dartmouth**
13/16 (3) · small (Columbia prof 6/8, Notre Dame 23/24, UCLA 144/145, Michigan 98/99, Vanderbilt 24/25). **Fix (per
university, one PR):** group coverage by `degree_type`; stamp the published per-program / per-credit rate for the null
MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit certificate, record
`tuition` in `_standard.omitted` with a reason — never a silent blanket null, and never the undergrad sticker copied
onto a professional school that bills its own higher rate (BU's flat-rate exception is verified). **PhD / certificate
nulls EXCLUDED (largely funded / per-credit → legitimate omit-with-reason).** Re-measure LIVE per tier.

---

# MEDIUM — `who_its_for` universal-depth starvation (root cause found) · reviews depth pass · bulk seeds

## 6. The 21 catalogs shipping `who_its_for` 0% — universal deep field un-done; UCLA REGRESSED; ROOT CAUSE = `p.who_its_for = None` — severity: medium — first seen run 84 · 2026-06-26
`who_its_for` ("Who it's for", a manifest field) is filled on **100% of EVERY program of 13 gold-complete catalogs**
(MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell · Stanford · Chicago · Penn · Berkeley ·
**Vanderbilt[NEW]** · **Dartmouth[NEW]**) yet **0% on 21 others** — BU · Brown · CMU · Duke · Emory · Georgia Tech ·
JHU · NYU · Northwestern · Purdue · Rice · UT-Austin · **UCLA(REGRESSED 100%→0%)** · UCSD · UF · UIUC · Michigan ·
Notre Dame · USC · UW-Seattle · Wisconsin (13-full / 21-empty / **0-partial** — the dimension-skip fingerprint).
**⚠️ ROOT CAUSE traced this run:** the `apply()` program loop in 12 of these modules contains the literal
`p.who_its_for = None` (verified in `brown · duke · emory · georgia_tech · michigan · nyu · rice · ucla · uiuc · usc ·
ut_austin · uw _profile.py`), which hard-nulls the field on every `replace=True` re-apply — so UCLA's `cip_code`
follow-up (#1141/#1142) re-applied the hard-nulling module and REVERTED who_its_for from 100% to 0%. The who-COMPLETE
catalogs instead assign `p.who_its_for = _WHO_BY_SLUG.get(slug) or _WHO_BY_TYPE.get(degree_type)`. Unlike the
coverage-gated deep fields (`external_reviews`/`class_profile`/`faculty_contacts`/`tracks` — sparse even on gold),
`who_its_for` is derivable for EVERY program from its own published audience / fit material, so 0% is un-done depth.
**Fix (per catalog, in the SAME pass that fills `cip_code`/tuition):** REPLACE `p.who_its_for = None` with a real
per-slug dict (`_WHO_BY_SLUG`) of field-specific 1–2 sentence statements of the applicant each program fits —
gold-contrast bar, never a classification stub ("for students interested in {field}"), never `= None`. Re-measure LIVE
to ~100%, and re-check it did not regress the catalog's OTHER live fields. Rule EXISTS (run 84) + the NEW hard-null /
re-apply-regression rule this run → compliance/repair.

## 7. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 · 2026-06-26
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass. Sampled 10
details/catalog: 0/10 with `external_reviews` on USC · NYU · UIUC · Michigan · UCLA · UT-Austin · Georgia Tech ·
Vanderbilt · Dartmouth · Emory + the seeds; ≤6/10 on the rest (Cornell 6, Purdue 5, BU/Caltech/CMU/MIT 4 the richest).
**Calibrate — reviews are coverage-gated; do NOT fabricate.** **Enrich:** on a structurally-clean catalog, run the
reviews depth pass over programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports / program
outcomes reports) — program-specific summary + themes (incl. cautions) + resolvable sources, no CIP-rollup strings, no
synthesized-from-metadata reviews (miss #8) — and record `external_reviews` in `_standard.omitted` with a reason where
a program genuinely has no coverage.

## 8. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first), plus ~53 more at 1–3 photos. **Enrich
(per university, one PR — after the HIGH tier clears):** a full real-named catalog with **field-specific
`description_text` on every program** + `who_its_for` (never `= None`) + real departments + published tuition
(non-resident scalar for publics) + `cip_code` · a working feed · a ≥4-photo verified gallery · reviews on coverable
programs · `_standard`. Pick a 0-photo seed once the higher tiers clear.

---

# CLEAN (structure + descriptions(pattern) + names + tuition-value-copy-down + exact-dup; no action) — verified LIVE run 86
- **Gold (description 0-control + `who_its_for` reference):** MIT (n=65, 0 on every description metric; real "Science,
  Technology, and Society" major; `who_its_for` 100%; cert/PhD tiers null + grad rows at its own undergrad sticker AND
  `cip_code` null — MIT is NOT a tuition or `cip_code` reference, the fillers are).
- **`cip_code`-COMPLETE (the model for entry #3):** Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD · Georgia
  Tech · UT-Austin · UW-Seattle · Penn · Berkeley · Columbia · Vanderbilt · Dartmouth + the 6 flagship seeds (100%
  in-sample).
- **`who_its_for`-COMPLETE (the model for entry #6):** MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell ·
  Stanford · Chicago · Penn · Berkeley · **Vanderbilt[NEW]** · **Dartmouth[NEW]** (100% on every sampled program).
  ⚠️ UCLA dropped OFF this list (regressed via `p.who_its_for = None`).
- **PUBLIC non-resident scalar CORRECT:** UW-Seattle · UT-Austin · Berkeley · Georgia Tech (bachelor `tuition` = oos).
- **EXACT-DUPLICATE class CLEAN fleet-wide:** 0 raw `(program_name, degree_type)` repeats on all 40 catalogs.
- **Name-realness CLEAN fleet-wide:** ZERO CIP-rollup TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" /
  ", General/Other" / possessive "Bachelor's in" / bare-abbreviation names on ALL 40 catalogs (the only scan hits were
  FALSE-POSITIVE legit slashed/combined names — kept, never mangled).
- **Tuition-VALUE-copy-down CLEAN:** no NEW grad==undergrad copy-down beyond BU's VERIFIED flat full-time $69,870 grad rate.
- **NON-EMPTY descriptions on the MATURE fleet:** 0 empty `description_text` of 7,270 mature-catalog programs (the 30
  empties are ALL on the 6 flagship seeds — entry #2).
- **PROGRESS LANDED LIVE since run 85:** Columbia · Vanderbilt · Dartmouth `cip_code` + `who_its_for` now 100% (were
  stranded last run); Berkeley `who_its_for` 0→100%, `cip_code` 100%, non-resident scalar correct.
