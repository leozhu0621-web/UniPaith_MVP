# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / wrong-program content shipped live,
**OR the backend deploy pipeline itself blocked** so no repair can land) · **high** (residual
fabricated NAMES on an otherwise-rich catalog, exact-duplicate REAL rows shipped fleet-wide,
OR a matcher-core field STARVED — a whole master's / professional tier null, a catalog-wide
0% `tuition` or `cip_code`, or a correct repair stranded un-deployed in an unmerged PR) ·
**medium** (institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog (7,291 programs across 40 catalogs), plus per-`degree_type` tuition COVERAGE,
a **per-program `cip_code` coverage probe** (sampled program details on `GET /programs/{id}` — `cip_code`
is now serialized), an exact-duplicate `(program_name, degree_type)` scan per catalog, a name-realness scan
(federal CIP rollup TITLE match + the "…and Related Sciences/Services" / ", General/Other" / `(CIP NN.NN)`
suffix tells), a sampled `external_reviews` coverage probe, and a campus-photo + posts-feed fetch on every
institution (all 300) / mature catalog. Gold MIT (n=65) is the description 0-control — but NOT a tuition or
`cip_code` control (it ships null cert/PhD tiers, grad rows at its own undergrad sticker, AND null `cip_code`).
The repo's alembic head set, the open-PR list, and each module's `cip_code` / `content_sources` /
`backfill_program_preferences` calls were read direct (`git` / MCP).

_Last graded: 2026-06-25 (grader **run 82**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — a `cip_code` COVERAGE gate (matcher-core column,
now serialized & measurable; the live analog of the tuition-coverage rule). **🟢 CLEARED since run 81:** the
run-81 worst tier — UW-Madison + U-Chicago "Area Studies" CIP-rollup NAMES (#1129/#1131/#1127) — the
name-realness scan now returns **ZERO** fleet-wide (no "Area Studies", no `(CIP NN.NN)`, no "…and Related
Sciences/Services", no ", General/Other" on any of the 40 catalogs). Structure / descriptions / tuition-VALUE
are gold-clean fleet-wide (`machine_artifacts` / `template_slot_artifacts` / `scrape_debris` = 0 everywhere).
**NEW worst tier = matcher-core `cip_code` STARVATION** — serialized now, populated on only 4 of 34 mature
catalogs, null on 30 incl. gold MIT + the fresh Brown/Vanderbilt (entry #1) — then the master's-tier tuition
residual (NYU fix STRANDED in open PR #1139) (entry #2), then the fleet-wide exact-duplicate-row class (43 rows
/ 22 catalogs, entry #3). See CHANGELOG run 82._

## Fleet at a glance (run 82, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (7,291 total); 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo** — unchanged from run 81). Seeding is **external**;
  the routine ENRICHES + REPAIRS only.
- **🟢 DEPLOY PIPELINE HEALTHY:** `origin/main` is a SINGLE alembic head (`uclamastertuition1`, confirmed by
  direct AST parse of all 557 migrations — the 5 other branch tips are already unified by merge migrations
  `p3q5r7s9t1u3` / `s3132merge1b2c` / `deepintelmerge1`). Deploy Backend's `alembic upgrade head` is unblocked.
- **🔴 matcher-core `cip_code` STARVATION (NEW worst tier — serialized now, null on 30 of 34 mature catalogs):**
  `cip_code` (the CIP join key to `ref_majors` + the field-66 vocabulary — the matcher's interest/field signal)
  is now serialized on `GET /programs/{id}` and populated **100% in-sample on exactly 4 catalogs (Caltech,
  Princeton, Notre Dame, Chicago)** while the other **30 ship it NULL fleet-wide** — including gold MIT and the
  two catalogs enriched to "gold" last cycle (Brown, Vanderbilt). The repo confirms only **4 of 36 profile
  modules assign `p.cip_code`** (`= spec.get("cip")`), the rest skip the line — yet every module ALREADY holds
  the IPEDS CIP per row (it gates catalog breadth). So this is a one-assignment, no-research fill, highest
  matcher leverage in the fleet. Entry #1. NEW rule this run (cip_code coverage gate). Durable enforcement is
  FLAG #3 (a coverage metric in the profile test).
- **🟡 master's / professional-tier tuition residual (matcher grad-budget signal) — NYU fix STRANDED in open
  PR #1139:** structurally-clean catalogs whose bachelor's tier is 100% but whose MASTER'S (and some
  PROFESSIONAL) tier ships a material null fraction. Worst: **UCLA master's 98/146 (48 null, 67%)** · **NYU
  master's 194/232 (38 null)** — NYU's fix is the OPEN UNMERGED PR **#1139** (school-billed Stern/Wagner/Silver
  rates), so the live gap persists only because that repair has not merged. Smaller: USC 249/261 (12) ·
  UW-Seattle 138/152 (14) + prof 6/7 · UT-Austin 114/128 (14) + prof 2/5 · Vanderbilt 15/24 (9, FRESH) + prof
  4/6 · Yale 30/38 (8) · BU 162/169 (7) + prof 20/25 · UCSD 54/61 (7) · Penn 55/62 (7) · Cornell 79/85 (6) +
  prof 4/5 · Harvard 85/90 (5) · Brown 1/5 (4, FRESH) · Berkeley 72/75 (3). These publish a per-program /
  per-credit rate, rarely funded → stamp the published rate. Entry #2.
- **🔴 Exact-duplicate REAL program rows shipped fleet-wide (43 rows / 22 catalogs — dominant by VOLUME, the
  student-visible defect):** the build dedups on `slug`, so a hand-curated `PROGRAMS` row and an IPEDS/CIP-derived
  row that render the IDENTICAL `(program_name, degree_type)` both ship — the same real degree TWICE (identical
  name + degree + department + description). Worst-first: JHU (5) · UCSD (4) · BU (3) · NYU (3) · UIUC (3) ·
  Emory (3) · Purdue (3) · Yale (2) · UW-Seattle (2) · Columbia (2) · Michigan (2) · then 1 each on Northwestern ·
  Berkeley · UT-Austin · Notre Dame · USC · **Vanderbilt** (NEW — fresh enrichment re-introduced a dup) ·
  Princeton · UW-Madison · UF · Penn · Georgia Tech. Real content → DEDUPE (drop the redundant row), never rename.
  Entry #3 (the `verbatim_shared` / `frame_abs150` metric hits on these 22 catalogs are ARTIFACTS of the
  duplicate pair — they clean to 0 once the dup is dropped; MIT's `name_prefixed=1` and Chicago's lone
  `frame_abs150=1` are the only non-dup heuristic hits, both benign). Rule exists (miss #2 dedup-on-rendered-name,
  run 80) → COMPLIANCE GAP; durable enforcement is FLAG #1 (code).
- **🟢 STRUCTURE + DESCRIPTIONS + NAMES + TUITION-VALUE clean fleet-wide (verified LIVE):** every mature catalog
  scores 0 on `machine_artifacts` / `template_slot_artifacts` / `scrape_debris`; the name-realness scan returns
  ZERO (no CIP-rollup TITLE, no `(CIP NN.NN)`, no "…and Related Sciences/Services", no ", General/Other", no
  "Area Studies"); 0 possessive-form "Bachelor's in {field}" rows; no NEW tuition copy-down (BU's flat-full-time
  $69,870 grad rate is the verified exception, prof tier distinct).
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority, calibrate — do NOT pressure fabrication):**
  sampled ~5 program details/catalog — most catalogs return ≤2/5 with `external_reviews`, and 0/5 on Brown,
  Dartmouth, Duke, Emory, Georgia Tech, JHU, NYU, Stanford, UT-Austin, UCLA, UF, Michigan, Notre Dame, USC.
  BUT gold MIT itself is 2/5 (reviews are coverage-gated — many programs honestly have no third-party coverage),
  so this is a depth-pass priority on catalogs whose STRUCTURE is already clean (it is, fleet-wide), NOT a
  fabrication mandate. Entry #4. (Sample is small; treat as a signal to run the reviews depth pass where
  coverage exists, omit-with-reason where it does not — miss #8 + STRUCTURE-BEFORE-DEPTH order.)
- **🟢 NOT a defect — Brown / Vanderbilt / Chicago feeds are HEALTHY:** run 81 read Brown/Vanderbilt as
  dead-feed (ingest-timing); this run Brown reads **650 posts**, and Vanderbilt + Chicago return payloads so
  LARGE the fetch truncates (multi-MB) — i.e. healthy, not dead. The ONLY live dead feeds are the 6 five-program
  flagship seeds (entry #5).
- **🟡 PhD-tier + certificate-tier tuition null is LARGELY LEGITIMATE (funded research doctorates / per-credit
  certificates → omit-with-reason) — do NOT pressure fabrication:** NYU phd 0/96, UCLA 0/82, UIUC 0/90, BU 0/79,
  Yale 0/66, Berkeley 0/63, Columbia 0/44, GT 0/39, Rice 0/29, Northwestern 0/24, Harvard 0/23; certificate
  0/N on Harvard/Stanford/BU/Penn/Yale/MIT. Peers prove SOME publish a flat doctoral/cert rate (UW-Seattle/
  UT-Austin/USC/Cornell phd 100%), so a tier null beside a peer that fills it is a VERIFY trigger — but treat
  PhD/cert nulls as notes, NOT a repair priority, and never the undergrad sticker copied down.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The catalog build dedups on `slug`, not on the rendered `(program_name, degree_type)`, and the per-module
   self-check (`_catalog_errors`) never asserts name uniqueness — so a curated row + an IPEDS-derived row that
   render the same name+degree ship as an exact duplicate, invisible to CI.** Confirmed FLEET-WIDE again this
   run (43 rows / 22 catalogs, incl. a NEW one on fresh Vanderbilt) — it has not converged under the miss-#2
   RULE alone, which is evidence a GATE, not another rule, is the lever. Durable fix: dedup the build UNION on
   `(program_name, degree_type)` (keep the richer row), and promote a `(program_name, degree_type)`-uniqueness
   assertion into `test_anti_stub_gate.py` over the MERGED catalog. **App/test code — highest-leverage code fix.**
2. **The enforced anti-stub gate is DESCRIPTION-only and never scans NAMES.** Names are clean fleet-wide THIS
   run, but the gate gap remains: a future verbatim CIP-ROLLUP name would ship undetected. Durable fix = a
   name-realness metric (FAIL any `program_name`/`department` equal to a federal CIP rollup TITLE or carrying
   the "…and Related Sciences/Services" suffix / `(CIP NN.NN)` code), parametrized over `CERTIFIED_CLEAN`, with
   the verified-real-major carve-out. App/test code. (carried.)
3. **`cip_code` is now serialized on `GET /programs/{id}` (RESOLVES run 81's "unserialized" flag) but populated
   on only 4 of 36 modules — there is NO enforced coverage gate.** Durable fix = a `cip_code` coverage metric in
   the profile test (assert ~100% per `CERTIFIED_CLEAN` catalog, omit-with-reason recorded for the rare
   uncodeable program). The enricher fix is a rulebook rule THIS run (one assignment per module); the gate makes
   it durable. App/test code.
4. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric.** Durable fix =
   a `tuition_value_artifacts` metric + per-tier coverage in the profile test, keying the copy-down FAIL on a
   professional row at the flat undergrad sticker ONLY when that professional SCHOOL publishes a distinct higher
   rate (must NOT fail `grad==undergrad` unconditionally — it false-flags BU's verified flat full-time rate).
   App/test code. (carried.)
5. **Stranded enricher PRs (open, unmerged = failed enricher runs):** **#1139** (NYU master's/professional
   tuition — the live NYU gap fix, READY) is the actionable one; older #1081 (Purdue), #1064 (Rice), #769 (UCLA
   de-fab), #515/#503 (Harvard reviews) appear superseded by later merged repairs. Landing #1139 clears the NYU
   half of entry #2.

---

# HIGH — matcher-core `cip_code` STARVATION (new measurable dimension) — clear FIRST

## 1. The 30 catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 · 2026-06-25
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the
field-66 vocabulary (the interest/field signal alongside the `description_text` embedding). It is now serialized
on `GET /programs/{id}` and populated 100% in-sample on **4 catalogs (Caltech · Princeton · Notre Dame ·
Chicago)** but **NULL on the other 30 mature catalogs** — every one of MIT · Brown · Vanderbilt · Harvard · Yale ·
Columbia · Cornell · Penn · Princeton… (full list = all 34 mature catalogs minus the 4 fillers), so the matcher
scores those ~6,000+ programs field-blind on the CIP key. The repo confirms only 4 of 36 profile modules assign
`p.cip_code` — the rest skip the line, yet every module already holds the IPEDS CIP per row (it gates breadth).
**Fix (one fleet sweep, or per catalog):** in each catalog's build, stamp `p.cip_code = spec.get("cip")` (the
IPEDS CIP already used for the breadth cross-check), exactly as the 4 fillers do — never a guess, omit-with-reason
only for a genuinely uncodeable interdisciplinary program. Re-measure LIVE per catalog to ~100%. (One assignment
per module, no new research — highest matcher leverage in the fleet.)

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 2. UCLA · NYU (#1139 stranded) + residuals — partial master's/professional tuition null — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S (and some
PROFESSIONAL) tier ships a material null fraction (the matcher scores those graduate programs' budget-fit BLIND).
Worst-first (live run 82):
- **UCLA** — master's **98/146 (48 null, 67%)** (largest residual; `uclamastertuition1` is the alembic head but
  live coverage is unchanged from run 81 — verify whether #1133 actually filled these or only dropped the
  fabricated MSM, then fill the residual master's tier).
- **NYU** — master's **194/232 (38 null)** + prof 3/6 — **FIX is the OPEN UNMERGED PR #1139** (Stern/Wagner/
  Silver/Meyers school-billed rates → 225/232). Land #1139 to clear.
- **USC** master's 249/261 (12) · **UW-Seattle** 138/152 (14) + prof 6/7 · **UT-Austin** 114/128 (14) + prof 2/5 ·
  **Vanderbilt** 15/24 (9, FRESH) + prof 4/6 · **Yale** 30/38 (8) + cert 0/3 · **BU** 162/169 (7) + prof 20/25 ·
  **UCSD** 54/61 (7) · **Penn** 55/62 (7) + cert 0/15 · **Cornell** 79/85 (6) + prof 4/5 · **Harvard** 85/90 (5) ·
  **Brown** 1/5 (4, FRESH) · **Berkeley** 72/75 (3) · Notre Dame 23/24 (1) · Michigan 96/97 (1).
**Fix (per university, one PR — or land #1139 for NYU):** group coverage by `degree_type`; stamp the published
per-program / per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded).
For a PhD or per-credit certificate, record `tuition` in `_standard.omitted` with a reason — never a silent
blanket null, and never the undergrad sticker copied onto a professional school that bills its own higher rate
(BU's flat-rate Law is the verified exception). **PhD / certificate nulls EXCLUDED (largely funded / per-credit →
legitimate omit-with-reason).** Re-measure LIVE per tier.

---

# HIGH — fleet-wide exact-duplicate REAL program rows (data-integrity / matcher double-weight)

## 3. The exact-duplicate-row catalogs — 43 rows on 22 catalogs from slug-vs-render dedup — severity: high — first seen run 80 · 2026-06-25
The build dedups on `slug`, so a hand-curated `PROGRAMS` row and an IPEDS/CIP-derived row that render the SAME
`(program_name, degree_type)` both ship — the same real degree TWICE (identical name + degree + department +
description). 22 mature catalogs, 43 extra rows (worst-first):
- **JHU (5):** BA German · BS Biochemistry · BS Neuroscience · MS Chemical Engineering · MS Finance.
- **UCSD (4):** BA Philosophy · BA Urban Studies · BS Psychology · MS Bioinformatics.
- **BU (3):** PhD Electrical Engineering · MA Statistics · MS Bioinformatics. **NYU (3):** BA German · BA Humanities · MS Chemical Engineering.
- **UIUC (3):** BA Sociology · BS Psychology · PhD Architecture. **Emory (3):** BA Sociology · BS Computer Science · BS Psychology.
- **Purdue (3):** BA German · BA Philosophy · BS Computer Science. **Yale (2):** BA Sociology · BS Neuroscience.
- **UW-Seattle (2):** BS Environmental Studies · PhD Mathematics. **Columbia (2):** BS Computer Science · MS Chemical Engineering.
- **Michigan (2):** BA Sociology · PhD Music Education.
- **1 each:** Northwestern (BA Cognitive Science) · Berkeley (MA Geography & Cartography) · UT-Austin (MS Finance) ·
  Notre Dame (BS Electrical Engineering) · USC (BA Sociology) · **Vanderbilt** (PhD Mathematics — NEW, fresh
  enrichment) · Princeton (BS Computer Science) · UW-Madison (BA Philosophy) · UF (BA German) · Penn (BA Public
  Policy Analysis) · Georgia Tech (MS Bioinformatics).
**Fix (per catalog, one PR each — or a single fleet sweep):** dedup the build UNION on `(program_name,
degree_type)` (keep the richer row, drop the redundant render); re-scan the MERGED live catalog and get ZERO
`(program_name, degree_type)` appearing >1×. Real content — DEDUPE, never rename. (See FLAG #1 — durable fix is a
build-union dedup + a name-uniqueness gate; the miss-#2 RULE already exists, so this is a COMPLIANCE GAP, not a
missing rule. The fresh-Vanderbilt dup proves new builds still re-introduce it → the code gate is the lever.)

---

# MEDIUM — reviews depth-pass · flagship seeds · institution-level seeds (seeding is external)

## 4. `external_reviews` depth pass on the (now structurally-clean) mature catalogs — severity: medium — first seen run 65 · 2026-06-19
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order now unblocks the reviews depth pass.
Sampled ~5 details/catalog: 0/5 with `external_reviews` on Brown · Dartmouth · Duke · Emory · Georgia Tech · JHU ·
NYU · Stanford · UT-Austin · UCLA · UF · Michigan · Notre Dame · USC; ≤2/5 on the rest (gold MIT itself 2/5).
**Calibrate — reviews are coverage-gated; do NOT fabricate.** **Enrich:** on a structurally-clean catalog, run
the reviews depth pass over programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports /
program outcomes reports) — program-specific summary + themes (incl. cautions) + resolvable sources, no CIP-rollup
strings, no synthesized-from-metadata reviews (miss #8) — and record `external_reviews` in `_standard.omitted`
with a reason where a program genuinely has no coverage.

## 5. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Washington U-St Louis** each ship 5 flagship rows
with **null department**, **0% tuition**, **`cip_code` null**, bare abbreviation names (BA/BS/PhD/MBA), and a
**DEAD FEED** (posts=0 — the only live dead feeds in the fleet). (Brown + Vanderbilt were CLEARED prior cycles.)
UC-Davis · UNC · WashU carry only **3 campus photos** (below the ≥4 gold gate). **Enrich (per university, one
PR):** a full real-named catalog + per-credential researched descriptions + real departments + published tuition
(per credential level) + `cip_code` per row + a working feed + a ≥4-photo verified gallery, then deepen.

## 6. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first): Air Force Institute of
Technology · Arizona State (Campus Immersion) · Arizona State (Digital Immersion) · Azusa Pacific · Colorado
State-Fort Collins · James Madison · Keiser-Ft Lauderdale · Loyola Marymount · Loyola-Chicago · Miami U-Oxford ·
Michigan Tech · Montclair State · Northcentral · Oakland · Oregon State · SUNY-ESF · Sacred Heart · Stephen F
Austin State · Texas A&M-Commerce · Texas A&M-Corpus Christi · Thomas Jefferson · Universidad Ana G.
Mendez-Gurabo · U Alabama-Birmingham · U Dayton · U Houston · U Kentucky · U Louisville · UMBC · U Missouri-St
Louis · U Nebraska-Lincoln · U Oklahoma-Norman · U Utah · Virginia Commonwealth — **plus 53 more at 1–3 photos**
(incl. NC State 2, Pitt 2, Fordham 2, Florida State 3, Temple 3, Texas A&M-College Station 3). **Enrich (per
university, one PR):** a full real-named catalog + per-credential field-specific descriptions + real departments +
published tuition + `cip_code` · a working feed · a ≥4-photo verified gallery · reviews on coverable programs ·
`_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions + names + tuition-value; no name/structure action) — verified LIVE run 82
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric; real "Science, Technology, and
  Society" major; `name_prefixed=1` is the benign real "Master in City Planning"; cert/PhD tiers null + grad rows
  at its own undergrad sticker — MIT is NOT a tuition reference; AND `cip_code` null — MIT is NOT a `cip_code`
  reference, the 4 fillers are).
- **`cip_code`-COMPLETE (the model for entry #1):** Caltech · Princeton · Notre Dame · Chicago (100% in-sample).
- **Name-realness CLEAN fleet-wide:** ZERO CIP-rollup TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" /
  ", General/Other" / "Area Studies" on ALL 40 catalogs (UW-Madison + Chicago "Area Studies" CLEARED by
  #1129/#1131/#1127 this cycle).
- **Tuition-COMPLETE / near (every published tier filled; PhD/cert omit-with-reason where funded/per-credit):**
  Princeton · JHU (cert 84/84) · UW-Madison (cert 128/128) · USC (phd 87/87) · UW-Seattle (phd 90/90) · UF (cert
  93/93) · UT-Austin (phd 86/86) · Cornell (phd 70/70) · Berkeley (prof 20/20) · Rice (prof 38/38) · Purdue ·
  Dartmouth · Emory · Chicago · Duke.
- **Heuristic over-counts to IGNORE (not defects):** MIT's `name_prefixed=1`; Chicago's lone `frame_abs150=1`;
  the `verbatim_shared` / `frame_abs150` hits on the 22 duplicate-row catalogs (artifacts of the duplicate pair,
  entry #3); BU's verified flat full-time $69,870 grad rate EQUAL to undergrad; real multi-clause / dual-degree /
  slash MAJOR names ("Materials Science and Engineering", "Electrical and Computer Engineering", "MD/PhD",
  "JD/MBA") — real, NOT CIP rollups.
