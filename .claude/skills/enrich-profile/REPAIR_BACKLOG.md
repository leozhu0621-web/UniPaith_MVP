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
program-bearing catalog (7,294 programs across 40 catalogs), plus per-`degree_type` tuition COVERAGE,
a professional-tier copy-down scan (grad/prof == undergrad sticker), a campus-photo proxy (`image_url`)
on all 300 institutions, an exact-duplicate `(program_name, degree_type)` scan per catalog, a
name-realness scan (federal CIP rollup TITLE match + the "…and Related Sciences/Services" / ", General/
Other" / `(CIP NN.NN)` suffix tells), and a posts-feed fetch on every mature catalog. Gold MIT (n=65) is
the description 0-control — but NOT a tuition control (it ships null cert/PhD tiers + grad rows at its
own undergrad sticker). The repo's alembic head set + the open-PR list + each fresh module's
`content_sources` / `backfill_program_preferences` calls were read direct (`git` / MCP).

_Last graded: 2026-06-25 (grader **run 81**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **0 rule changes** — after a full sweep, every live defect maps
to an EXISTING rule (miss #1 / miss #2 / the tuition-coverage rules); the structure / description /
tuition-VALUE / matcher-side dimensions are gold-clean fleet-wide, so no NEW gap-class warranted a rule
(anti-churn + no-edit-without-NEW-evidence). **🟢 CLEARED since run 80:** the run-80 worst tier — UC-Berkeley
"Area Studies" CIP-rollup names (#1123, resolved to real area programs: Global Studies, Near Eastern Studies,
South & Southeast Asian Studies, Ethnic Studies …, verified LIVE) — and **two flagship seeds enriched to gold**
(Brown #1117 = 57-program catalog · Vanderbilt #1121 = 103-program catalog, both real conferred-degree names +
real departments + field-specific descriptions + tuition + 5-photo galleries, verified LIVE). **NEW worst tier =
the federal-CIP-rollup "Area Studies" NAME residual on UW-Madison + Chicago** (fabrication, 5 rows, entry #1),
then the fleet-wide exact-duplicate-row class — now 43 rows / 24 catalogs (entry #2), then the residual
master's-tier tuition gap on UCLA + NYU (entry #3), then the seeds. See CHANGELOG run 81._

## Fleet at a glance (run 81, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level stubs**
  (0 programs, dead feed, **33 with ZERO campus photo** — unchanged from run 80). Seeding is **external**;
  the routine ENRICHES + REPAIRS only.
- **🟢 DEPLOY PIPELINE HEALTHY:** `origin/main` is a SINGLE alembic head (`berkvandmerge1`, confirmed direct
  — the run-80→81 enrichment + repair wave all landed and deployed). Deploy Backend's `alembic upgrade head`
  is unblocked. (The auto-merge dual-head race stays DORMANT — merges #1106/#1125 unified the heads.)
- **🔴 Federal-CIP-ROLLUP "Area Studies" NAME class — UC-Berkeley CLEARED, UW-Madison + Chicago STILL LIVE
  (fabrication, 5 rows, worst tier):** **"Area Studies"** is a federal CIP series TITLE (CIP 05.01), not a
  conferred degree — no institution awards a degree literally named "Area Studies" (the real degree is a
  specific area program). It ships verbatim as `program_name` across credential levels on **UW-Madison** (BA +
  Graduate Certificate + MS "Area Studies", dept "International Studies") and **University of Chicago** (BA + MA
  "Area Studies", dept literally "Area Studies" too — rollup echoed into department). This is the exact miss-#2
  class the Berkeley/Cornell/Penn/Harvard repairs cleared, left un-cleared on these two (miss #2 names "Area
  Studies" explicitly — a whole-class compliance gap). Entry #1.
- **🔴 Exact-duplicate REAL program rows shipped fleet-wide (43 rows / 24 catalogs — the dominant defect by
  VOLUME):** the catalog build dedups on `slug`, so a hand-curated `PROGRAMS` row and an IPEDS/CIP-derived row
  that render the IDENTICAL `(program_name, degree_type)` (often identical department + description too) both
  ship — the same real degree TWICE. Confirmed exact on 24 of the ~32 mature catalogs (worst-first by dup
  count): UIUC (5) · UW-Seattle (4) · Georgia Tech (3) · Purdue (3) · UW-Madison (3) · NYU (2) · UF (2) ·
  Harvard (2) · Yale (2) · Penn (2) · Columbia (2) · then 1 each on USC · BU · Michigan · UT-Austin · JHU ·
  Cornell · Stanford · Rice · UCSD · Northwestern · Chicago · Caltech · Princeton. Recurring fields are the
  cross-listed / interdisciplinary ones a curated row and an IPEDS row both name — Sociology, Philosophy,
  Neuroscience, Mathematics (PhD), Computer/Electrical Engineering, Materials Science & Engineering, Psychology
  (MS). Real content, so the fix is DEDUPE (drop the redundant row), not rename. Doubles the program for the
  student and double-weights it for the matcher; invisible to the slug-dedup and to the per-module self-check.
  Entry #2 (the `verbatim_shared` / `frame_abs150` counts on these 24 catalogs are ARTIFACTS of the duplicate
  pair — they clean to 0 once the dup is dropped). The rule already exists (miss #2 dedup-on-rendered-name,
  run 80) — this is a COMPLIANCE GAP; durable enforcement is FLAG #1 (code).
- **🟢 STRUCTURE + DESCRIPTIONS + TUITION-VALUE otherwise clean fleet-wide (verified LIVE):** every mature
  catalog scores 0 on `template_slot_artifacts` / `scrape_debris` / `machine_artifacts`; no bare-abbreviation /
  "Programs"-dept / null-dept rows on any mature catalog (only the 6 five-program flagship seeds have null
  dept); 0 possessive-form "Bachelor's in {field}" rows fleet-wide; no NEW tuition copy-down (BU's 15
  professional rows at the $69,870 flat rate are the VERIFIED flat-full-time exception — prof tier carries 3
  distinct values incl. distinct MD/DMD/SSW; NYU's single combined B.A./D.D.S. at the undergrad sticker is a
  genuine combined-degree, not a copy-down). The only `verbatim_shared` / `frame_abs150` hits are the
  duplicate-row artifacts above + MIT's known benign `name_prefixed=1` ("Master in City Planning").
- **🟡 master's-tier tuition residual concentrated on UCLA + NYU (partial, not whole-tier-null):** **UCLA**
  master's **98/146 (48 null, 67%)** and **NYU** master's **194/232 (38 null, 84%)** are the two largest residual
  master's gaps after the run-79→80 repair wave cleared the whole-tier starvation. Smaller residuals: Yale
  master's 30/38 (8 null) + cert 0/3 · UW-Seattle master's 138/152 (14) · TX-Austin master's 115/128 (13) ·
  Cornell master's 79/85 (6) · UCSD 54/61 (7) · Penn 56/63 (7). These publish a per-program / per-credit rate
  and are rarely funded → stamp the published rate. Entry #3 (lower than run 80 — no longer whole-tier
  starvation, just a partial residual).
- **🟡 PhD-tier + certificate-tier null is LARGELY LEGITIMATE (funded research doctorates / per-credit
  certificates → omit-with-reason) — do NOT pressure fabrication:** NYU phd 0/97, UIUC 0/87, BU 0/76, UCLA
  0/82, Michigan 1/148, Penn 0/47, Yale 0/66, Berkeley 0/63, Columbia 0/44, GT 0/41; certificate 0/N on
  Harvard/Stanford/BU/Penn/Yale/MIT. Peers prove SOME publish a flat doctoral/cert rate (UW-Seattle phd 90/90,
  UT-Austin 86/86, USC 87/87, Cornell 70/70; UW-Madison cert 128/128, UF cert 93/93, JHU cert 84/84), so a tier
  null beside a peer that fills it is a VERIFY trigger, not proof — but treat PhD/cert nulls as notes, NOT a
  repair priority, and never the undergrad sticker copied down.
- **🟢 NOT a defect — dead feeds on the two FRESH enrichments are ingest-TIMING, not data:** **Brown** and
  **Vanderbilt** (enriched this cycle, <1 day old) read **posts=0**, but BOTH modules DO set `content_sources`
  (real `news_rss` + `events_feed` ICS — `brown_profile.py` / `vanderbilt_profile.py`), so the daily content
  ingest simply has not run for them yet (older enrichments populated: Dartmouth 31, Notre Dame 13, Emory 1525).
  Re-check next run; if still 0 after an ingest cycle, THEN it is a miss-#1 data defect. Matcher-side
  `backfill_program_preferences` IS called in both fresh migrations (compliant).

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The catalog build dedups on `slug`, not on the rendered `(program_name, degree_type)`, and the
   per-module self-check (`_catalog_errors`) never asserts name uniqueness — so a curated row + an
   IPEDS-derived row that render the same name+degree ship as an exact duplicate, invisible to CI.** This is
   now confirmed FLEET-WIDE (43 rows / 24 of ~32 mature catalogs — essentially the default state of every
   catalog built from a curated + IPEDS union), and it has not converged under the miss-#2 re-scan RULE alone,
   which is evidence that a GATE, not another rule, is the lever. The enforced anti-stub gate's
   `analyze().verbatim_shared` already detects the identical-description symptom but is module-scoped (runs over
   a module's own `PROGRAMS` list at certification, not over the MERGED live catalog), so a duplicate from the
   build union evades it. Durable fix: dedup the build UNION on `(program_name, degree_type)` (drop the
   redundant render, keep the richer row), and promote a `(program_name, degree_type)`-uniqueness assertion into
   `test_anti_stub_gate.py` over the merged catalog. **App/test code — now the highest-leverage code fix.**
2. **The enforced anti-stub gate is DESCRIPTION-only and never scans NAMES, so verbatim CIP-ROLLUP program
   names ("Area Studies") ship live undetected** (`anti_stub.py` + `test_anti_stub_gate.py`): the gate scores 0
   on UW-Madison/Chicago while 5 federal-CIP-title rows ship. Durable fix = a name-realness metric: FAIL any
   `program_name` / `department` field equal to a federal CIP rollup TITLE (the IPEDS code→title table) OR
   carrying the "…and Related Sciences/Services" suffix / a literal `(CIP NN.NN)` code, parametrized over
   `CERTIFIED_CLEAN`, with the verified-real-major carve-out (carried from run 79 — still unaddressed). App/test code.
3. **`cip_code` is serialized as a KEY on `/programs/{id}` but its VALUE is `None` on EVERY program incl.
   gold MIT (re-confirmed run 81)**, so the matcher-side "flag empty `cip_code` via public API" channel is
   UNUSABLE. The in-repo IPEDS catalogs carry a `cip` per row — expose it on the API or audit via DB/git.
   (`tuition` IS serialized with real values — the tuition gaps are a real DATA gap.) (carried from run 80.)
4. **There is NO enforced gate on tuition VALUE or COVERAGE — `anti_stub` has no tuition metric.** Both are
   invisible to CI. Durable fix = a `tuition_value_artifacts` metric + per-tier coverage in the profile
   test — keying the copy-down FAIL on a professional row at the flat undergrad sticker ONLY when that
   professional SCHOOL publishes a distinct higher rate (must NOT fail `grad==undergrad` unconditionally —
   it false-flags BU's verified flat full-time rate incl. the Law JD). App/test code. (carried from run 80.)

---

# HIGH — federal-CIP-ROLLUP "Area Studies" NAME residual (fabrication axis) — clear FIRST

## 1. UW-Madison · U-Chicago — "Area Studies" CIP-rollup NAMES live — severity: high — first seen run 80 · 2026-06-25
Two catalogs ship the federal CIP series TITLE **"Area Studies"** (CIP 05.01) verbatim as a degree name
across credential levels — a degree no institution confers under that literal name (the real degree is a
specific area program). (UC-Berkeley, the third in this entry at run 80, was CLEARED by #1123 — verified LIVE.)
Per-credential rows still live:
- **UW-Madison (3):** BA + Graduate Certificate + MS "Area Studies" (dept "International Studies").
- **U-Chicago (2):** BA + MA "Area Studies" (dept literally "Area Studies" — rollup echoed into department).
**Fix (per university, one PR each):** resolve each "Area Studies" row to the institution's REAL published
area-studies degree(s) + owning department (the named area programs the school actually awards — e.g. East
Asian / Latin American / Middle Eastern Studies — exactly as the Berkeley repair resolved them to Global
Studies / Near Eastern Studies / South & Southeast Asian Studies), or drop the federal aggregation bucket if
no single named degree exists; fix the Chicago `department` echo. THEN re-scan the WHOLE catalog with the
miss-#2 tells (federal CIP rollup TITLE match + "…and Related Sciences/Services" / ", General/Other" /
`(CIP NN.NN)`) and get ZERO. Do NOT mangle verified real multi-clause majors (carve-out). Re-measure LIVE.

---

# HIGH — fleet-wide exact-duplicate REAL program rows (data-integrity / matcher double-weight)

## 2. The exact-duplicate-row catalogs — 43 rows on 24 catalogs from slug-vs-render dedup — severity: high — first seen run 80 · 2026-06-25
The build dedups on `slug`, so a hand-curated `PROGRAMS` row and an IPEDS/CIP-derived row that render the
SAME `(program_name, degree_type)` both ship — the same real degree TWICE (identical name + degree +
department + description). 24 mature catalogs, 43 extra rows (worst-first by dup count):
- **UIUC (5):** BA Philosophy · BS Electrical Engineering · BS Neuroscience · MS Chemical Engineering · MS Psychology.
- **UW-Seattle (4):** PhD Civil Engineering · PhD Mathematics · PhD Political Science · MS Materials Science & Engineering.
- **Georgia Tech (3):** PhD Architecture · PhD Industrial Engineering · MS Materials Science & Engineering.
- **Purdue (3):** BA Philosophy · BA Sociology · BS Biochemistry. **UW-Madison (3):** BS Psychology · PhD Veterinary Medicine · MS Bioinformatics.
- **NYU (2):** BA German · PhD Biomedical Sciences. **UF (2):** BS Computer Science · BS Teacher Education (Subject Areas).
- **Harvard (2):** PhD Biomedical Sciences · Graduate Certificate Curriculum & Instruction. **Yale (2):** BA Philosophy · BS Neuroscience.
- **Penn (2):** BA Sociology · PhD Mathematics. **Columbia (2):** BA Sociology · MS Chemical Engineering.
- **1 each:** USC (BA Biological Sciences) · BU (BS Electrical Engineering) · Michigan (MS Psychology) · UT-Austin
  (PhD Architecture) · JHU (MS Finance) · Cornell (PhD Mathematics) · Stanford (BA Sociology) · Rice (BS Neuroscience)
  · UCSD (MS Psychology) · Northwestern (BA Sociology) · Chicago (BA Philosophy) · Caltech (BS Computer Science) ·
  Princeton (BA Sociology).
**Fix (per catalog, one PR each — or a single fleet sweep):** dedup the build UNION on `(program_name,
degree_type)` (keep the richer row, drop the redundant render); re-scan the MERGED live catalog for any
`(program_name, degree_type)` appearing >1× and get ZERO. Real content — DEDUPE, never rename. The
`verbatim_shared` / `frame_abs150` counts on these catalogs are artifacts of the duplicate pair and clear
with it. (See FLAG #1 — the durable fix is a build-union dedup + a name-uniqueness gate; the miss-#2 RULE
already exists, so this is a COMPLIANCE GAP, not a missing rule.)

---

# HIGH/MEDIUM — residual master's-tier tuition gap (matcher grad-budget signal)

## 3. UCLA · NYU (+ small residuals) — partial master's-tier tuition null behind a 100% bachelor's tier — severity: high — first seen run 74 · 2026-06-21
Structurally + description clean catalogs whose bachelor's tier is 100% but whose MASTER'S tier ships a
material null fraction (the matcher scores those graduate programs' budget-fit BLIND). No longer whole-tier
starvation (the run-79→80 wave cleared that) — a partial residual. These publish a per-program / per-credit
rate and are rarely funded → unambiguous fillable gap. **PhD / certificate nulls EXCLUDED (largely funded /
per-credit → legitimate omit-with-reason; do not pressure fabrication).** Worst-first (live run 81):
- **UCLA** — master's **98/146 (48 null, 67%)** (ba 141/141, prof 4/4). The largest residual master's gap.
- **NYU** — master's **194/232 (38 null, 84%)** + prof 3/6 (ba 169/169).
- **Yale** — master's 30/38 (8 null) + cert 0/3 (ba 82/82). **UW-Seattle** — master's 138/152 (14 null).
- **UT-Austin** — master's 115/128 (13) + prof 2/5. **UCSD** — master's 54/61 (7). **Penn** — master's 56/63 (7).
- **Cornell** — master's 79/85 (6) + prof 4/5. Scattered professional nulls: Stanford prof 0/2 · Columbia prof 5/8.
**Fix (per university, one PR):** group coverage by `degree_type`; stamp the published per-program /
per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD
or per-credit certificate, record `tuition` in `_standard.omitted` with a reason — never a silent blanket
null, and never the undergrad sticker copied onto a professional school that bills its own higher rate (the
run-76 copy-down tell; BU Law, which genuinely bills the university flat rate, is the verified exception).
Re-measure LIVE per tier.

---

# MEDIUM — flagship seeds · institution-level seeds (seeding is external)

## 4. The flagship seeds (5 programs each) — EMPTY descriptions + null department + 0% tuition + DEAD FEED — severity: medium — first seen run 57 · 2026-06-18
**Georgetown · UC-Davis · UC-Irvine · UNC-Chapel Hill · UVA · Washington U-St Louis** each ship 5 flagship rows
with **null department**, **0% tuition**, and a **DEAD FEED** (posts=0), with bare abbreviation names (BA/BS/
PhD/MBA). (Brown #1117 + Vanderbilt #1121 were CLEARED this cycle — full real-named catalogs, verified LIVE.)
Several carry **3 campus photos** (UC-Davis — still below the ≥4 gold gate); re-measure per institution.
**Enrich (per university, one PR):** a full real-named catalog + per-credential researched descriptions +
real departments + published tuition (per credential level) + a working feed + a ≥4-photo verified gallery,
then deepen toward the full real catalog.

## 5. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
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

# CLEAN (structure + descriptions + tuition-value; no name/structure action) — verified LIVE run 81
- **Gold (description 0-control):** MIT (n=65, 0 on every description metric; real "Science, Technology, and
  Society" major; `name_prefixed=1` is the benign real "Master in City Planning"; cert/PhD tiers null + grad
  rows at its own undergrad sticker — MIT is NOT a tuition reference).
- **Freshly enriched to gold this cycle (verified LIVE):** Brown (n=57) · Vanderbilt (n=103) — real conferred-
  degree names + real departments + field-specific descriptions + tuition + 5-photo galleries + `content_sources`
  set (feed ingest pending). UC-Berkeley "Area Studies" repair (#1123) — resolved to real area programs.
- **Tuition-COMPLETE / near (every published tier filled; PhD/cert omit-with-reason where funded/per-credit):**
  Princeton (43, 100%) · JHU (cert 84/84) · UW-Madison (cert 128/128, but see NAME entry #1) · USC (phd 87/87) ·
  UW-Seattle (phd 90/90) · UF (cert 93/93) · UT-Austin (phd 86/86) · Cornell (phd 70/70) · Berkeley (prof 20/20)
  · Rice (prof 38/38) · Purdue · Dartmouth · Emory · Chicago (but see NAME entry #1) · Columbia · Notre Dame · Duke.
- **Heuristic over-counts to IGNORE (not defects):** MIT's `name_prefixed=1`; a verified flat full-time rate
  EQUAL to undergrad on the general AND a genuinely-flat-rate professional school (BU $69,870 incl. Law JD);
  GT's real "Professional Master's in …" (PMASE); real multi-clause / dual-degree / slash MAJOR names
  ("Materials Science and Engineering", "Electrical and Computer Engineering", "Theater, Dance, and Performance
  Studies", "Radio/Television/Film", "MD/PhD", "JD/MBA") — these are real, NOT CIP rollups (the name tell keys
  on the CIP-title TABLE + the federal suffix forms, NOT on a bare slash or cross-institution sharing). The
  `verbatim_shared` / `frame_abs150` hits on the 24 duplicate-row catalogs are artifacts of the duplicate pair
  (entry #2), NOT a separate description-stub class.
