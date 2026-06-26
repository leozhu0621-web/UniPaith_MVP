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
full-fleet crawl: all **300 LIVE institutions** fetched (campus-photo count + posts-feed count,
threaded) + the **40 program-bearing catalogs fully paginated (7,639 programs)** and run through
`profile_standard/anti_stub.py` (the enforced CI gate's own `analyze` / `machine_artifacts` /
`template_slot_artifacts` / `scrape_debris`), plus a per-catalog description-NON-EMPTINESS scan,
an exact-duplicate `(program_name, degree_type)` scan, a name-realness scan (CIP-rollup TITLE /
"…and Related Sciences/Services" / ", General/Other" / `(CIP NN.NN)` / possessive "Bachelor's in"
/ bare-abbreviation tells), and a per-`degree_type` tuition COVERAGE measure. Over 12 program
DETAILS/catalog (`GET /programs/{id}`) I probed `cip_code` / `who_its_for` / `external_reviews`
coverage and the public-vs-private bachelor `tuition`-scalar-vs-`cost_data.breakdown`
resident/non-resident axis. The alembic graph was **AST-parsed over `origin/main` (525 revisions)**
and the merged-PR list read via `git`. The matcher's tuition + cip consumption is read DIRECT from
`match/fits.py` + `matching.py`. Gold MIT (n=65) is the description 0-control AND a `who_its_for`
reference (100%) — but NOT a tuition or `cip_code` control (it ships null cert/PhD tiers, grad rows
at its own undergrad sticker, and null `cip_code`; its lone `name_prefixed` row — a one-line "Master
in City Planning (MCP) from DUSP." — is a pre-existing thin description on the reference, not a class).

_Last graded: 2026-06-26 (grader **run 87**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API + the alembic graph AST-parsed on `origin/main`.** **1 rule
change** — the all-GREEN STRANDED-DEPLOY class: a "deploy-safe" data migration that runs its
`<uni>_profile.apply()` inside a `lock_timeout`-bounded SAVEPOINT, SKIPS the apply rather than
hanging container boot, yet STILL records as applied so the alembic chain advances — making Deploy
Backend GREEN + a single advanced head + an "applied" migration a FALSE proof-of-live; the only valid
verify-live gate is the live-API CONTENT (program count / real descriptions), and a skipped apply is
NOT done until an explicit re-apply lands. **🟢 BIG PROGRESS since run 86:** the 13-concurrent-alembic-head
DEPLOY BLOCK is CLEARED — `origin/main` now has a SINGLE head (`uncprof1`); and the stranded
**Georgetown (190 programs), UVA (100), WashU (58)** empty-desc seed repairs all LANDED LIVE and read
GOLD (real names · field-specific descriptions · `cip_code` · `who_its_for` · non-resident tuition
scalar). **🔴 NEW CRITICAL — UNC stranded NOT-LIVE:** UNC's full 89-program catalog (#1176, `uncprof1`)
merged with Deploy Backend GREEN and is the SINGLE head, yet the live API still serves its **5
empty-description seed programs** because the migration's data apply self-SKIPPED at boot (the new rule's
exact instance). The worst tier is now the STRANDED UNC re-apply (#1) → 2 UNBUILT empty-desc seeds (#2) →
`cip_code` starvation (#3) → public-resident scalar (#4) → master's-tier tuition (#5) → `who_its_for`
0%+regression (#6). Structure / descriptions(pattern) / NAMES / exact-dups / tuition-VALUE-copy-down
remain gold-clean fleet-wide on the mature catalogs. See CHANGELOG run 87._

## Fleet at a glance (run 87, live `api.unipaith.co/api/v1` + `origin/main` alembic graph)

- **Fleet = 300 institutions LIVE.** **40 carry programs (7,639 total); 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**, 50 more at 1–3 photos, 177 at 4+). Seeding is **external**;
  the routine ENRICHES + REPAIRS only.
- **🟢 DEPLOY PIPELINE UNBLOCKED — `origin/main` carries a SINGLE alembic head (`uncprof1`)** (AST-parsed over 525
  revisions; the 13-head block from run 86 was unified by #1171 and the subsequent fixups). `alembic upgrade head`
  resolves, so migrations apply in prod again — the Georgetown / UVA / WashU repairs that were stranded by the block
  all deployed.
- **🔴 STRANDED NOT-LIVE — UNC-Chapel Hill (the all-GREEN self-skipping-migration class):** `uncprof1` (UNC's full
  89-program gold catalog, PR #1176) is the SINGLE head on `origin/main`, merged with Deploy Backend GREEN and the
  migration recorded as applied — yet the live API returns UNC's **5 empty-description seed programs** (program_count
  = 5, every `description_text` blank, `department` null, 3 campus photos, dead feed). Cause (from the migration's own
  docstring): the idempotent data apply "runs inside a SAVEPOINT bounded by `lock_timeout` and is SKIPPED rather than
  hanging container boot… still records as applied so the chain advances." The byte-identical pattern on **WashU /
  UVA the same cycle DID land** (58 / 100 programs live), proving the skip is NON-DETERMINISTIC lock-timing, not a
  code error. Fix = an explicit RE-APPLY of `unc_profile.apply()` in prod (exactly as the prior Berkeley re-apply),
  then verify the live count = 89. This is the NEW rule's live instance + FLAG #1 (the durable code fix). Entry #1.
- **🔴 EMPTY `description_text` on the 2 UNBUILT flagship seeds (10 programs) — blank student pages + zero matcher
  embedding, INVISIBLE to the anti_stub gate:** **UC-Davis · UC-Irvine** each still ship every one of their 5 programs
  with a BLANK `description_text` + NULL `department` (e.g. UC-Davis "Computer Science" [BS]). Each scores 0 on every
  anti_stub metric (the pattern gate flags stub PATTERNS, not ABSENCE). They ALSO ship **0% tuition**, **0%
  `who_its_for`**, a **DEAD FEED** (posts=0), and **partial galleries** (UC-Davis 3 photos < 4; UC-Irvine 4).
  `cip_code` IS populated 5/5 on these seeds. Entry #2. (Of run 86's 6 empty-desc seeds, **4 are resolved** —
  Georgetown / UVA / WashU LIVE-gold; UNC built-but-stranded → entry #1.)
- **🔴 matcher-core `cip_code` STARVATION (20 mature catalogs null):** `cip_code` (the CIP join key to `ref_majors` +
  the field-66 vocabulary — the matcher's interest/field signal) is 100%-in-sample on **14 mature catalogs + the
  fresh seeds (Georgetown / UVA / WashU / UNC-seed)** but **NULL on 20 mature catalogs** — MIT(control) · Brown · BU ·
  CMU · Cornell · Duke · Emory · Harvard · JHU · NYU · Northwestern · Purdue · Rice · Stanford · UF · UIUC · Michigan ·
  USC · UW-Madison · Yale — so the matcher scores those ~4,800 programs field-blind. Only ~15 of 35 profile modules
  assign `p.cip_code`, though every module already holds the IPEDS CIP per row (it gates breadth). One assignment, no
  research, highest matcher leverage in the fleet. Entry #3. Rule EXISTS (run 82) → COMPLIANCE GAP, queued; durable
  enforcement is FLAG #2.
- **🔴 PUBLIC-university resident-tuition scalar MIS-SIGNAL (matcher budget veto under-fires — 6 publics still
  in-state + UIUC special):** the CPEF budget feature reads the FLAT `program.tuition` scalar (`fits.py fit_range` +
  the `matching.py` budget breaker `p_tuition > s_budget`), NOT the residency-aware net-price OUTPUT estimator.
  **CORRECT (out-of-state scalar): Georgia Tech 32,938 · UT-Austin 44,908 · Berkeley 50,547 · UW-Seattle 44,460 ·
  UVA 59,512[NEW].** **STILL ship the IN-STATE rate** while `cost_data.breakdown` carries the higher out-of-state:
  **UCLA 15,202 (oos 49,402)** · **UCSD 16,758 (50,958)** · **Michigan 17,864 (63,480)** · **Florida 6,381 (28,659)** ·
  **Wisconsin 12,186 (44,210)** · **Purdue 9,992 (28,794)**. ⚠️ **UIUC 12,992 = in_state and its breakdown has NO
  `tuition_out_of_state`** — research UIUC's published non-resident sticker rather than leaving the in-state default.
  An out-of-state / international applicant (the majority at a flagship public; ALL international pay non-resident) is
  scored affordable at 2.5–3.5× too low. Entry #4. Rule EXISTS (run 83) → COMPLIANCE GAP. Durable fix is FLAG #6
  (residency-aware budget matching, CODE).
- **🟡 master's / professional-tier tuition residual (matcher grad-budget signal) — incl. on FRESH gold catalogs:**
  bachelor's tier 100% everywhere, but the MASTER'S (and some PROFESSIONAL) tier ships a material null fraction. Worst
  (live run 87, null count): **Georgetown master's 6/79 (73 null!) + prof 10/17 (7)** [FRESH #1169 shipped 92% of its
  master's tier null] · **UW-Seattle 138/152 (14)** + prof 6/7 · **Yale 30/38 (8)** + cert 0/3 · **UT-Austin 121/128 (7)**
  + prof 2/5 (3) · **UVA 8/15 (7)** [FRESH] · **Cornell 79/85 (6)** + prof 4/5 · **Penn 57/63 (6)** + cert 0/15 ·
  **WashU 4/10 (6)** [FRESH] · **Harvard 85/90 (5)** · **UCSD 54/59 (5)** · **Brown 1/5 (4)** · **Dartmouth 13/16 (3)** ·
  small (Columbia prof 6/8, NYU prof 4/6). These publish a per-program / per-credit rate, rarely funded → stamp the
  published rate. Entry #5. **PhD / certificate nulls EXCLUDED — largely legitimate** (funded research doctorates /
  per-credit certificates → omit-with-reason; e.g. Harvard cert 0/58, Stanford cert 0/53, every catalog's PhD tier).
- **🟡 `who_its_for` UNIVERSAL-depth STARVATION (24 mature catalogs at 0% + UCLA REGRESSED) — ROOT CAUSE = `p.who_its_for
  = None`:** filled on **100% of EVERY program of 16 gold-complete catalogs (MIT · Princeton · Caltech · Harvard · Yale ·
  Columbia · Cornell · Stanford · Chicago · Penn · Berkeley · Vanderbilt · Dartmouth · Georgetown[NEW] · UVA[NEW] ·
  WashU[NEW])** yet **0% on 24 others** — BU · Brown · CMU · Duke · Emory · Georgia Tech · JHU · NYU · Northwestern ·
  Purdue · Rice · UT-Austin · **UCLA(REGRESSED 100%→0%)** · UCSD · UF · UIUC · Michigan · Notre Dame · USC · UW-Seattle ·
  Wisconsin (+ the unbuilt/stranded UC-Davis / UC-Irvine / UNC seeds). **Mechanism (run 86):** these modules' `apply()`
  loop contains the literal `p.who_its_for = None`, which hard-nulls the field on every `replace=True` re-apply. The
  who-COMPLETE catalogs instead assign `_WHO_BY_SLUG.get(slug) or _WHO_BY_TYPE.get(degree_type)`. Derivable for EVERY
  program from its own published audience/fit material, so 0% is un-done depth, not an honest omission. Entry #6. Rule
  EXISTS (run 84 + the run-86 hard-null rule) → COMPLIANCE GAP. Durable enforcement is FLAG #4.
- **🟢 EXACT-DUPLICATE REAL rows CLEAN fleet-wide:** the raw `(program_name, degree_type)` scan returns **ZERO** on all
  40 catalogs. FLAG #5 (build-union dedup + name-uniqueness CI gate) remains the durable guard.
- **🟢 STRUCTURE + DESCRIPTIONS(pattern) + NAMES + TUITION-VALUE-COPY-DOWN clean on the mature fleet (LIVE):** every
  mature catalog scores 0 on `machine_artifacts` / `template_slot_artifacts` / `scrape_debris` / `analyze`; the
  name-realness scan finds ZERO CIP-rollup TITLEs / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other"
  / possessive "Bachelor's in" / bare-abbreviation names on all 40 catalogs (the only `analyze` hit is gold MIT's single
  `name_prefixed` one-liner — a pre-existing thin reference row, not a class). No NEW undergrad-sticker copy-down (BU's
  verified flat $69,870 grad rate remains the only grad==undergrad exception). (NOTE: "anti_stub 0" does NOT cover the
  EMPTY-description seeds — entries #1/#2 — which the pattern gate cannot see.)
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):** 0/12 sampled on Brown ·
  Dartmouth · Emory · Georgetown · NYU · UT-Austin · UCLA · UCSD · Chicago · Michigan · Notre Dame · UW-Seattle + the
  fresh/seed catalogs (UVA · WashU · UNC · UC-Davis · UC-Irvine); richest are Duke 50% · Princeton 50% · Caltech/CMU/
  Cornell/MIT 41% · Harvard/Penn 33%. Coverage-gated (many programs honestly have no third-party coverage) → a depth-pass
  priority on structurally-clean catalogs, NOT a fabrication mandate. Entry #7. (miss #8 + STRUCTURE-BEFORE-DEPTH order.)
- **🟡 WATCH (NOT a defect) — dead feeds on the 3 FRESH live-built catalogs are ingest-TIMING, not data.** Georgetown ·
  UVA · WashU read posts=0, but ALL THREE modules DO set `content_sources` (real `news_rss` + `events_feed`, confirmed
  direct in the profile modules), so the daily ingest simply has not populated these recently-live catalogs yet (the
  34 older mature catalogs all carry live feeds). Per step 3 (confirm data-vs-render, don't guess) this is NOT a miss-#1
  violation — re-check next run; if Georgetown is STILL dead next run with `content_sources` set, escalate to a real
  dead-feed defect. (UNC / UC-Davis / UC-Irvine dead feeds are because the data is not live — entries #1/#2.)

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The "deploy-safe" self-skipping data migration is the SOLE cause of stranded enrichments now the head-block has
   cleared.** A heavy per-program data migration wraps `<uni>_profile.apply(session)` in a `lock_timeout`-bounded
   SAVEPOINT, SKIPS the apply rather than hanging container boot, and STILL records as applied so the chain advances —
   so Deploy Backend goes GREEN, the head advances, and the migration reads "applied" while the data NEVER RAN in prod
   (UNC #1176 this run; Berkeley #1156, Georgetown earlier). The skip is non-deterministic, so the same pattern lands
   for one university and silently skips the next. Durable fix: give the data-stamping a prod execution path that
   ACTUALLY RUNS (a one-off job / management command, or a migration that retries/blocks until applied and FAILS the
   deploy if it cannot), instead of a boot-time migration that records-as-applied-while-skipping. App/deploy code.
   **(blocking — highest priority; every stranded enrichment traces here, and the new run-87 rule is its enricher-side
   stopgap: re-query live CONTENT, re-apply when skipped.)**
2. **`cip_code` is serialized but populated on only ~15 of 35 modules — NO enforced coverage gate.** Durable fix =
   a `cip_code` coverage metric in the profile test (~100% non-null per mature catalog). (carried.)
3. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES and is BLIND to EMPTY descriptions.**
   Names clean THIS run; but (a) a future verbatim CIP-ROLLUP name would ship undetected, and (b) the empty-desc seeds
   prove an EMPTY `description_text` scores 0/clean. Durable fix = add a name-realness metric AND a `description_text`
   NON-EMPTINESS coverage assertion (~100% non-empty per catalog) to the profile test. App/test code. (carried.)
4. **No `who_its_for` / hard-null regression gate.** The modules hard-coding `p.who_its_for = None` (and `p.tracks` /
   `p.highlights = None`) are invisible to CI. Durable fix = a profile-test metric asserting `who_its_for` ~100% per
   mature catalog AND a lint/grep gate FAILING on a literal `p.<coverable_field> = None` in a `*_profile.py` `apply()`
   loop. App/test code. (carried.)
5. **The catalog build dedups on `slug`, not the rendered `(program_name, degree_type)`, and `_catalog_errors` never
   asserts name uniqueness.** Class is CLEAN this run (0 dups) but the gate gap remains. Durable fix: dedup the build
   UNION on `(program_name, degree_type)` + a uniqueness assertion in `test_anti_stub_gate.py`. (carried.)
6. **The CPEF budget feature is RESIDENCY-BLIND:** `matching.py` reads the single `program.tuition` scalar with no
   in-state/out-of-state branch on the student's residency. The non-resident-scalar default (entry #4) is the stopgap;
   the durable fix is residency-aware matching. App code. (carried.)
7. **No enforced gate on tuition VALUE or COVERAGE.** Durable fix = a `tuition_value_artifacts` metric + per-tier
   coverage, keying the copy-down FAIL on a professional row at the flat undergrad sticker ONLY when that school
   publishes a distinct higher rate (must NOT fail `grad==undergrad` unconditionally — false-flags BU's verified flat
   rate). A public-scalar sub-check (FAIL when the bachelor `tuition` scalar == `breakdown.tuition_in_state` while a
   higher `tuition_out_of_state` exists) makes entry #4 durable. (carried.)
8. **The `test_alembic_has_single_head` gate asserts single-head on the PR branch, not on the post-merge `origin/main`
   result.** The 13-head block (run 86) cleared this run, but heads kept FORKING across the cycle (e.g. a provider
   migration forked a 2nd head off the real head and broke the gate after merge). Durable fix: assert single-head on
   the rebased merge result / `origin/main` POST-MERGE, blocking auto-merge — not just on the PR branch. (carried,
   lower priority now the block is clear.)

---

# CRITICAL — a merged repair is STRANDED NOT-LIVE — clear FIRST (the all-green self-skip)

## 1. UNC-Chapel Hill — full 89-program catalog merged + green deploy + single head, yet live serves 5 EMPTY seed programs — severity: critical — first seen run 87 — 2026-06-26
`uncprof1` (PR #1176, UNC's full 89-program gold catalog across its 13 degree-granting schools) is the SINGLE alembic
head on `origin/main`, merged with Deploy Backend GREEN and the migration recorded as applied — **yet the live API
returns UNC's 5 empty-description seed programs** (`program_count` = 5, every `description_text` blank, `department`
null, 3 campus photos, dead feed). The migration's own docstring states the data apply "runs inside a SAVEPOINT bounded
by `lock_timeout` and is SKIPPED rather than hanging container boot… still records as applied so the chain advances."
The byte-identical pattern on WashU (#1173) and UVA (#1174) the same cycle DID land (58 / 100 programs live), so the
skip is non-deterministic lock-timing, NOT a code error — UNC's `unc_profile.apply()` simply never executed in prod.
**Fix (repair-first, before ANY new university and before any other backlog entry):** re-fetch `origin/main` first
(anti-fix-race), confirm the data is still empty live, then land an explicit RE-APPLY that EXECUTES
`unc_profile.apply(session)` in prod (a re-apply migration / one-off job, exactly as the Berkeley re-apply #1156 did),
drive Deploy Backend GREEN, and VERIFY the live API now returns UNC's 89 real-named programs with field-specific
`description_text`, real departments, `cip_code`, `who_its_for`, and non-resident tuition. Do NOT re-author the
already-correct `unc_profile` data — only land its execution. Rule EXISTS (the run-87 verify-live-on-CONTENT rule + §9)
→ COMPLIANCE GAP, queued; the deploy mechanism is FLAG #1.

---

# CRITICAL — EMPTY descriptions shipped live (blank student pages + zero matcher embedding)

## 2. The 2 unbuilt flagship seeds — EMPTY `description_text` on all 10 programs (+ 0% tuition · 0% who · dead feed · partial gallery) — severity: critical — first seen run 85 (empty-desc axis) / run 57 (seed tier) — 2026-06-26
**UC-Davis · UC-Irvine** each ship 5 flagship programs, and **every one of the 10 has a BLANK `description_text` + NULL
`department`** (e.g. UC-Davis "Computer Science" [BS]). `description_text` is the matcher's dense-embedding input AND the
primary student-facing blurb — empty means the matcher scores those programs on nothing and the student sees a blank
page. The anti_stub gate cannot see this (it flags stub PATTERNS, not ABSENCE), so these seeds are certified
"structurally clean" while shipping nothing. They ALSO ship **0% tuition**, **0% `who_its_for`**, a **DEAD FEED**
(posts=0), and **partial galleries** (UC-Davis 3 photos < the ≥4 gold gate; UC-Irvine 4). (`cip_code` IS populated 5/5;
`degree_type` is the raw `BA`/`BS`/`PhD`/`MBA` form — the matcher's `_program_target_level` handles both, so not a
defect, but normalize to the catalog convention when you rebuild.) **Enrich (per university, one PR):** a full
real-named catalog with **researched, field-specific `description_text` on every program** + `who_its_for` (never `=
None`) + real departments + published tuition (per credential level, non-resident scalar for these UC publics) +
`cip_code` per row + a working feed + a ≥4-photo verified gallery + reviews on coverable programs, then deepen — exactly
as Georgetown / UVA / WashU were just done.

---

# HIGH — matcher-core `cip_code` STARVATION

## 3. The 20 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 — 2026-06-26
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the field-66
vocabulary (the interest/field signal alongside the `description_text` embedding). 100%-in-sample on **14 mature
catalogs (Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD · Georgia Tech · UT-Austin · UW-Seattle · Penn ·
Berkeley · Columbia · Vanderbilt · Dartmouth) + the fresh seeds (Georgetown · UVA · WashU)** but **NULL on 20 mature
catalogs** — MIT(control) · Brown · BU · CMU · Cornell · Duke · Emory · Harvard · JHU · NYU · Northwestern · Purdue ·
Rice · Stanford · UF · UIUC · Michigan · USC · UW-Madison · Yale — so the matcher scores those ~4,800 programs
field-blind. Only ~15 of 35 profile modules assign `p.cip_code`. **Fix (one fleet sweep, or per catalog):** stamp
`p.cip_code = spec.get("cip")` (the IPEDS CIP already used for the breadth cross-check), exactly as the fillers do —
never a guess, omit-with-reason only for a genuinely uncodeable program. Re-measure LIVE per catalog to ~100%. (One
assignment per module, no new research — highest matcher leverage in the fleet.) Rule EXISTS (run 82) →
compliance/repair, not a new rule.

---

# HIGH — PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 4. The 6 public catalogs (+ UIUC) still shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 — 2026-06-26
The CPEF budget feature reads the FLAT `program.tuition` scalar (`fits.py fit_range` + the `matching.py` budget breaker
`p_tuition > s_budget`), NOT the residency-aware net-price OUTPUT estimator. **CORRECT (out-of-state scalar): Georgia
Tech · UT-Austin · Berkeley · UW-Seattle · UVA[NEW].** STILL in-state while `cost_data.breakdown` carries the higher
non-resident rate:
- **UCLA** 15,202 vs **49,402** · **UCSD** 16,758 vs **50,958** · **Michigan** 17,864 vs **63,480** · **Florida** 6,381
  vs **28,659** · **Wisconsin** 12,186 vs **44,210** · **Purdue** 9,992 vs **28,794**.
- ⚠️ **UIUC** 12,992 = in_state, and its breakdown has **NO `tuition_out_of_state`** — research UIUC's published
  non-resident sticker rather than leaving the in-state default.
**Fix (per public catalog, one PR — or a single fleet sweep):** stamp the NON-RESIDENT (out-of-state) sticker into the
scalar `tuition` (the value already in `cost_data.breakdown.tuition_out_of_state` — no new research, except UIUC),
keeping BOTH rates in the breakdown. Re-measure LIVE. (A choice between two PUBLISHED numbers, never a guess.) See
FLAG #6 — durable fix is residency-aware matching. Rule EXISTS (run 83) → compliance/repair.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 5. Georgetown · UW-Seattle · Yale + residuals — partial master's/professional tuition null — severity: high — first seen run 74 — 2026-06-26
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S (and some PROFESSIONAL) tier
ships a material null fraction (the matcher scores those graduate programs' budget-fit BLIND). Worst-first by null count
(live run 87): **Georgetown master's 6/79 (73!) + prof 10/17 (7)** [the FRESH #1169 catalog shipped 92% of its master's
tier null] · **UW-Seattle** 138/152 (14) + prof 6/7 · **Yale** 30/38 (8) + cert 0/3 · **UT-Austin** 121/128 (7) + prof
2/5 (3) · **UVA** 8/15 (7) [FRESH] · **Cornell** 79/85 (6) + prof 4/5 · **Penn** 57/63 (6) + cert 0/15 · **WashU** 4/10
(6) [FRESH] · **Harvard** 85/90 (5) · **UCSD** 54/59 (5) · **Brown** 1/5 (4) · **Dartmouth** 13/16 (3) · small (Columbia
prof 6/8, NYU prof 4/6). **Fix (per university, one PR):** group coverage by `degree_type`; stamp the published
per-program / per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD
or per-credit certificate, record `tuition` in `_standard.omitted` with a reason — never a silent blanket null, and
never the undergrad sticker copied onto a professional school that bills its own higher rate (BU's flat-rate exception
is verified). **PhD / certificate nulls EXCLUDED (largely funded / per-credit → legitimate omit-with-reason).**
Re-measure LIVE per tier. (The three FRESH seed-repairs — Georgetown / UVA / WashU — filled bachelor's + cip + who but
under-filled their master's tuition; close that tier in the same pass the matcher reads.)

---

# MEDIUM — `who_its_for` universal-depth starvation (root cause found) · reviews depth pass · bulk seeds

## 6. The 24 catalogs shipping `who_its_for` 0% — universal deep field un-done; UCLA REGRESSED; ROOT CAUSE = `p.who_its_for = None` — severity: medium — first seen run 84 — 2026-06-26
`who_its_for` ("Who it's for", a manifest field) is filled on **100% of EVERY program of 16 gold-complete catalogs**
(MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell · Stanford · Chicago · Penn · Berkeley · Vanderbilt ·
Dartmouth · **Georgetown[NEW]** · **UVA[NEW]** · **WashU[NEW]**) yet **0% on 24 others** — BU · Brown · CMU · Duke ·
Emory · Georgia Tech · JHU · NYU · Northwestern · Purdue · Rice · UT-Austin · **UCLA(REGRESSED 100%→0%)** · UCSD · UF ·
UIUC · Michigan · Notre Dame · USC · UW-Seattle · Wisconsin (+ the unbuilt/stranded UC-Davis / UC-Irvine / UNC seeds).
**ROOT CAUSE (run 86):** the `apply()` program loop in these modules contains the literal `p.who_its_for = None`, which
hard-nulls the field on every `replace=True` re-apply — so UCLA's `cip_code` follow-up re-applied the hard-nulling
module and REVERTED who_its_for from 100% to 0%. The who-COMPLETE catalogs instead assign `p.who_its_for =
_WHO_BY_SLUG.get(slug) or _WHO_BY_TYPE.get(degree_type)`. Unlike the coverage-gated deep fields
(`external_reviews`/`class_profile`/`faculty_contacts`/`tracks`), `who_its_for` is derivable for EVERY program from its
own published audience / fit material, so 0% is un-done depth. **Fix (per catalog, in the SAME pass that fills
`cip_code`/tuition):** REPLACE `p.who_its_for = None` with a real per-slug dict (`_WHO_BY_SLUG`) of field-specific 1–2
sentence statements of the applicant each program fits — gold-contrast bar, never a classification stub ("for students
interested in {field}"), never `= None`. Re-measure LIVE to ~100%, and re-check it did not regress the catalog's OTHER
live fields. Rule EXISTS (run 84 + the run-86 hard-null rule) → compliance/repair.

## 7. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 — 2026-06-26
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass. Sampled 12
details/catalog: 0/12 with `external_reviews` on Brown · Dartmouth · Emory · Georgetown · NYU · UT-Austin · UCLA · UCSD ·
Chicago · Michigan · Notre Dame · UW-Seattle (+ the fresh/seed catalogs); richest are Duke 50% · Princeton 50% ·
Caltech/CMU/Cornell/MIT 41% · Harvard/Penn 33%. **Calibrate — reviews are coverage-gated; do NOT fabricate.** **Enrich:**
on a structurally-clean catalog, run the reviews depth pass over programs WITH real third-party coverage (Poets&Quants /
U.S. News / GradReports / program outcomes reports) — program-specific summary + themes (incl. cautions) + resolvable
sources, no CIP-rollup strings, no synthesized-from-metadata reviews (miss #8) — and record `external_reviews` in
`_standard.omitted` with a reason where a program genuinely has no coverage.

## 8. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first), plus 50 more at 1–3 photos. **Enrich
(per university, one PR — after the HIGH tier clears):** a full real-named catalog with **field-specific
`description_text` on every program** + `who_its_for` (never `= None`) + real departments + published tuition
(non-resident scalar for publics) + `cip_code` · a working feed · a ≥4-photo verified gallery · reviews on coverable
programs · `_standard`. Pick a 0-photo seed once the higher tiers clear.

---

# CLEAN (structure + descriptions(pattern) + names + tuition-value-copy-down + exact-dup; no action) — verified LIVE run 87
- **Gold (description 0-control + `who_its_for` reference):** MIT (n=65, real "Science, Technology, and Society" major;
  `who_its_for` 100%; cert/PhD tiers null + grad rows at its own undergrad sticker AND `cip_code` null — MIT is NOT a
  tuition or `cip_code` reference, the fillers are; its lone `name_prefixed` one-liner is a pre-existing thin row, not a class).
- **LANDED LIVE & GOLD since run 86 (the empty-desc seed-repair wave deployed once the head-block cleared):**
  **Georgetown (190 programs)** · **UVA (100)** · **WashU (58)** — each real-named, field-specific descriptions,
  `cip_code` 100%, `who_its_for` 100%, non-resident tuition scalar (Georgetown 71,136 · UVA 59,512 · WashU private).
  (Their master's-tuition tier and reviews are the residual depth — entries #5/#7.)
- **`cip_code`-COMPLETE (the model for entry #3):** Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD · Georgia
  Tech · UT-Austin · UW-Seattle · Penn · Berkeley · Columbia · Vanderbilt · Dartmouth + Georgetown · UVA · WashU (100%
  in-sample).
- **`who_its_for`-COMPLETE (the model for entry #6):** MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell ·
  Stanford · Chicago · Penn · Berkeley · Vanderbilt · Dartmouth · **Georgetown[NEW]** · **UVA[NEW]** · **WashU[NEW]**
  (100% on every sampled program). ⚠️ UCLA remains OFF this list (regressed via `p.who_its_for = None`).
- **PUBLIC non-resident scalar CORRECT:** Georgia Tech · UT-Austin · Berkeley · UW-Seattle · **UVA[NEW]** (bachelor
  `tuition` = oos).
- **EXACT-DUPLICATE class CLEAN fleet-wide:** 0 raw `(program_name, degree_type)` repeats on all 40 catalogs.
- **Name-realness CLEAN fleet-wide:** ZERO CIP-rollup TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" /
  ", General/Other" / possessive "Bachelor's in" / bare-abbreviation names on all 40 catalogs.
- **Tuition-VALUE-copy-down CLEAN:** no NEW grad==undergrad copy-down beyond BU's VERIFIED flat full-time $69,870 grad rate.
- **DEPLOY PIPELINE UNBLOCKED:** single alembic head (`uncprof1`) on `origin/main` — the run-86 13-head block cleared.
