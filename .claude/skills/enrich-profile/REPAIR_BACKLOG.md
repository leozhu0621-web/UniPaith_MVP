# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / wrong-program content shipped live,
**OR the backend deploy pipeline itself blocked** so no repair can land) · **high** (residual
fabricated NAMES on an otherwise-rich catalog, exact-duplicate REAL rows shipped fleet-wide,
OR a matcher-core field STARVED / MIS-SIGNALED — a whole master's / professional tier null, a
catalog-wide 0% `tuition` or `cip_code`, a public's resident-rate scalar the budget veto reads
too low, or a correct repair stranded un-deployed in an unmerged PR) · **medium** (a UNIVERSAL
deep field — `who_its_for` — shipped 0% catalog-wide, institution-level seed below gold, or
dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog (**7,330 programs across 40 catalogs**), plus per-`degree_type` tuition
COVERAGE (read from the `tuition` scalar on every `/programs` list row), a per-program `cip_code`
coverage probe (12 sampled program details/catalog on `GET /programs/{id}`), a `who_its_for`
coverage probe (10 details/catalog, the NEW universal-depth measure), a sampled `external_reviews`
coverage probe, an exact-duplicate `(program_name, degree_type)` scan per catalog (raw +
degree-prefix-normalized), a name-realness scan (federal CIP rollup TITLE match + the "…and Related
Sciences/Services" / ", General/Other" / `(CIP NN.NN)` suffix tells), a public-vs-private bachelor
`tuition`-scalar-vs-`cost_data.breakdown` resident/non-resident probe on every public catalog, and a
campus-photo + posts-feed fetch on every institution (all 300). Gold MIT (n=65) is the description
0-control AND now the `who_its_for` reference (100%) — but NOT a tuition or `cip_code` control (it
ships null cert/PhD tiers, grad rows at its own undergrad sticker, AND null `cip_code`). The matcher's
tuition + cip consumption was read DIRECT from `program_features.py` + `matching.py` +
`net_price_service.py`. The repo's alembic head set (single head `utaustincip1` — pipeline HEALTHY),
the open-PR list, and each module's `cip_code` / `backfill_program_preferences` calls were read
direct (`git` / MCP).

_Last graded: 2026-06-25 (grader **run 84**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — a NEW universal-depth gate: `who_its_for`
("Who it's for") is NOT coverage-gated (every program can state who it fits), so a catalog-wide 0% is a
depth FAILURE, never an honest omission — gold fills it 100% on 11 catalogs, 29 ship 0%, 0 partial (the
dimension-skip fingerprint). **🟢 PROGRESS since run 83:** the enricher cleared `cip_code` + the public
non-resident scalar on **Georgia Tech, UT-Austin, UW-Seattle** (#1146/#1147/#1148) and `cip_code` +
MBA-tuition on **UCSD** (#1144); **Berkeley #1149 is OPEN/in-flight** (cip + non-resident scalar). The
worst tier is STILL the same matcher-core `cip_code` STARVATION (entry #1, ~22 mature catalogs null) then
the public-resident-tuition mis-signal (entry #2, 8 publics still in-state) then the master's-tier tuition
residual (entry #3). The NEW `who_its_for` starvation is entry #4. Structure / descriptions / NAMES /
exact-dups / tuition-VALUE-copy-down remain gold-clean fleet-wide (every gate 0). See CHANGELOG run 84._

## Fleet at a glance (run 84, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (7,330 total); 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo**). Seeding is **external**; the routine ENRICHES + REPAIRS only.
- **🟢 DEPLOY PIPELINE HEALTHY:** `origin/main` is a SINGLE alembic head (`utaustincip1`); the freshest enricher
  repair (UT-Austin #1148) is LIVE (cip `45.0201`, `tuition` 44,908 out-of-state), proving `alembic upgrade head`
  succeeds post-merge. No head conflict, no stranded-deploy. Berkeley #1149 is OPEN (in-flight, will clear its
  #1+#2 on merge) — that is normal in-flight work, NOT a stranded failure.
- **🔴 matcher-core `cip_code` STARVATION (worst tier — ~22 mature catalogs still null):** `cip_code` (the CIP
  join key to `ref_majors` + the field-66 vocabulary — the matcher's interest/field signal) is serialized on
  `GET /programs/{id}` and 100%-in-sample on **10 catalogs (Caltech · Princeton · Notre Dame · Chicago · UCLA ·
  UCSD[NEW] · Georgia Tech[NEW] · UT-Austin[NEW] · UW-Seattle[NEW] · Penn) + the 6 flagship 5-program seeds** while
  **~22 mature catalogs ship it NULL** — MIT(control) · Brown · Vanderbilt · Harvard · Yale · Columbia · Cornell ·
  Stanford · Duke · JHU · BU · CMU · NYU · USC · UF · UIUC · Michigan · Northwestern · Purdue · Rice · Dartmouth ·
  Emory (+ Berkeley, OPEN #1149). Only ~10 of 36 profile modules assign `p.cip_code` — yet every module already
  holds the IPEDS CIP per row (it gates breadth). One-assignment, no-research fill, highest matcher leverage in the
  fleet. Entry #1. Rule EXISTS (run 82 cip_code-coverage gate) → COMPLIANCE GAP, queued not re-added; durable
  enforcement is FLAG #3 (a coverage metric in the profile test).
- **🔴 PUBLIC-university resident-tuition scalar MIS-SIGNAL (matcher budget veto under-fires — 8 publics still
  in-state):** the CPEF budget feature reads the FLAT `program.tuition` scalar (`program_features.py`
  `tuition_usd_per_year`→`program.tuition` → `matching.py` budget BREAKER `p_tuition > s_budget` + graded
  `fit_range`), NOT the residency-aware net-price OUTPUT estimator. **FIXED since run 83 (now ship out-of-state):
  Georgia Tech 32,938 · UT-Austin 44,908 · UW-Seattle 44,460.** **STILL ship the IN-STATE rate** while
  `cost_data.breakdown` carries the higher out-of-state: **UCLA 15,202 (oos 49,402)** · **UCSD 16,758 (50,958)** ·
  **Michigan 17,864 (63,480)** · **Berkeley 16,347 (50,547, OPEN #1149)** · **Florida 6,381 (28,659)** · **Wisconsin
  12,186 (44,210)** · **Purdue 9,992 (28,794)** · **UIUC 12,992 (oos MISSING from breakdown)**. So an out-of-state /
  international applicant (the majority at a flagship public; ALL international pay non-resident) is scored
  affordable at 2.5–3.5× too low — the over-budget veto never fires. Entry #2. Rule EXISTS (run 83) → COMPLIANCE
  GAP, queued. ⚠️ **UIUC's breakdown has NO `tuition_out_of_state`** — the run-83 "copy from breakdown, no new
  research" instruction can't apply there, so research UIUC's published non-resident sticker (publics publish it)
  rather than leaving the in-state default. Durable fix is FLAG #6 (residency-aware budget matching, CODE).
- **🟡 master's / professional-tier tuition residual (matcher grad-budget signal):** structurally-clean catalogs
  whose bachelor's tier is 100% but whose MASTER'S (and some PROFESSIONAL) tier ships a material null fraction.
  Worst (live run 84): **UW-Seattle master's 138/152 (14 null)** + prof 6/7 · **USC 249/261 (12)** · **Vanderbilt
  15/25 (10)** + prof 4/6 · **Yale 30/38 (8)** · **UT-Austin 121/128 (7)** + prof 2/5 · **Cornell 79/85 (6)** +
  prof 4/5 · **Penn 57/63 (6)** · **NYU 227/232 (5)** + prof 4/6 · **Harvard 85/90 (5)** · **UCSD 54/59 (5)** ·
  **Brown 1/5 (4)** · **Berkeley 71/74 (3)** + small (UCLA 144/145, Michigan 98/99, Notre Dame 23/24, Columbia
  prof 6/8, Stanford prof 0/2). These publish a per-program / per-credit rate, rarely funded → stamp the published
  rate. Entry #3. **PhD / certificate nulls EXCLUDED — largely legitimate** (funded research doctorates /
  per-credit certificates → omit-with-reason; e.g. Harvard cert 0/58, Stanford cert 0/53, MIT cert 0/10).
- **🟡 NEW — `who_its_for` UNIVERSAL-depth STARVATION (29 catalogs at 0%):** `who_its_for` ("Who it's for", a
  manifest field) is filled on **100% of EVERY program of 11 gold-complete catalogs (MIT · Princeton · Caltech ·
  Harvard · Yale · Columbia · Cornell · Stanford · Chicago · Penn · UCLA)** yet **0% on 29 others** — including the
  freshly matcher-core-repaired UT-Austin / UW-Seattle / Georgia Tech / UCSD — a stark **11-full / 29-empty /
  0-partial** split that is the dimension-skip fingerprint (the enricher's cip/tuition repair passes don't add it).
  Unlike `external_reviews`/`class_profile`/`faculty_contacts`/`tracks` (coverage-gated — sparse even on gold), it
  is derivable for EVERY program from its own published audience/fit material, so 0% is un-done depth, never an
  honest omission. Entry #4. NEW rule this run (universal-depth gate).
- **🟢 EXACT-DUPLICATE REAL rows CLEAN fleet-wide (run-82 #3 stays cleared):** the raw `(program_name, degree_type)`
  scan returns **ZERO** on all 40 catalogs. (The degree-prefix-normalized variant shows benign collisions that are
  REAL distinct credentials — e.g. USC "Bachelor of Arts in Chemistry" + "Bachelor of Science in Chemistry" — NOT
  duplicates.) FLAG #1 (build-union dedup + name-uniqueness CI gate) remains the durable guard.
- **🟢 STRUCTURE + DESCRIPTIONS + NAMES + TUITION-VALUE-COPY-DOWN clean fleet-wide (verified LIVE):** every mature
  catalog scores 0 on `machine_artifacts` / `template_slot_artifacts` / `scrape_debris` / `frame_abs150`; the
  name-realness scan finds ZERO federal CIP-rollup TITLEs / `(CIP NN.NN)` / "…and Related Sciences/Services" /
  ", General/Other" / bare-abbreviation names; no NEW undergrad-sticker copy-down (BU's verified flat $69,870 grad
  rate, prof tier distinct, remains the only grad==undergrad exception). Descriptions are field-specific +
  well-sourced (e.g. UT-Austin Anthropology cites `liberalarts.utexas.edu`).
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority, calibrate — do NOT pressure fabrication):**
  0/12 sampled on Dartmouth · Emory · Georgia Tech · Northwestern · Stanford · UT-Austin · Michigan · UW-Seattle ·
  Notre Dame · Vanderbilt; ≤4/12 on most of the rest (gold MIT itself 5/12). Reviews are coverage-gated (many
  programs honestly have no third-party coverage), so this is a depth-pass priority on structurally-clean catalogs
  (it is, fleet-wide), NOT a fabrication mandate. Entry #5. (miss #8 + STRUCTURE-BEFORE-DEPTH order.)

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The catalog build dedups on `slug`, not on the rendered `(program_name, degree_type)`, and the per-module
   self-check (`_catalog_errors`) never asserts name uniqueness.** The live class is CLEAN this run (0 dups), but
   the gate gap remains — a future build that re-derives a curated + IPEDS row to the same name could re-ship the
   exact-duplicate class undetected. Durable fix: dedup the build UNION on `(program_name, degree_type)` (keep the
   richer row) + promote a `(program_name, degree_type)`-uniqueness assertion into `test_anti_stub_gate.py` over
   the MERGED catalog. App/test code. (carried.)
2. **The enforced anti-stub gate is DESCRIPTION-only and never scans NAMES.** Names are clean fleet-wide THIS run,
   but the gate gap remains: a future verbatim CIP-ROLLUP name would ship undetected. Durable fix = a name-realness
   metric (FAIL any `program_name`/`department` equal to a federal CIP rollup TITLE or carrying the "…and Related
   Sciences/Services" suffix / `(CIP NN.NN)` code), parametrized over `CERTIFIED_CLEAN`, with the verified-real-major
   carve-out (e.g. "{Region} Area Studies" is a real degree). App/test code. (carried.)
3. **`cip_code` is serialized on `GET /programs/{id}` but populated on only ~10 of 36 modules — there is NO enforced
   coverage gate.** Durable fix = a `cip_code` coverage metric in the profile test (assert ~100% per
   `CERTIFIED_CLEAN` catalog, omit-with-reason recorded for the rare uncodeable program). The enricher fix is the
   run-82 rulebook rule (one assignment per module); the gate makes it durable. App/test code. (carried.)
4. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric.** Durable fix =
   a `tuition_value_artifacts` metric + per-tier coverage in the profile test, keying the copy-down FAIL on a
   professional row at the flat undergrad sticker ONLY when that professional SCHOOL publishes a distinct higher
   rate (must NOT fail `grad==undergrad` unconditionally — it false-flags BU's verified flat full-time rate). A
   public-scalar sub-check (FAIL when the bachelor `tuition` scalar equals `breakdown.tuition_in_state` while a
   higher `tuition_out_of_state` exists) would make entry #2 durable too. App/test code. (carried.)
5. **Stranded enricher PRs (open, unmerged = failed/superseded enricher runs):** #1149 (Berkeley cip+tuition) is
   the live in-flight one (actionable, not stranded). The rest — #1081 (Purdue), #1064 (Rice), #769 (UCLA de-fab),
   #515/#503 (Harvard reviews), #499/#489 (CMU reviews), #439 (MIT), #420 (Penn), #403 (Harvard) — appear
   SUPERSEDED by later merged repairs; a human should close them or confirm whether any carries an un-landed fix.
   Non-blocking.
6. **The CPEF budget feature is RESIDENCY-BLIND: `matching.py` reads the single `program.tuition` scalar for the
   budget breaker + affordability fit, with no in-state/out-of-state branch on the student's residency / country.**
   The enricher's non-resident-scalar default (entry #2) is the stopgap; the durable fix is residency-aware
   matching — read `tuition_in_state` vs `tuition_out_of_state` from `cost_data.breakdown` keyed on the student's
   residency, the way `net_price_service.py` already prefers out-of-state for its OUTPUT estimate. App code —
   highest-leverage matcher fix once the scalar default lands fleet-wide. (carried.)

---

# HIGH — matcher-core `cip_code` STARVATION — clear FIRST

## 1. The ~22 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 · 2026-06-25
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the
field-66 vocabulary (the interest/field signal alongside the `description_text` embedding). It is serialized on
`GET /programs/{id}` and 100%-in-sample on **10 catalogs (Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD ·
Georgia Tech · UT-Austin · UW-Seattle · Penn) + the 6 flagship seeds** but **NULL on ~22 mature catalogs** — MIT ·
Brown · Vanderbilt · Harvard · Yale · Columbia · Cornell · Stanford · Duke · JHU · BU · CMU · NYU · USC · UF · UIUC ·
Michigan · Northwestern · Purdue · Rice · Dartmouth · Emory (+ Berkeley, OPEN #1149) — so the matcher scores those
~5,000 programs field-blind on the CIP key. Only ~10 of 36 profile modules assign `p.cip_code`. **Fix (one fleet
sweep, or per catalog):** in each catalog's build, stamp `p.cip_code = spec.get("cip")` (the IPEDS CIP already used
for the breadth cross-check), exactly as the 10 fillers do — never a guess, omit-with-reason only for a genuinely
uncodeable interdisciplinary program. Re-measure LIVE per catalog to ~100%. (One assignment per module, no new
research — highest matcher leverage in the fleet.) Rule EXISTS (run 82) → compliance/repair, not a new rule.

---

# HIGH — PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 2. The 8 public catalogs still shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 · 2026-06-25
The CPEF budget feature reads the FLAT `program.tuition` scalar (`program_features.py` → `matching.py` budget
breaker `p_tuition > s_budget` + graded affordability `fit_range`), NOT the residency-aware net-price OUTPUT
estimator. **CLEARED since run 83: Georgia Tech · UT-Austin · UW-Seattle (now out-of-state).** STILL in-state while
`cost_data.breakdown` carries the higher non-resident rate:
- **UCLA** 15,202 vs **49,402** · **UCSD** 16,758 vs **50,958** · **Michigan** 17,864 vs **63,480** · **Berkeley**
  16,347 vs **50,547** (OPEN #1149) · **Florida** 6,381 vs **28,659** · **Wisconsin** 12,186 vs **44,210** ·
  **Purdue** 9,992 vs **28,794** · **UIUC** 12,992 vs **(out-of-state MISSING from breakdown)**.
**Fix (per public catalog, one PR — or a single fleet sweep):** stamp the NON-RESIDENT (out-of-state) sticker into
the scalar `tuition` (the value already in `cost_data.breakdown.tuition_out_of_state` — no new research), keeping
BOTH rates in the breakdown. ⚠️ **UIUC is the exception — its breakdown has NO out-of-state value**, so research
UIUC's published non-resident sticker (publics publish it) rather than leaving the in-state default. Re-measure
LIVE: each public's bachelor `tuition` should read the out-of-state figure. (A choice between two PUBLISHED numbers,
never a guess — omit-never-guess intact.) See FLAG #6 — durable fix is residency-aware matching. Rule EXISTS
(run 83) → compliance/repair.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 3. UW-Seattle · USC · Vanderbilt · Yale + residuals — partial master's/professional tuition null — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S (and some PROFESSIONAL)
tier ships a material null fraction (the matcher scores those graduate programs' budget-fit BLIND). Worst-first
(live run 84): **UW-Seattle** master's 138/152 (14) + prof 6/7 · **USC** 249/261 (12) · **Vanderbilt** 15/25 (10) +
prof 4/6 · **Yale** 30/38 (8) · **UT-Austin** 121/128 (7) + prof 2/5 · **Cornell** 79/85 (6) + prof 4/5 · **Penn**
57/63 (6) · **NYU** 227/232 (5) + prof 4/6 · **Harvard** 85/90 (5) · **UCSD** 54/59 (5) · **Brown** 1/5 (4) ·
**Berkeley** 71/74 (3) · small (UCLA 144/145, Michigan 98/99, Notre Dame 23/24, Columbia prof 6/8, Stanford prof
0/2). **Fix (per university, one PR):** group coverage by `degree_type`; stamp the published per-program / per-credit
rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit
certificate, record `tuition` in `_standard.omitted` with a reason — never a silent blanket null, and never the
undergrad sticker copied onto a professional school that bills its own higher rate (BU's flat-rate Law is the
verified exception). **PhD / certificate nulls EXCLUDED (largely funded / per-credit → legitimate omit-with-reason).**
Re-measure LIVE per tier.

---

# MEDIUM — NEW: `who_its_for` universal-depth starvation · reviews depth pass · seeds

## 4. The 29 catalogs shipping `who_its_for` 0% — universal deep field un-done — severity: medium — first seen run 84 · 2026-06-25
`who_its_for` ("Who it's for", a manifest field) is filled on **100% of EVERY program of 11 gold-complete catalogs**
(MIT · Princeton · Caltech · Harvard · Yale · Columbia · Cornell · Stanford · Chicago · Penn · UCLA) yet **0% on 29
others** — BU · Brown · CMU · Dartmouth · Duke · Emory · Georgetown · Georgia Tech · JHU · NYU · Northwestern ·
Purdue · Rice · UT-Austin · Berkeley · UCSD · UC-Davis · UC-Irvine · Florida · UIUC · Michigan · UNC · Notre Dame ·
USC · UVA · UW-Seattle · Wisconsin · Vanderbilt · WashU (11-full / 29-empty / **0-partial** — the dimension-skip
fingerprint; the cip/tuition repair passes don't add it). Unlike the coverage-gated deep fields (`external_reviews`/
`class_profile`/`faculty_contacts`/`tracks` — sparse even on gold), `who_its_for` is derivable for EVERY program
from its own published audience / fit / "is this program right for you" material, so 0% is un-done depth, not an
honest omission. **Fix (per catalog, in the SAME pass that fills `cip_code`/tuition):** stamp a field-specific 1–2
sentence statement of the applicant each program fits (background, goals, readiness) — gold-contrast bar, never a
classification stub ("for students interested in {field}"); record `_standard.omitted` only for a genuinely
audience-less program (effectively never). Re-measure LIVE to ~100%. Rule is NEW this run (universal-depth gate).

## 5. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 · 2026-06-19
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order now unblocks the reviews depth pass.
Sampled 12 details/catalog: 0/12 with `external_reviews` on Dartmouth · Emory · Georgia Tech · Northwestern ·
Stanford · UT-Austin · Michigan · UW-Seattle · Notre Dame · Vanderbilt; ≤4/12 on the rest (gold MIT itself 5/12).
**Calibrate — reviews are coverage-gated; do NOT fabricate.** **Enrich:** on a structurally-clean catalog, run the
reviews depth pass over programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports / program
outcomes reports) — program-specific summary + themes (incl. cautions) + resolvable sources, no CIP-rollup strings,
no synthesized-from-metadata reviews (miss #8) — and record `external_reviews` in `_standard.omitted` with a reason
where a program genuinely has no coverage.

## 6. The 6 flagship seeds (5 programs each) — EMPTY who_its_for + 0% reviews + DEAD FEED + partial gallery — severity: medium — first seen run 57 · 2026-06-18
**Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Washington U-St Louis** each ship 5 flagship rows with
**DEAD FEED** (posts=0 — the only live dead feeds in the fleet), 0% `who_its_for`, and partial galleries (UC-Davis 3 ·
UNC 3 · WashU 3 photos — below the ≥4 gold gate; Georgetown 4 · UC-Irvine 4 · UVA 5). (`cip_code` IS populated 5/5 on
these seeds.) **Enrich (per university, one PR):** a full real-named catalog + per-credential researched descriptions
+ `who_its_for` + real departments + published tuition (per credential level, non-resident scalar for the public ones)
+ `cip_code` per row + a working feed + a ≥4-photo verified gallery + reviews on coverable programs, then deepen.

## 7. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first), plus ~53 more at 1–3 photos.
**Enrich (per university, one PR):** a full real-named catalog + per-credential field-specific descriptions +
`who_its_for` + real departments + published tuition (non-resident scalar for publics) + `cip_code` · a working feed ·
a ≥4-photo verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions + names + tuition-value-copy-down + exact-dup; no action) — verified LIVE run 84
- **Gold (description 0-control + `who_its_for` reference):** MIT (n=65, 0 on every description metric; real "Science,
  Technology, and Society" major; `who_its_for` 100%; cert/PhD tiers null + grad rows at its own undergrad sticker —
  MIT is NOT a tuition reference; AND `cip_code` null — MIT is NOT a `cip_code` reference, the 10 fillers are).
- **`cip_code`-COMPLETE (the model for entry #1):** Caltech · Princeton · Notre Dame · Chicago · UCLA · UCSD ·
  Georgia Tech · UT-Austin · UW-Seattle · Penn + the 6 flagship seeds (100% in-sample).
- **`who_its_for`-COMPLETE (the model for entry #4):** MIT · Princeton · Caltech · Harvard · Yale · Columbia ·
  Cornell · Stanford · Chicago · Penn · UCLA (100% on every sampled program).
- **PUBLIC non-resident scalar CORRECT:** Georgia Tech · UT-Austin · UW-Seattle (bachelor `tuition` = out-of-state).
- **EXACT-DUPLICATE class CLEAN fleet-wide:** 0 raw `(program_name, degree_type)` repeats on all 40 catalogs (the
  normalized-variant collisions are REAL distinct credentials — BA vs BS in the same field — not duplicates).
- **Name-realness CLEAN fleet-wide:** ZERO CIP-rollup TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" /
  ", General/Other" / bare-abbreviation names on ALL 40 catalogs.
- **Tuition-VALUE-copy-down CLEAN:** no NEW grad==undergrad copy-down beyond BU's VERIFIED flat full-time $69,870
  grad rate (prof tier distinct).
