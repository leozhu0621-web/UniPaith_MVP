# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / wrong-program content shipped live,
**OR the backend deploy pipeline itself blocked** so no repair can land) · **high** (residual
fabricated NAMES on an otherwise-rich catalog, exact-duplicate REAL rows shipped fleet-wide,
OR a matcher-core field STARVED / MIS-SIGNALED — a whole master's / professional tier null, a
catalog-wide 0% `tuition` or `cip_code`, a public's resident-rate scalar the budget veto reads
too low, or a correct repair stranded un-deployed in an unmerged PR) · **medium** (institution-level
seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog (7,290 programs across 40 catalogs), plus per-`degree_type` tuition COVERAGE
(read from the `tuition` scalar carried on every `/programs` list row), a **per-program `cip_code`
coverage probe** (12 sampled program details/catalog on `GET /programs/{id}`), a sampled
`external_reviews` coverage probe (same details), an exact-duplicate `(program_name, degree_type)`
scan per catalog (raw + degree-prefix-normalized), a name-realness scan (federal CIP rollup TITLE
match + the "…and Related Sciences/Services" / ", General/Other" / `(CIP NN.NN)` suffix tells), a
public-vs-private bachelor-tuition + `cost_data.breakdown` resident/non-resident probe, and a
campus-photo + posts-feed fetch on every institution (all 300). Gold MIT (n=65) is the description
0-control — but NOT a tuition or `cip_code` control (it ships null cert/PhD tiers, grad rows at its
own undergrad sticker, AND null `cip_code`). The matcher's tuition consumption was read DIRECT from
`program_features.py` + `matching.py` + `net_price_service.py`. The repo's alembic head set, the
open-PR list, the Deploy-Backend run statuses, and each module's `cip_code` /
`backfill_program_preferences` calls were read direct (`git` / MCP).

_Last graded: 2026-06-25 (grader **run 83**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — a PUBLIC-university non-resident-tuition
scalar rule (the matcher reads the flat `tuition` scalar for its budget veto + affordability fit, and
every public ships the IN-STATE rate → the veto under-fires 2.5–3.5× for the out-of-state + international
majority). **🟢 TWO worst tiers CLEARED since run 82:** (a) the run-82 #3 exact-duplicate-REAL-row class
(43 rows / 22 catalogs) now scans to **ZERO** fleet-wide (raw AND normalized) — the enrichment rebuilds
re-deduped; (b) UCLA `cip_code` 0→100% (12/12 live, #1141/#1142) and NYU master's tuition filled (#1139
deployed, 194→227/232). Penn `cip_code` is mid-deploy (#1143 Deploy-Backend in_progress) — pending, NOT a
defect. **NEW worst tier = the same matcher-core `cip_code` STARVATION (entry #1, ~28 mature catalogs still
null)** then the NEW public-resident-tuition mis-signal (entry #2) then the master's-tier tuition residual
(entry #3, much smaller post-#1139). Structure / descriptions / NAMES / tuition-VALUE-copy-down are
gold-clean fleet-wide. See CHANGELOG run 83._

## Fleet at a glance (run 83, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (7,290 total); 260 are bare institution-level stubs**
  (0 programs, dead feed, **34 with ZERO campus photo**). Seeding is **external**; the routine ENRICHES + REPAIRS only.
- **🟢 DEPLOY PIPELINE HEALTHY:** `origin/main` Deploy-Backend is succeeding (UCLA #1141/#1142 + NYU #1139
  deployed green); the only in-flight run is Penn #1143 (`04717b8`, in_progress — its `cip_code` + MPH-tuition
  fill is pending, which is why Penn still reads `cip_code` 0/12 LIVE — a deploy-lag, NOT a missed assignment:
  `penn_profile.py:4643` DOES `p.cip_code = spec.get("cip")`).
- **🔴 matcher-core `cip_code` STARVATION (worst tier — ~28 mature catalogs still null):** `cip_code` (the CIP
  join key to `ref_majors` + the field-66 vocabulary — the matcher's interest/field signal) is serialized on
  `GET /programs/{id}` and populated 100%-in-sample on **6 catalogs (Caltech · Princeton · Notre Dame · Chicago ·
  UCLA[NEW] · the 6 flagship 5-program seeds)** while **~28 mature catalogs ship it NULL** — MIT · Brown ·
  Vanderbilt · Harvard · Yale · Columbia · Cornell · Stanford · Duke · JHU · BU · CMU · NYU · USC · UW-Seattle ·
  UT-Austin · Berkeley · UCSD · UF · UIUC · Michigan · Northwestern · Purdue · Rice · GT · Dartmouth · Emory
  (+ Penn, mid-deploy). The repo confirms only **6 of 36 profile modules** assign `p.cip_code` — yet every
  module already holds the IPEDS CIP per row (it gates breadth). One-assignment, no-research fill, highest matcher
  leverage in the fleet. Entry #1. Rule EXISTS (run 82 cip_code-coverage gate) → COMPLIANCE GAP, queued not
  re-added; durable enforcement is FLAG #3 (a coverage metric in the profile test).
- **🔴 NEW — PUBLIC-university resident-tuition scalar MIS-SIGNAL (matcher budget veto under-fires for the
  out-of-state + international MAJORITY):** the CPEF budget feature reads the FLAT `program.tuition` scalar
  (`program_features.py` `tuition_usd_per_year`→`program.tuition` → `matching.py` budget BREAKER `p_tuition >
  s_budget` + graded `fit_range`), NOT the residency-aware net-price OUTPUT estimator. Every one of the **11
  public catalogs ships the IN-STATE resident rate** as that scalar while its `cost_data.breakdown` correctly
  carries the higher out-of-state rate: **UCLA 15,202 (out-of-state 49,402)** · **UT-Austin 11,688 (44,908)** ·
  **Michigan 17,864 (63,480)** · UW-Seattle 13,406 · Florida 6,381 · Berkeley 16,347 · UCSD 16,758 · Wisconsin
  12,186 · UIUC 12,992 · Purdue 9,992 · Georgia Tech 10,512. So an out-of-state / international applicant (the
  majority at a flagship public; ALL international pay non-resident) is scored as comfortably affordable at a
  number 2.5–3.5× too low — the over-budget veto never fires. Entry #2. NEW rule this run (public non-resident
  scalar); durable fix is FLAG #6 (residency-aware budget matching, CODE).
- **🟡 master's / professional-tier tuition residual (matcher grad-budget signal) — much smaller post-#1139:**
  structurally-clean catalogs whose bachelor's tier is 100% but whose MASTER'S (and some PROFESSIONAL) tier ships
  a material null fraction. Worst (live run 83): **UW-Seattle master's 138/152 (14 null)** + prof 6/7 ·
  **UT-Austin 115/128 (13)** + prof 2/5 · **USC 249/261 (12)** · **Vanderbilt 15/25 (10, FRESH)** + prof 4/6 ·
  **Yale 30/38 (8)** · **BU 160/167 (7)** + prof 20/25 (5) · **Penn 56/63 (7, mid-deploy #1143)** · **UCSD 53/60
  (7)** · **Cornell 79/85 (6)** · **Harvard 85/90 (5)** · **NYU 227/232 (5, residual after #1139)** + prof 4/6 ·
  **Brown 1/5 (4, FRESH)** · **Berkeley 71/74 (3)**. These publish a per-program / per-credit rate, rarely funded
  → stamp the published rate. **CLEARED since run 82: UCLA (98→144/146) by #1133/#1141, NYU master's by #1139.**
  Entry #3.
- **🟢 EXACT-DUPLICATE REAL rows CLEARED fleet-wide (was run-82 #3, 43 rows / 22 catalogs):** the `(program_name,
  degree_type)` scan (raw AND degree-prefix-normalized) now returns **ZERO** on all 40 catalogs — the JHU/UCSD/BU/
  NYU/UIUC/Emory/Purdue/… pairs are gone, and the corroborating `frame_abs150` artifacts that accompanied each dup
  pair are absent (only 3 benign singletons remain: Yale 1, Northwestern 1, Chicago 1). The enrichment rebuilds
  re-deduped. (FLAG #1 — a build-union dedup + name-uniqueness CI gate — remains the durable guard so a future
  build cannot re-introduce it; but the live class is clean.)
- **🟢 STRUCTURE + DESCRIPTIONS + NAMES + TUITION-VALUE-COPY-DOWN clean fleet-wide (verified LIVE):** every mature
  catalog scores 0 on `machine_artifacts` / `template_slot_artifacts` / `scrape_debris`; the name-realness scan
  finds ZERO federal CIP-rollup TITLEs / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other" (the
  3 "Area Studies" heuristic hits — USC "East Asian Area Studies", UW "Scandinavian Area Studies" — are REAL named
  degrees, not rollups); 0 bare-abbreviation names; no NEW undergrad-sticker copy-down (BU's verified flat
  $69,870 grad rate, prof tier distinct, remains the only grad==undergrad exception).
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority, calibrate — do NOT pressure fabrication):**
  sampled 12 program details/catalog — 0/12 with `external_reviews` on Brown · Emory · Georgia Tech · Northwestern ·
  Purdue · UT-Austin · Berkeley · UF · UIUC · Michigan · USC · UW-Seattle · Vanderbilt; ≤4/12 on most of the rest
  (gold MIT itself 3/12). Reviews are coverage-gated (many programs honestly have no third-party coverage), so this
  is a depth-pass priority on catalogs whose STRUCTURE is already clean (it is, fleet-wide), NOT a fabrication
  mandate. Entry #4. (miss #8 + STRUCTURE-BEFORE-DEPTH order.)
- **🟡 PhD-tier + certificate-tier tuition null is LARGELY LEGITIMATE (funded research doctorates / per-credit
  certificates → omit-with-reason) — do NOT pressure fabrication:** Vanderbilt phd 0/15, Yale 0/66, Penn 0/46,
  NYU 0/96, BU 0/78, Berkeley 0/63, Columbia 0/44, GT 0/39, Rice 0/29, Northwestern 0/24, Harvard 0/23;
  certificate 0/N on Harvard/Stanford/BU/Penn/Yale/MIT. Peers prove SOME publish a flat doctoral/cert rate
  (UW-Seattle/UT-Austin/USC/Cornell phd 100%), so a tier null beside a peer that fills it is a VERIFY trigger —
  but treat PhD/cert nulls as notes, NOT a repair priority, and never the undergrad sticker copied down.

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
3. **`cip_code` is serialized on `GET /programs/{id}` but populated on only 6 of 36 modules — there is NO enforced
   coverage gate.** Durable fix = a `cip_code` coverage metric in the profile test (assert ~100% per
   `CERTIFIED_CLEAN` catalog, omit-with-reason recorded for the rare uncodeable program). The enricher fix is the
   run-82 rulebook rule (one assignment per module); the gate makes it durable. App/test code. (carried.)
4. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric.** Durable fix =
   a `tuition_value_artifacts` metric + per-tier coverage in the profile test, keying the copy-down FAIL on a
   professional row at the flat undergrad sticker ONLY when that professional SCHOOL publishes a distinct higher
   rate (must NOT fail `grad==undergrad` unconditionally — it false-flags BU's verified flat full-time rate).
   App/test code. (carried.)
5. **Stranded enricher PRs (open, unmerged = failed enricher runs):** the run-82 actionable one (#1139 NYU tuition)
   is now MERGED + deployed. Remaining open repair PRs — #1081 (Purdue), #1064 (Rice), #769 (UCLA de-fab), #515/#503
   (Harvard reviews), #499/#489 (CMU reviews) — appear SUPERSEDED by later merged repairs (UCLA/NYU/Penn all
   landed via newer PRs); a human should close them or confirm whether any carries an un-landed fix. Non-blocking.
6. **NEW — the CPEF budget feature is RESIDENCY-BLIND: `matching.py` reads the single `program.tuition` scalar for
   the budget breaker + affordability fit, with no in-state/out-of-state branch on the student's residency /
   country.** The enricher's non-resident-scalar default (entry #2 / new rule) is the stopgap; the durable fix is
   residency-aware matching — read `tuition_in_state` vs `tuition_out_of_state` from `cost_data.breakdown` keyed on
   the student's residency, the way `net_price_service.py` already prefers out-of-state for its OUTPUT estimate.
   App code — highest-leverage matcher fix once the scalar default lands. (NEW this run.)

---

# HIGH — matcher-core `cip_code` STARVATION — clear FIRST

## 1. The ~28 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 · 2026-06-25
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the
field-66 vocabulary (the interest/field signal alongside the `description_text` embedding). It is serialized on
`GET /programs/{id}` and populated 100%-in-sample on **6 catalogs (Caltech · Princeton · Notre Dame · Chicago ·
UCLA · the 6 flagship 5-program seeds)** but **NULL on ~28 mature catalogs** — MIT · Brown · Vanderbilt · Harvard ·
Yale · Columbia · Cornell · Stanford · Duke · JHU · BU · CMU · NYU · USC · UW-Seattle · UT-Austin · Berkeley ·
UCSD · UF · UIUC · Michigan · Northwestern · Purdue · Rice · Georgia Tech · Dartmouth · Emory (+ Penn, mid-deploy
#1143) — so the matcher scores those ~6,000 programs field-blind on the CIP key. The repo confirms only 6 of 36
profile modules assign `p.cip_code`. **Fix (one fleet sweep, or per catalog):** in each catalog's build, stamp
`p.cip_code = spec.get("cip")` (the IPEDS CIP already used for the breadth cross-check), exactly as the 6 fillers
do — never a guess, omit-with-reason only for a genuinely uncodeable interdisciplinary program. Re-measure LIVE
per catalog to ~100%. (One assignment per module, no new research — highest matcher leverage in the fleet.) Rule
EXISTS (run 82) → this is a compliance/repair, not a new rule.

---

# HIGH — NEW: PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 2. The 11 public catalogs shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 · 2026-06-25
The CPEF budget feature reads the FLAT `program.tuition` scalar (`program_features.py` →
`matching.py` budget breaker `p_tuition > s_budget` + graded affordability `fit_range`), NOT the residency-aware
net-price OUTPUT estimator. Every public catalog ships the IN-STATE resident rate as that scalar while
`cost_data.breakdown` correctly carries the higher non-resident rate — so an out-of-state / international applicant
(the majority at a flagship public; ALL international pay non-resident) is scored affordable at a number 2.5–3.5×
too low, and the over-budget veto never fires:
- **UCLA** `tuition` 15,202 vs breakdown out-of-state **49,402** · **UT-Austin** 11,688 vs **44,908** ·
  **Michigan** 17,864 vs **63,480** · **UW-Seattle** 13,406 · **Florida** 6,381 · **Berkeley** 16,347 ·
  **UCSD** 16,758 · **Wisconsin** 12,186 · **UIUC** 12,992 · **Purdue** 9,992 · **Georgia Tech** 10,512.
**Fix (per public catalog, one PR — or a single fleet sweep):** stamp the NON-RESIDENT (out-of-state) sticker into
the scalar `tuition` (the value already present in `cost_data.breakdown.tuition_out_of_state` — no new research),
keeping BOTH rates in the breakdown. Re-measure LIVE: each public's bachelor `tuition` should read the
out-of-state figure. (This is a choice between two PUBLISHED numbers, never a guess — omit-never-guess intact.)
See FLAG #6 — the durable fix is residency-aware matching; the non-resident scalar is the matcher-correct default
until that lands. Rule is NEW this run.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 3. UW-Seattle · UT-Austin · USC · Vanderbilt + residuals — partial master's/professional tuition null — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S (and some PROFESSIONAL)
tier ships a material null fraction (the matcher scores those graduate programs' budget-fit BLIND). Worst-first
(live run 83): **UW-Seattle** master's 138/152 (14) + prof 6/7 · **UT-Austin** 115/128 (13) + prof 2/5 · **USC**
249/261 (12) · **Vanderbilt** 15/25 (10, FRESH) + prof 4/6 · **Yale** 30/38 (8) · **BU** 160/167 (7) + prof 20/25
(5) · **Penn** 56/63 (7, mid-deploy #1143) · **UCSD** 53/60 (7) · **Cornell** 79/85 (6) · **Harvard** 85/90 (5) ·
**NYU** 227/232 (5, residual after #1139) + prof 4/6 · **Brown** 1/5 (4, FRESH) · **Berkeley** 71/74 (3) ·
Michigan 98/99 (1) · Notre Dame 23/24 (1). **CLEARED since run 82: UCLA (now 144/146) + NYU master's (#1139).**
**Fix (per university, one PR):** group coverage by `degree_type`; stamp the published per-program / per-credit
rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit
certificate, record `tuition` in `_standard.omitted` with a reason — never a silent blanket null, and never the
undergrad sticker copied onto a professional school that bills its own higher rate (BU's flat-rate Law is the
verified exception). **PhD / certificate nulls EXCLUDED (largely funded / per-credit → legitimate omit-with-reason).**
Re-measure LIVE per tier.

---

# MEDIUM — reviews depth-pass · flagship seeds · institution-level seeds (seeding is external)

## 4. `external_reviews` depth pass on the (now structurally-clean) mature catalogs — severity: medium — first seen run 65 · 2026-06-19
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order now unblocks the reviews depth pass.
Sampled 12 details/catalog: 0/12 with `external_reviews` on Brown · Emory · Georgia Tech · Northwestern · Purdue ·
UT-Austin · Berkeley · UF · UIUC · Michigan · USC · UW-Seattle · Vanderbilt; ≤4/12 on the rest (gold MIT itself
3/12). **Calibrate — reviews are coverage-gated; do NOT fabricate.** **Enrich:** on a structurally-clean catalog,
run the reviews depth pass over programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports /
program outcomes reports) — program-specific summary + themes (incl. cautions) + resolvable sources, no CIP-rollup
strings, no synthesized-from-metadata reviews (miss #8) — and record `external_reviews` in `_standard.omitted`
with a reason where a program genuinely has no coverage.

## 5. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Washington U-St Louis** each ship 5 flagship rows
with bare abbreviation names, **DEAD FEED** (posts=0 — the only live dead feeds in the fleet), and partial galleries
(UC-Davis 3 · UNC 3 · WashU 3 photos — below the ≥4 gold gate; Georgetown 4 · UC-Irvine 4 · UVA 5). (`cip_code` IS
populated 5/5 on these seeds.) **Enrich (per university, one PR):** a full real-named catalog + per-credential
researched descriptions + real departments + published tuition (per credential level, non-resident scalar for the
public ones) + `cip_code` per row + a working feed + a ≥4-photo verified gallery, then deepen.

## 6. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **34 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first), plus ~53 more at 1–3 photos.
**Enrich (per university, one PR):** a full real-named catalog + per-credential field-specific descriptions + real
departments + published tuition (non-resident scalar for publics) + `cip_code` · a working feed · a ≥4-photo
verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions + names + tuition-value-copy-down + exact-dup; no action) — verified LIVE run 83
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric; real "Science, Technology, and
  Society" major; cert/PhD tiers null + grad rows at its own undergrad sticker — MIT is NOT a tuition reference;
  AND `cip_code` null — MIT is NOT a `cip_code` reference, the 6 fillers are).
- **`cip_code`-COMPLETE (the model for entry #1):** Caltech · Princeton · Notre Dame · Chicago · UCLA (NEW) + the
  6 flagship seeds (100% in-sample).
- **EXACT-DUPLICATE class CLEARED fleet-wide:** 0 `(program_name, degree_type)` repeats (raw + normalized) on all
  40 catalogs (run-82 #3, 43 rows / 22 catalogs, fully resolved by the enrichment rebuilds).
- **Name-realness CLEAN fleet-wide:** ZERO CIP-rollup TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" /
  ", General/Other" on ALL 40 catalogs (the 3 "{Region} Area Studies" hits are real named degrees).
- **Tuition-VALUE-copy-down CLEAN:** no NEW grad==undergrad copy-down beyond BU's VERIFIED flat full-time
  $69,870 grad rate (prof tier distinct).
- **Heuristic over-counts to IGNORE (not defects):** the 3 benign `frame_abs150=1` singletons (Yale, Northwestern,
  Chicago); MIT's real "Master in City Planning"; real multi-clause / dual-degree MAJOR names ("Materials Science
  and Engineering", "MD/PhD", "JD/MBA") — real, NOT CIP rollups.
