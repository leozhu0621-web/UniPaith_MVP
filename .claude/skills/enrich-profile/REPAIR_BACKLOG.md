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
**medium** (a UNIVERSAL deep field — `who_its_for` — shipped 0% catalog-wide, institution-level
seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog (**7,288 programs across 40 catalogs**), plus a NEW per-catalog
description-NON-EMPTINESS scan (the anti_stub gate is blind to EMPTY text), per-`degree_type` tuition
COVERAGE (from the `tuition` scalar on every `/programs` row), a per-program `cip_code` /
`who_its_for` / `external_reviews` coverage probe (15 program DETAILS/catalog on `GET /programs/{id}`,
5 for the flagship seeds), an exact-duplicate `(program_name, degree_type)` scan, a name-realness scan
(federal CIP rollup TITLE + "…and Related Sciences/Services" / ", General/Other" / `(CIP NN.NN)` tells),
a public-vs-private bachelor `tuition`-scalar-vs-`cost_data.breakdown` resident/non-resident probe on
every public catalog, and a campus-photo + posts-feed fetch on every institution (all 300). The matcher's
tuition + cip consumption was read DIRECT from `match/fits.py` + `derive_preferences.py`. **The alembic
graph was AST-parsed over `origin/main` (569 revisions) and the merged-PR list read via `git` — this run
it found EIGHT concurrent heads (deploy pipeline BLOCKED).** Gold MIT (n=65) is the description 0-control
AND a `who_its_for` reference (100%) — but NOT a tuition or `cip_code` control (it ships null cert/PhD tiers,
grad rows at its own undergrad sticker, AND null `cip_code`).

_Last graded: 2026-06-25 (grader **run 85**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API + the alembic graph parsed on `origin/main`.** **1 rule change** — a
NEW description-NON-EMPTINESS coverage gate: an EMPTY / whitespace-only `description_text` is the most
matcher-core failure there is (zero embedding + a blank student page) yet it EVADES the entire pattern-based
anti_stub gate (which scores an empty catalog 0/clean), so "anti_stub 0 / structurally clean" is
necessary-NOT-sufficient — measure description NON-EMPTINESS per catalog. **🔴 NEW CRITICAL — the deploy
pipeline is BLOCKED: `origin/main` carries 8 concurrent alembic heads, so `alembic upgrade head` cannot run
and the merged Vanderbilt (#1155) + Dartmouth (#1159) enrichment repairs are STRANDED NOT-LIVE (their
`cip_code` / `who_its_for` are null in production despite the PRs merging).** **🟢 PROGRESS since run 84:** the
enricher cleared `cip_code` + `who_its_for` + non-resident scalar on **Berkeley** (#1156 re-apply, now LIVE
100%). The new worst tier is the deploy BLOCK (entry #1) → then EMPTY-description seeds (entry #2) → then the
same matcher-core `cip_code` STARVATION (#3) → public-resident scalar (#4) → master's-tier tuition (#5).
Structure / descriptions / NAMES / exact-dups / tuition-VALUE-copy-down remain gold-clean fleet-wide on the
mature catalogs (every anti_stub gate 0). See CHANGELOG run 85._

## Fleet at a glance (run 85, live `api.unipaith.co/api/v1` + `origin/main` alembic graph)

- **Fleet = 300 institutions LIVE.** **40 carry programs (7,288 total); 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**, ~53 more at 1–3 photos). Seeding is **external**; the
  routine ENRICHES + REPAIRS only.
- **🔴 DEPLOY PIPELINE BLOCKED — 8 concurrent alembic heads on `origin/main`** (`a32revwork1b2c` · `b31a1c2d3e4f`
  · `berkeleycip2` · `dartcipwho1` · `deepintel1` · `f1a9c0d2e3b4` · `n9p2q4r6s8t0` · `vandycip1`). `alembic
  upgrade head` errors "Multiple head revisions are present", so NO new migration applies in prod. Direct live
  proof: **Vanderbilt #1155 (`vandycip1`) and Dartmouth #1159 (`dartcipwho1`) MERGED to main yet their
  `cip_code` AND `who_its_for` read NULL in production** (re-checked on 4 spread programs each) — the repairs are
  stranded. CLAUDE.md mandates a fixup merge migration unifying the heads BEFORE any further backend ship; the
  enricher's own rulebook has the single-head + `test_alembic_has_single_head` + verify-live rules (SKILL.md
  ~L1630–L1665, L1795). This is a COMPLIANCE GAP (rules exist → queued, not re-added) + the deploy-mechanism is
  FLAGGED for a human. Entry #1. **Until this clears, EVERY queued repair below cannot land live — fix it first.**
- **🔴 EMPTY `description_text` on ALL 6 flagship seeds (30 programs) — blank student pages + zero matcher
  embedding, INVISIBLE to the anti_stub gate:** Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA ·
  Washington U-St Louis each ship every one of their 5 programs with a BLANK `description_text` (e.g. WashU
  "Business Administration and Management" [MBA], UVA "Systems Engineering" [BS], Georgetown "Nursing" [BS]),
  yet each scores 0 on every anti_stub metric (the pattern gate flags stub PATTERNS, not ABSENCE) and was
  certified "structurally clean" in prior backlogs. `description_text` is the dense-embedding input AND the
  primary student-facing blurb — an empty one is matcher starvation + a blank page. The mature fleet is 0 empties
  of 7,258 programs. Entry #2. NEW rule this run (description-non-emptiness coverage gate).
- **🔴 matcher-core `cip_code` STARVATION (~22 mature catalogs null):** `cip_code` (the CIP join key to
  `ref_majors` + the field-66 vocabulary — the matcher's interest/field signal) is 100%-in-sample on **11
  mature catalogs (Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD · Georgia Tech · UT-Austin ·
  UW-Seattle · Penn · Berkeley[NEW]) + the 6 flagship seeds** while **~22 mature catalogs ship it NULL** —
  MIT(control) · Brown · Vanderbilt(stranded #1155) · Harvard · Yale · Columbia · Cornell · Stanford · Duke ·
  JHU · BU · CMU · NYU · USC · UF · UIUC · Michigan · Wisconsin · Northwestern · Purdue · Rice · Dartmouth
  (stranded #1159) · Emory. Only ~11 of 36 profile modules assign `p.cip_code` — every module already holds the
  IPEDS CIP per row (it gates breadth). One-assignment, no-research fill, highest matcher leverage in the fleet.
  Entry #3. Rule EXISTS (run 82) → COMPLIANCE GAP, queued; durable enforcement is FLAG #3.
- **🔴 PUBLIC-university resident-tuition scalar MIS-SIGNAL (matcher budget veto under-fires — 7 publics still
  in-state):** the CPEF budget feature reads the FLAT `program.tuition` scalar (`fits.py fit_range` +
  `matching.py` budget breaker `p_tuition > s_budget`), NOT the residency-aware net-price OUTPUT estimator.
  **CLEARED (now out-of-state): UW-Seattle 44,460 · UT-Austin 44,908 · Berkeley 50,547[NEW] · Georgia Tech
  32,938.** **STILL ship the IN-STATE rate** while `cost_data.breakdown` carries the higher out-of-state:
  **UCLA 15,202 (oos 49,402)** · **UCSD 16,758 (50,958)** · **Michigan 17,864 (63,480)** · **Florida 6,381
  (28,659)** · **Wisconsin 12,186 (44,210)** · **Purdue 9,992 (28,794)** · **UIUC 12,992 (oos MISSING from
  breakdown)**. An out-of-state / international applicant (the majority at a flagship public; ALL international
  pay non-resident) is scored affordable at 2.5–3.5× too low. Entry #4. Rule EXISTS (run 83) → COMPLIANCE GAP.
  ⚠️ **UIUC's breakdown has NO `tuition_out_of_state`** — research UIUC's published non-resident sticker rather
  than leaving the in-state default. Durable fix is FLAG #7 (residency-aware budget matching, CODE).
- **🟡 master's / professional-tier tuition residual (matcher grad-budget signal):** bachelor's tier 100%
  everywhere, but the MASTER'S (and some PROFESSIONAL) tier ships a material null fraction. Worst (live run 85):
  **UW-Seattle master's 138/152 (14 null)** + prof 6/7 · **USC 249/261 (12)** · **Vanderbilt 15/25 (10)** + prof
  4/6 · **Yale 30/38 (8)** · **UT-Austin 121/128 (7)** + prof 2/5 · **BU 160/167 (7)** · **Cornell 79/85 (6)** +
  prof 4/5 · **Penn 57/63 (6)** · **NYU 227/232 (5)** + prof 4/6 · **Harvard 85/90 (5)** · **UCSD 54/59 (5)** ·
  **Brown 1/5 (4)** + small (UCLA 144/145, Michigan 98/99, Notre Dame 23/24, Columbia prof 6/8, Stanford prof
  0/2). **Berkeley master's now 74/74 (CLEARED).** These publish a per-program / per-credit rate, rarely funded →
  stamp the published rate. Entry #5. **PhD / certificate nulls EXCLUDED — largely legitimate** (funded research
  doctorates / per-credit certificates → omit-with-reason; e.g. Harvard cert 0/58, Stanford cert 0/53, MIT cert 0/10).
- **🟡 `who_its_for` UNIVERSAL-depth STARVATION (29 catalogs at 0%; + a REGRESSION):** filled on **100% of
  EVERY program of 11 gold-complete catalogs (MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell ·
  Stanford · Chicago · Penn · Berkeley[NEW])** yet **0% on 29 others**. **⚠️ UCLA REGRESSED 100% → 0%** (run 84
  listed it who-complete; this run 0/15 sampled + verified on 8 spread programs) while Berkeley flipped 0%→100%
  — net 11-full / 29-empty / 0-partial (the dimension-skip fingerprint). Derivable for EVERY program from its own
  published audience/fit material, so 0% is un-done depth, not an honest omission. Entry #6. Rule EXISTS (run 84).
- **🟢 EXACT-DUPLICATE REAL rows CLEAN fleet-wide:** the raw `(program_name, degree_type)` scan returns **ZERO**
  on all 40 catalogs. FLAG #1 (build-union dedup + name-uniqueness CI gate) remains the durable guard.
- **🟢 STRUCTURE + DESCRIPTIONS(pattern) + NAMES + TUITION-VALUE-COPY-DOWN clean on the mature fleet (LIVE):**
  every mature catalog scores 0 on `machine_artifacts` / `template_slot_artifacts` / `scrape_debris` /
  `frame_abs150` / `classification` / `verbatim_shared`; the name-realness scan finds ZERO federal CIP-rollup
  TITLEs / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other" / bare-abbreviation names; no NEW
  undergrad-sticker copy-down (BU's verified flat $69,870 grad rate remains the only grad==undergrad exception).
  (NOTE: "anti_stub 0" does NOT cover the EMPTY-description seeds — entry #2 — which the pattern gate cannot see.)
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):** 0/15 sampled on
  USC · NYU · UCLA · UW-Seattle · Georgia Tech · Stanford · Vanderbilt · Brown · Emory · Dartmouth + the seeds;
  ≤7/15 on most of the rest (gold MIT itself 7/15, Caltech 9/15 the richest). Coverage-gated (many programs
  honestly have no third-party coverage) → a depth-pass priority on structurally-clean catalogs, NOT a fabrication
  mandate. Entry #7. (miss #8 + STRUCTURE-BEFORE-DEPTH order.)

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **8 concurrent alembic heads on `origin/main` block `alembic upgrade head` (deploy BLOCKED) — and the
   `test_alembic_has_single_head` CI gate did NOT prevent it.** Each enrichment PR is single-head against ITS
   base, so the gate passes per-PR, but parallel PRs each chained to the then-current head and squash-merged,
   leaving main with 8 divergent leaves (the squash-skew CLAUDE.md warns about). Durable fix: ship a fixup merge
   migration unifying all 8 heads (session-unique rev id) NOW, and strengthen the gate to assert single-head on
   `origin/main` post-merge (not just on the PR branch). App/workflow code. **(NEW, blocking — highest priority.)**
2. **Heavy per-program DATA migrations are being "stamped-not-run" in prod to stop them hanging container boot
   (#1153 "stop embedding the 7k-program catalog"; #1157 "stop berkeleycip1 hanging container boot"), so their
   cip/who/tuition stamping MERGES but never EXECUTES — Berkeley needed an explicit re-apply (#1156), and
   Vanderbilt/Dartmouth now sit stranded the same way.** The data-stamping needs an execution path that actually
   runs in prod (a one-off job / management command) rather than a boot-time migration that gets skipped. App/deploy
   code. **(NEW — the mechanism behind every stranded enrichment repair.)**
3. **The catalog build dedups on `slug`, not the rendered `(program_name, degree_type)`, and `_catalog_errors`
   never asserts name uniqueness.** Class is CLEAN this run (0 dups) but the gate gap remains. Durable fix: dedup the
   build UNION on `(program_name, degree_type)` + a uniqueness assertion in `test_anti_stub_gate.py`. (carried.)
4. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES and is BLIND to EMPTY
   descriptions.** Names clean THIS run; but (a) a future verbatim CIP-ROLLUP name would ship undetected, and (b)
   the 6 seeds prove an EMPTY `description_text` scores 0/clean. Durable fix = add to the profile test a
   name-realness metric AND a `description_text` NON-EMPTINESS coverage assertion (~100% non-empty per catalog).
   App/test code. (carried + EXTENDED this run for emptiness — the enforcement teeth for entry #2's new rule.)
5. **`cip_code` is serialized but populated on only ~11 of 36 modules — NO enforced coverage gate.** Durable fix =
   a `cip_code` coverage metric in the profile test. (carried.)
6. **No enforced gate on tuition VALUE or COVERAGE.** Durable fix = a `tuition_value_artifacts` metric + per-tier
   coverage, keying the copy-down FAIL on a professional row at the flat undergrad sticker ONLY when that school
   publishes a distinct higher rate (must NOT fail `grad==undergrad` unconditionally — false-flags BU's verified
   flat rate). A public-scalar sub-check (FAIL when the bachelor `tuition` scalar == `breakdown.tuition_in_state`
   while a higher `tuition_out_of_state` exists) makes entry #4 durable. (carried.)
7. **The CPEF budget feature is RESIDENCY-BLIND:** `matching.py` reads the single `program.tuition` scalar with no
   in-state/out-of-state branch on the student's residency. The non-resident-scalar default (entry #4) is the
   stopgap; the durable fix is residency-aware matching. App code. (carried.)
8. **Stranded enricher PRs (open, unmerged = failed/superseded runs):** the older set — #1081 (Purdue), #1064
   (Rice), #769 (UCLA de-fab), #515/#503 (Harvard reviews), #499/#489 (CMU reviews), #439 (MIT), #420 (Penn),
   #403 (Harvard) — appear SUPERSEDED; a human should close them. Non-blocking.

---

# CRITICAL — the deploy pipeline is BLOCKED — clear FIRST (nothing below can land until it is)

## 1. 8 concurrent alembic heads on `origin/main` → `alembic upgrade head` fails → Vanderbilt + Dartmouth repairs stranded NOT-LIVE — severity: critical — first seen run 85 · 2026-06-25
`origin/main` carries **8 alembic leaf-heads** (`a32revwork1b2c`, `b31a1c2d3e4f`, `berkeleycip2`, `dartcipwho1`,
`deepintel1`, `f1a9c0d2e3b4`, `n9p2q4r6s8t0`, `vandycip1`), so `alembic upgrade head` errors and no new migration
applies in production. **Direct live proof of the stranding:** Vanderbilt PR #1155 (`vandycip1`,
cip_code+who_its_for+grad-tuition) and Dartmouth PR #1159 (`dartcipwho1`, cip_code+who_its_for) both MERGED, yet
on the live API every sampled Vanderbilt + Dartmouth program reads `cip_code = null` AND `who_its_for` empty —
the migrations are merged-but-not-executed (the same "stamped-not-run" failure Berkeley hit in #1156). **Fix
(repair-first, before ANY new university and before any other backlog entry):** author ONE fixup merge migration
(session-unique revision id) whose `down_revision` is the tuple of all 8 heads, re-fetch `origin/main` first to
avoid a fix-race (SKILL.md anti-fix-race), confirm `alembic heads` → single head, merge it, then re-run / re-apply
the stranded Vanderbilt + Dartmouth data and VERIFY the live API now returns their `cip_code` / `who_its_for`
populated. Rules EXIST (single-head + `test_alembic_has_single_head` + verify-live, SKILL.md) → COMPLIANCE GAP,
queued not re-added; the deploy mechanism is FLAG #1 + #2.

---

# CRITICAL — EMPTY descriptions shipped live (blank student pages + zero matcher embedding)

## 2. The 6 flagship seeds — EMPTY `description_text` on all 30 programs (+ 0% tuition · 0% who · dead feed · partial gallery) — severity: critical — first seen run 85 (empty-desc axis) / run 57 (seed tier) · 2026-06-25
**Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Washington U-St Louis** each ship 5 flagship programs,
and **every one of the 30 has a BLANK `description_text`** (e.g. WashU "Business Administration and Management" [MBA],
UVA "Systems Engineering" [BS], Georgetown "Nursing" [BS], UC-Davis "Computer Science" [BS]). `description_text` is the
matcher's dense-embedding input AND the primary student-facing blurb — empty means the matcher scores those programs on
nothing and the student sees a blank page. The anti_stub gate cannot see this (it flags stub PATTERNS, not ABSENCE), so
these seeds have been certified "structurally clean" while shipping nothing. They ALSO ship **0% tuition** across all
tiers (incl. the knowable bachelor's sticker), **0% `who_its_for`**, a **DEAD FEED** (posts=0 — the only enriched dead
feeds in the fleet), and **partial galleries** (UC-Davis 3 · UNC 3 · WashU 3 photos — below the ≥4 gold gate; Georgetown
4 · UC-Irvine 4 · UVA 5). (`cip_code` IS populated 5/5 on these seeds; `degree_type` is the raw `BA`/`BS`/`PhD`/`MBA`
form — the matcher's `_program_target_level` handles both, so not a defect, but normalize to the catalog convention when
you rebuild.) **Enrich (per university, one PR — after entry #1 unblocks the pipeline):** a full real-named catalog with
**researched, field-specific `description_text` on every program** + `who_its_for` + real departments + published tuition
(per credential level, non-resident scalar for the public ones) + `cip_code` per row + a working feed + a ≥4-photo verified
gallery + reviews on coverable programs, then deepen. Rule for empty-desc is NEW this run; the rest are existing misses.

---

# HIGH — matcher-core `cip_code` STARVATION

## 3. The ~22 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 · 2026-06-25
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the field-66
vocabulary (the interest/field signal alongside the `description_text` embedding). 100%-in-sample on **11 mature catalogs
(Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD · Georgia Tech · UT-Austin · UW-Seattle · Penn · Berkeley) + the
6 flagship seeds** but **NULL on ~22 mature catalogs** — MIT(control) · Brown · Vanderbilt(stranded #1155) · Harvard ·
Yale · Columbia · Cornell · Stanford · Duke · JHU · BU · CMU · NYU · USC · UF · UIUC · Michigan · Wisconsin · Northwestern ·
Purdue · Rice · Dartmouth(stranded #1159) · Emory — so the matcher scores those ~5,000 programs field-blind. Only ~11 of 36
profile modules assign `p.cip_code`. **Fix (one fleet sweep, or per catalog):** stamp `p.cip_code = spec.get("cip")` (the
IPEDS CIP already used for the breadth cross-check), exactly as the 11 fillers do — never a guess, omit-with-reason only for
a genuinely uncodeable program. Re-measure LIVE per catalog to ~100%. (One assignment per module, no new research — highest
matcher leverage in the fleet.) ⚠️ Vanderbilt + Dartmouth already CARRY the assignment in merged migrations — they are
stranded by entry #1, not unwritten; clearing entry #1 lands them. Rule EXISTS (run 82) → compliance/repair, not a new rule.

---

# HIGH — PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 4. The 7 public catalogs still shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 · 2026-06-25
The CPEF budget feature reads the FLAT `program.tuition` scalar (`fits.py fit_range` + the `matching.py` budget breaker
`p_tuition > s_budget`), NOT the residency-aware net-price OUTPUT estimator. **CLEARED: UW-Seattle · UT-Austin · Berkeley ·
Georgia Tech (now out-of-state).** STILL in-state while `cost_data.breakdown` carries the higher non-resident rate:
- **UCLA** 15,202 vs **49,402** · **UCSD** 16,758 vs **50,958** · **Michigan** 17,864 vs **63,480** · **Florida** 6,381 vs
  **28,659** · **Wisconsin** 12,186 vs **44,210** · **Purdue** 9,992 vs **28,794** · **UIUC** 12,992 vs **(out-of-state
  MISSING from breakdown)**.
**Fix (per public catalog, one PR — or a single fleet sweep):** stamp the NON-RESIDENT (out-of-state) sticker into the
scalar `tuition` (the value already in `cost_data.breakdown.tuition_out_of_state` — no new research), keeping BOTH rates in
the breakdown. ⚠️ **UIUC is the exception — its breakdown has NO out-of-state value**, so research UIUC's published
non-resident sticker rather than leaving the in-state default. Re-measure LIVE. (A choice between two PUBLISHED numbers,
never a guess.) See FLAG #7 — durable fix is residency-aware matching. Rule EXISTS (run 83) → compliance/repair.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 5. UW-Seattle · USC · Vanderbilt · Yale + residuals — partial master's/professional tuition null — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S (and some PROFESSIONAL) tier ships
a material null fraction (the matcher scores those graduate programs' budget-fit BLIND). Worst-first (live run 85):
**UW-Seattle** master's 138/152 (14) + prof 6/7 · **USC** 249/261 (12) · **Vanderbilt** 15/25 (10) + prof 4/6 · **Yale**
30/38 (8) · **UT-Austin** 121/128 (7) + prof 2/5 · **BU** 160/167 (7) · **Cornell** 79/85 (6) + prof 4/5 · **Penn** 57/63 (6) ·
**NYU** 227/232 (5) + prof 4/6 · **Harvard** 85/90 (5) · **UCSD** 54/59 (5) · **Brown** 1/5 (4) · small (UCLA 144/145, Michigan
98/99, Notre Dame 23/24, Columbia prof 6/8, Stanford prof 0/2). **Berkeley master's CLEARED (74/74).** **Fix (per university,
one PR):** group coverage by `degree_type`; stamp the published per-program / per-credit rate for the null MASTER'S /
PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit certificate, record `tuition` in
`_standard.omitted` with a reason — never a silent blanket null, and never the undergrad sticker copied onto a professional
school that bills its own higher rate (BU's flat-rate Law is the verified exception). **PhD / certificate nulls EXCLUDED
(largely funded / per-credit → legitimate omit-with-reason).** Re-measure LIVE per tier.

---

# MEDIUM — `who_its_for` universal-depth starvation (+ a regression) · reviews depth pass · bulk seeds

## 6. The 29 catalogs shipping `who_its_for` 0% — universal deep field un-done; UCLA REGRESSED — severity: medium — first seen run 84 · 2026-06-25
`who_its_for` ("Who it's for", a manifest field) is filled on **100% of EVERY program of 11 gold-complete catalogs** (MIT ·
Princeton · Caltech · Harvard · Yale · Columbia · Cornell · Stanford · Chicago · Penn · **Berkeley[NEW]**) yet **0% on 29
others** — USC · NYU · UIUC · BU · Michigan · **UCLA(REGRESSED 100%→0%)** · UW-Seattle · Wisconsin · UT-Austin · Florida ·
JHU · CMU · Purdue · Rice · Duke · Georgia Tech · UCSD · Northwestern · Notre Dame · Vanderbilt(stranded #1155) · Brown ·
Emory · Dartmouth(stranded #1159) · WashU · UVA · Georgetown · UC-Davis · UC-Irvine · UNC (11-full / 29-empty / **0-partial**
— the dimension-skip fingerprint). ⚠️ **UCLA regressed**: run 84 listed it who-complete; this run it reads 0/15 sampled and
0/8 on a direct spread-check — investigate whether its `cip_code` follow-up (#1142) blanked the field, and re-fill. Unlike the
coverage-gated deep fields (`external_reviews`/`class_profile`/`faculty_contacts`/`tracks` — sparse even on gold),
`who_its_for` is derivable for EVERY program from its own published audience / fit material, so 0% is un-done depth. **Fix
(per catalog, in the SAME pass that fills `cip_code`/tuition):** stamp a field-specific 1–2 sentence statement of the applicant
each program fits — gold-contrast bar, never a classification stub ("for students interested in {field}"). Re-measure LIVE to
~100%. Rule EXISTS (run 84) → compliance/repair.

## 7. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 · 2026-06-19
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass. Sampled 15
details/catalog: 0/15 with `external_reviews` on USC · NYU · UCLA · UW-Seattle · Georgia Tech · Stanford · Vanderbilt · Brown ·
Emory · Dartmouth + the seeds; ≤7/15 on the rest (gold MIT itself 7/15, Caltech 9/15 the richest). **Calibrate — reviews are
coverage-gated; do NOT fabricate.** **Enrich:** on a structurally-clean catalog, run the reviews depth pass over programs WITH
real third-party coverage (Poets&Quants / U.S. News / GradReports / program outcomes reports) — program-specific summary +
themes (incl. cautions) + resolvable sources, no CIP-rollup strings, no synthesized-from-metadata reviews (miss #8) — and
record `external_reviews` in `_standard.omitted` with a reason where a program genuinely has no coverage.

## 8. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken explore-card
gradient header + detail hero — the acute sub-set to clear first), plus ~53 more at 1–3 photos. **Enrich (per university, one
PR — after the HIGH tier clears):** a full real-named catalog with **field-specific `description_text` on every program** +
`who_its_for` + real departments + published tuition (non-resident scalar for publics) + `cip_code` · a working feed · a
≥4-photo verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the higher tiers clear.

---

# CLEAN (structure + descriptions(pattern) + names + tuition-value-copy-down + exact-dup; no action) — verified LIVE run 85
- **Gold (description 0-control + `who_its_for` reference):** MIT (n=65, 0 on every description metric; real "Science,
  Technology, and Society" major; `who_its_for` 100%; cert/PhD tiers null + grad rows at its own undergrad sticker AND
  `cip_code` null — MIT is NOT a tuition or `cip_code` reference, the fillers are).
- **`cip_code`-COMPLETE (the model for entry #3):** Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD · Georgia Tech ·
  UT-Austin · UW-Seattle · Penn · **Berkeley[NEW]** + the 6 flagship seeds (100% in-sample).
- **`who_its_for`-COMPLETE (the model for entry #6):** MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell ·
  Stanford · Chicago · Penn · **Berkeley[NEW]** (100% on every sampled program). ⚠️ UCLA dropped OFF this list (regressed).
- **PUBLIC non-resident scalar CORRECT:** UW-Seattle · UT-Austin · **Berkeley[NEW]** · Georgia Tech (bachelor `tuition` = oos).
- **EXACT-DUPLICATE class CLEAN fleet-wide:** 0 raw `(program_name, degree_type)` repeats on all 40 catalogs.
- **Name-realness CLEAN fleet-wide:** ZERO CIP-rollup TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" /
  ", General/Other" / bare-abbreviation names on ALL 40 catalogs.
- **Tuition-VALUE-copy-down CLEAN:** no NEW grad==undergrad copy-down beyond BU's VERIFIED flat full-time $69,870 grad rate.
- **NON-EMPTY descriptions on the MATURE fleet:** 0 empty `description_text` of 7,258 mature-catalog programs (the 30 empties
  are ALL on the 6 flagship seeds — entry #2).
