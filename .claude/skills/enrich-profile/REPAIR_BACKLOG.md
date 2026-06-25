# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / scraped-debris /
near-duplicate / machine-broken template-slot grammar / wrong-program content shipped live,
**OR the backend deploy pipeline itself blocked** so no repair can land) · **high** (residual
fabricated NAMES on an otherwise-rich catalog, exact-duplicate REAL rows shipped fleet-wide,
OR a matcher-core field STARVED — a whole master's / professional tier null, a catalog-wide
0%, or a correct repair stranded un-deployed in an unmerged PR) · **medium** (institution-level
seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured this run with
`profile_standard/anti_stub.py` (the enforced CI gate's own functions): `analyze`,
`template_slot_artifacts`, `scrape_debris`, `machine_artifacts`, and
`frame_stripped_shared_body(..., abs_chars=150)` over the fully-paginated `/programs` list of every
program-bearing catalog (7,141 programs across 40 catalogs), plus per-`degree_type` tuition COVERAGE,
a campus-photo proxy (`image_url`) on all 300 institutions, an exact-duplicate `(program_name,
degree_type)` scan per catalog, and a name-realness scan (federal CIP rollup TITLE match + the
"…and Related Sciences/Services" / ", General/Other" / `(CIP NN.NN)` suffix tells). Gold MIT (n=65) is
the description 0-control — but NOT a tuition control (it ships null cert/PhD tiers + grad rows at its
own undergrad sticker). The repo's alembic head set + the open-PR list were read direct (`git` / MCP).

_Last graded: 2026-06-25 (grader **run 80**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — promoted the slug-vs-rendered-name dedup
gap into miss #2's ENFORCED list (the terse step-3 "dedupe by real name, not just slug" had no teeth and
the live fleet ships 30 exact-duplicate rows across 15 catalogs because the build dedups on SLUG while a
curated row and an IPEDS-derived row render the IDENTICAL name+degree). **🟢 CLEARED since run 79:** the
CRITICAL run-79 entry #1 (DUAL ALEMBIC HEAD blocking ALL backend deploys) — `origin/main` is now a SINGLE
head (`gatechproftuition1`); merges #1098 + #1106 collapsed the dual head and the stranded-PR wave landed
(Penn/Cornell/Harvard CIP names #1104/#1102/#1096; tuition repairs for Columbia/Rice/Chicago/Emory/
Dartmouth/Berkeley/Duke/UCLA/GT/Yale/Northwestern/Notre Dame). **NEW worst tier = the federal-CIP-rollup
"Area Studies" NAME class** (fabrication) still live on Berkeley/UW-Madison/Chicago (8 rows, entry #1),
then the fleet-wide exact-duplicate-row class (entry #2), then the residual master's-tier tuition
starvation now concentrated on UCLA + NYU (entry #3), then the seeds. See CHANGELOG run 80._

## Fleet at a glance (run 80, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo** — unchanged from run 79). Seeding is **external**;
  the routine ENRICHES + REPAIRS only.
- **🟢 DEPLOY PIPELINE HEALTHY (run-79 CRITICAL block CLEARED):** `origin/main` is a SINGLE alembic head
  (`gatechproftuition1`, confirmed direct from the migration graph — 548 revisions, 1 head). The run-79
  dual head (`penntuition1` + `gatechgradtuition1`) was unified by merges #1098 / #1106, Deploy Backend's
  `alembic upgrade head` is unblocked, and the whole stranded-PR wave from run 79 landed and deployed
  (CIP-name + tuition repairs all LIVE). The §8-step-5 auto-merge dual-head race is DORMANT again.
- **🔴 Federal-CIP-ROLLUP "Area Studies" NAME class still live (fabrication, 8 rows, NEW worst tier):**
  **"Area Studies"** is a federal CIP series TITLE (CIP 05.01), not a conferred degree — no institution
  awards a degree literally named "Area Studies" (the real degree is a specific area program: East Asian
  Studies, Latin American Studies, …). It ships verbatim as `program_name` across credential levels on
  **UC-Berkeley** (BA + MA + PhD "Area Studies", dept "Global Studies Program"), **UW-Madison** (BA +
  Graduate Certificate + MS "Area Studies", dept "International Studies"), and **University of Chicago**
  (BA + MA "Area Studies", dept literally "Area Studies" too — rollup echoed into department). This is the
  exact miss-#2 class the Cornell/Penn/Harvard repairs cleared, left un-cleared on these three (miss #2
  names "Area Studies" explicitly — a whole-class compliance gap). Entry #1.
- **🔴 Exact-duplicate REAL program rows shipped fleet-wide (30 rows / 15 catalogs, NEW class):** the
  catalog build dedups on `slug`, so a hand-curated `PROGRAMS` row and an IPEDS/CIP-derived row that
  render the IDENTICAL `(program_name, degree_type)` (often identical department + description too) both
  ship — the same real degree TWICE. Confirmed exact on 15 of the ~32 mature catalogs: USC · NYU (×2) ·
  Yale · UIUC (×4) · Notre Dame (×2) · UW-Seattle (×4) · Columbia (×2) · Northwestern · Emory · Michigan
  (×2) · JHU (×4) · Purdue (×2) · UF (×2) · Georgia Tech · Duke. Recurring fields are the cross-listed /
  interdisciplinary ones a curated row and an IPEDS row both name — Computer Engineering, Political
  Science, Nursing, Mechanical Engineering, Psychology. Real content, so the fix is DEDUPE (drop the
  redundant row), not rename. Doubles the program for the student and double-weights it for the matcher;
  invisible to the slug-dedup and to the per-module self-check. Entry #2 (the `verbatim_shared` /
  `shared_leading_body` / `frame_abs150` counts on these catalogs are ARTIFACTS of the duplicate pair —
  they clean to 0 once the dup is dropped). The miss-#2 tightening this run gives the rule teeth.
- **🟢 STRUCTURE + DESCRIPTIONS otherwise clean fleet-wide (verified LIVE):** every mature catalog scores
  0 on `template_slot_artifacts` / `scrape_debris` / `machine_artifacts`; no bare-abbreviation /
  "Programs"-dept / null-dept rows on any mature catalog (only the 8 five-program flagship seeds have null
  dept). The only `verbatim_shared` / `frame_abs150` hits are the duplicate-row artifacts above + MIT's
  known benign `name_prefixed=1` ("Master in City Planning").
- **🔴 master's-tier tuition starvation now concentrated on UCLA + NYU (matcher-blind on grad budget):**
  **UCLA** master's **97/145 (48 null)** and **NYU** master's **195/233 (38 null)** are the two large
  residual gaps after the run-79→80 repair wave cleared Columbia/Rice/Chicago/Emory/Dartmouth/Berkeley/
  Duke/GT/Northwestern/Notre Dame/Yale master's tiers. Smaller residuals: Yale master's 30/38 (8) + cert
  0/3 · UCSD master's 53/60 (7) · Penn master's 56/63 (7) · Notre Dame master's 23/24 (1) · plus scattered
  professional-tier nulls (NYU prof 3/6, Stanford prof 0/2, UT-Austin prof 2/5, Cornell prof 4/5, Columbia
  prof 5/8). Entry #3.
- **🟡 PhD-tier + certificate-tier null is LARGELY LEGITIMATE (funded research doctorates / per-credit
  certificates → omit-with-reason) — do NOT pressure fabrication:** NYU phd 0/97, UIUC 0/91, BU 0/78,
  UCLA 0/82, Michigan 1/148, Penn 0/46, Yale 0/65, Berkeley 0/64; certificate 0/N on Harvard/Stanford/BU/
  Penn/Yale/CMU/MIT. Peers prove SOME publish a flat doctoral/cert rate (UW-Seattle phd 87/87, UT-Austin
  86/86, USC 88/88, Cornell 70/70; UW-Madison cert 128/128, UF cert 93/93, JHU cert 85/85), so a tier null
  beside a peer that fills it is a VERIFY trigger, not proof — but treat PhD/cert nulls as notes, NOT a
  repair priority, and never the undergrad sticker copied down.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The catalog build dedups on `slug`, not on the rendered `(program_name, degree_type)`, and the
   per-module self-check (`_catalog_errors`) never asserts name uniqueness — so a curated row + an
   IPEDS-derived row that render the same name+degree ship as an exact duplicate, invisible to CI.** The
   enforced anti-stub gate's `analyze().verbatim_shared` already detects the identical-description symptom
   but is module-scoped (runs over a module's own `PROGRAMS` list at certification, not over the MERGED
   live catalog), so a duplicate introduced by a SEPARATE migration evades it. Durable fix: dedup the build
   UNION on `(program_name, degree_type)` (drop the redundant render, keep the richer row), and promote a
   `(program_name, degree_type)`-uniqueness assertion into `test_anti_stub_gate.py` over the merged catalog.
   App/test code.
2. **The enforced anti-stub gate is DESCRIPTION-only and never scans NAMES, so verbatim CIP-ROLLUP program
   names ("Area Studies") ship live undetected** (`anti_stub.py` + `test_anti_stub_gate.py`): the gate
   scores 0 on Berkeley/UW-Madison/Chicago while 8 federal-CIP-title rows ship. Durable fix = a
   name-realness metric: FAIL any `program_name` / `department` field equal to a federal CIP rollup TITLE
   (the IPEDS code→title table) OR carrying the "…and Related Sciences/Services" suffix / a literal
   `(CIP NN.NN)` code, parametrized over `CERTIFIED_CLEAN`, with the verified-real-major carve-out
   (carried from run 79 — still unaddressed). App/test code.
3. **`cip_code` is serialized as a KEY on `/programs/{id}` but its VALUE is `None` on EVERY program incl.
   gold MIT (re-confirmed run 80)**, so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE. The in-repo IPEDS catalogs carry a `cip` per row (e.g. jhu_profile.py rows have `"cip"`) —
   expose it on the API or audit via DB/git. (`tuition` IS serialized with real values — the tuition gaps
   are a real DATA gap.) (carried from run 79 — still unaddressed.)
4. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric.** Both are
   invisible to CI. Durable fix = a `tuition_value_artifacts` metric + per-tier coverage in the profile
   test — keying the copy-down FAIL on a professional row at the flat undergrad sticker ONLY when that
   professional SCHOOL publishes a distinct higher rate (must NOT fail `grad==undergrad` unconditionally —
   it false-flags BU's verified flat full-time rate incl. the Law JD). App/test code. (carried from run 79.)

---

# HIGH — federal-CIP-ROLLUP "Area Studies" NAME residual (fabrication axis) — clear FIRST

## 1. UC-Berkeley · UW-Madison · U-Chicago — "Area Studies" CIP-rollup NAMES live — severity: high — first seen run 80 · 2026-06-25
Three catalogs ship the federal CIP series TITLE **"Area Studies"** (CIP 05.01) verbatim as a degree name
across credential levels — a degree no institution confers under that literal name (the real degree is a
specific area program). Per-credential rows:
- **UC-Berkeley (3):** BA + MA + PhD "Area Studies" (dept "Global Studies Program").
- **UW-Madison (3):** BA + Graduate Certificate + MS "Area Studies" (dept "International Studies").
- **U-Chicago (2):** BA + MA "Area Studies" (dept literally "Area Studies" — rollup echoed into department).
**Fix (per university, one PR each):** resolve each "Area Studies" row to the institution's REAL published
area-studies degree(s) + owning department (e.g. the named area programs the school actually awards), or
drop the federal aggregation bucket if no single named degree exists; fix the Chicago `department` echo.
THEN re-scan the WHOLE catalog with the miss-#2 tells (federal CIP rollup TITLE match + "…and Related
Sciences/Services" / ", General/Other" / `(CIP NN.NN)`) and get ZERO. Do NOT mangle verified real
multi-clause majors (carve-out). Re-measure LIVE.

---

# HIGH — fleet-wide exact-duplicate REAL program rows (data-integrity / matcher double-weight)

## 2. The exact-duplicate-row catalogs — 30 rows on 15 catalogs from slug-vs-render dedup — severity: high — first seen run 80 · 2026-06-25
The build dedups on `slug`, so a hand-curated `PROGRAMS` row and an IPEDS/CIP-derived row that render the
SAME `(program_name, degree_type)` both ship — the same real degree TWICE (identical name + degree +
department + description). 15 mature catalogs, 30 extra rows (worst-first by dup count):
- **UW-Seattle (4):** MS Geography · MS Industrial Engineering · MS Linguistics · MS Nursing.
- **JHU (4):** BS Computer Engineering · Graduate Certificate Physics · MS Industrial Engineering · MS Mechanical Engineering.
- **UIUC (4):** BA Global Studies · BA Political Science · PhD Sociology · MS Mechanical Engineering.
- **NYU (2):** PhD German · MA Psychology. **Columbia (2):** BS Computer Engineering · JSD (Doctor of the Science of Law).
- **Notre Dame (2):** BA Arabic · BS Computer Engineering. **Michigan (2):** BA Political Science · MS Nursing.
- **Purdue (2):** BA Political Science · MS Economics. **UF (2):** BA Political Science · MS Nursing.
- **Duke (1):** DNP. **USC (1):** PhD Classics. **Yale (1):** BA Political Science. **Northwestern (1):** PhD Psychology.
- **Emory (1):** BS Psychology. **Georgia Tech (1):** BS Computer Engineering.
**Fix (per catalog, one PR each — or a single fleet sweep):** dedup the build UNION on `(program_name,
degree_type)` (keep the richer row, drop the redundant render); re-scan the MERGED live catalog for any
`(program_name, degree_type)` appearing >1× and get ZERO. Real content — DEDUPE, never rename. The
`shared_leading_body` / `frame_abs150` counts on these catalogs are artifacts of the duplicate pair and
clear with it. (See FLAG #1 — the durable fix is a build-union dedup + a name-uniqueness gate.)

---

# HIGH — master's-tier tuition starvation (matcher-blind on grad budget)

## 3. UCLA · NYU (+ small residuals) — master's-tier tuition null behind a 100% bachelor's tier — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S tier ships
mostly null (matcher scores graduate budget-fit BLIND). These publish a per-program / per-credit rate and
are rarely funded → unambiguous starvation. **PhD / certificate nulls EXCLUDED (largely funded / per-credit
→ legitimate omit-with-reason; do not pressure fabrication).** Worst-first (live run 80):
- **UCLA** — master's **97/145 (48 null)** (ba 139/139, prof 4/4). The largest residual master's gap.
- **NYU** — master's **195/233 (38 null)** + prof 3/6 (ba 167/167).
- **Yale** — master's 30/38 (8 null) + cert 0/3 (ba 81/81).
- **UCSD** — master's 53/60 (7 null) (ba 71/71). **Penn** — master's 56/63 (7 null) (ba 54/54).
- **Notre Dame** — master's 23/24 (1) (ba 62/62). Scattered professional nulls: Stanford prof 0/2 · UT-Austin
  prof 2/5 · Cornell prof 4/5 · Columbia prof 5/8.
**Fix (per university, one PR):** group coverage by `degree_type`; stamp the published per-program /
per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD
or per-credit certificate, record `tuition` in `_standard.omitted` with a reason — never a silent blanket
null, and never the undergrad sticker copied onto a professional school that bills its own higher rate (the
run-76 copy-down tell; BU Law, which genuinely bills the university flat rate, is the verified exception).
Re-measure LIVE per tier.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 4. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Brown · Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Vanderbilt · Washington U-St Louis** each
ship 5 flagship rows with **null department**, **0% tuition**, and a **DEAD FEED** (posts=0), with bare
abbreviation names (BA/BS/PhD). Several carry **3 campus photos** (UC-Davis, Vanderbilt — still below the
≥4 gold gate); re-measure per institution. **Enrich (per university, one PR):** a full real-named catalog +
per-credential researched descriptions + real departments + published tuition (per credential level) + a
working feed + a ≥4-photo verified gallery, then deepen toward the full real catalog.

## 5. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos** (broken
explore-card gradient header + detail hero — the acute sub-set to clear first): Air Force Institute of
Technology · Arizona State (Campus Immersion) · Arizona State (Digital Immersion) · Azusa Pacific · Colorado
State-Fort Collins · James Madison · Keiser-Ft Lauderdale · Loyola Marymount · Loyola-Chicago · Miami U-Oxford
· Michigan Tech · Montclair State · Northcentral · Oakland · Oregon State · SUNY-ESF · Sacred Heart · Stephen F
Austin State · Texas A&M-Commerce · Texas A&M-Corpus Christi · Thomas Jefferson · Universidad Ana G.
Mendez-Gurabo · U Alabama-Birmingham · U Dayton · U Houston · U Kentucky · U Louisville · UMBC · U Missouri-St
Louis · U Nebraska-Lincoln · U Oklahoma-Norman · U Utah · Virginia Commonwealth — **plus more at 1–3 photos**.
**Enrich (per university, one PR):** a full real-named catalog + per-credential field-specific descriptions +
real departments + published tuition · a working feed · a ≥4-photo verified gallery · reviews on coverable
programs · `_standard`. Pick a 0-photo seed once the HIGH tier clears.

---

# CLEAN (structure + descriptions; no name/structure action) — verified LIVE run 80
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric; real "Science, Technology, and
  Society" major; `name_prefixed=1` is the benign real "Master in City Planning"; cert/PhD tiers null + grad
  rows at its own undergrad sticker — MIT is NOT a tuition reference).
- **Tuition-COMPLETE / near (every published tier filled; PhD/cert omit-with-reason where funded/per-credit):**
  Princeton (43, 100%) · JHU (cert 85/85) · UW-Madison (cert 128/128) · USC (phd 88/88) · UW-Seattle (phd
  87/87) · UF (cert 93/93) · UT-Austin (phd 86/86) · Cornell (phd 70/70) · Berkeley (prof 20/20) · Rice
  (prof 38/38) · Purdue · Dartmouth · Emory · Chicago (but see NAME entry #1) · Columbia · Notre Dame.
- **Heuristic over-counts to IGNORE (not defects):** MIT's `name_prefixed=1`; a verified flat full-time rate
  EQUAL to undergrad on the general AND a genuinely-flat-rate professional school (BU $69,870 incl. Law JD);
  GT's real "Professional Master's in …" (PMASE); real multi-clause / dual-degree / slash MAJOR names
  ("Materials Science and Engineering", "Electrical and Computer Engineering", "Latina/Latino Studies",
  "Radio/Television/Film", "MD/PhD", "JD/MBA", "Zoology/Animal Biology") — these are real, NOT CIP rollups
  (the name tell keys on the CIP-title TABLE + the federal suffix forms, NOT on a bare slash or
  cross-institution sharing). The `verbatim_shared` / `shared_leading_body` / `frame_abs150` hits on the 15
  duplicate-row catalogs are artifacts of the duplicate pair (entry #2), NOT a separate description-stub class.
