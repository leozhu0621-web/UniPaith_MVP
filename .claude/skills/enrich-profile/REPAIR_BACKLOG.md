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
`who_its_for` — shipped 0% catalog-wide / type-GAMED to a degree-type template, a generic
degree-TYPE-noun ("Professional program in {field}") / CIP-title-slash / sentence-CASED name on
an otherwise-real catalog, institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured THIS run by a direct
full-fleet crawl: all **300 LIVE institutions** fetched (campus-photo gallery length read from
`school_outcomes.campus_photos`; posts-feed count read as a LIST length — the endpoint ignores
`page_size` and returns the full list, so a 0 is a direct read; `?page_size` is capped at 50 on
`/institutions/search`, 100 on `/programs`) + the **40 program-bearing catalogs fully paginated
(8,024 programs)** run through a per-catalog description-NON-EMPTINESS scan, an exact-duplicate
`(program_name, degree_type)` scan, a name-realness scan (CIP-rollup TITLE / "…and Related
Sciences/Services" / ", General/Other" / `(CIP NN.NN)` / possessive "Bachelor's in" /
bare-abbreviation / generic "{DegreeType} program in {field}" placeholder / embedded-slash tells),
a name-CASING scan (mid-name lowercase content word), and a per-`degree_type` tuition COVERAGE
measure. Over 20 program DETAILS/catalog (`GET /programs/{id}`, deterministic id-sorted sample =
~800 detail fetches) I probed `cip_code` / `who_its_for` (coverage AND distinctness) /
`external_reviews` coverage. Gold MIT (n=65) is the description 0-control but is NOT a tuition,
`cip_code`, OR `who_its_for`-distinctness control (it ships null cert/PhD tiers, null `cip_code`,
AND a type-gamed `who_its_for` of 0.25 distinct).

_Last graded: 2026-06-30 (grader **run 93**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — a CARVE-OUT to the embedded-SLASH
rollup tell: a verified real JOINT/DUAL-degree ("MD/PhD", "JD/MBA", "MSW/MPH"), a COMBINED/DOUBLE
major ("Mathematics/Economics"), and a GENDER-INCLUSIVE ethnic-studies name ("Latina/Latino
Studies", "Chicana/Chicano Studies") are REAL — a blunt "any `/` ⇒ rollup" scan (the FLAG-#3 CI
metric, or an over-zealous repair) FALSE-FLAGS them; the discriminator is unchanged from run 77
(byte-identical to a CIP rollup TITLE is still a FAIL — e.g. UW-Madison "Zoology/Animal Biology" =
CIP 26.0701 — but a real joint/combined/inclusive slash is NOT). Mirrors the run-77 comma-and and
run-92 possessive carve-outs (omit-never-guess in REVERSE). **🟢 STATE HELD vs run 92 — no
regressions, the matcher-core picture is essentially unchanged:** **`cip_code` null only on gold
MIT** (39/40 catalogs 100% in-sample); **all 15 publics still ship the NON-RESIDENT scalar**;
**`who_its_for` 0% on the same 4** (Georgia Tech · UT-Austin · Notre Dame · UW-Seattle) + **type-gamed
on 9** (Berkeley/Penn 0.05 · Columbia/Chicago 0.10 · Caltech 0.11 · Princeton/UF/Michigan 0.15 · MIT
0.25); **master's/professional-tier tuition residual dominated by Georgetown** (master's 6/79 covered
= 73 null). Structure / descriptions (pattern + NON-EMPTINESS, 0/8,024 empty) / exact-dups (0) /
tuition-copy-down (0) / photos (program-bearing all ≥4) / feeds (program-bearing all live, UC-Irvine
still healthy) all gold-clean fleet-wide. **🟡 NEW THIS RUN (small):** UW-Madison ships the CIP-title
slash "Zoology/Animal Biology" on 3 rows (cert/bachelor's/master's) — a name-realness compliance gap
(miss #2) run 92 missed; folded into entry #4. **NO critical entries remain.** See CHANGELOG run 93._

## Fleet at a glance (run 93, live `api.unipaith.co/api/v1` + `origin/main`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (8,024 total); 260 are bare institution-level
  stubs** (0 programs, dead feed, **33 with ZERO campus photo**, 50 more at 1–3 photos, the rest at 4+).
  Seeding is **external**; the routine ENRICHES + REPAIRS only.
- **🟢 NO CRITICAL DEFECTS.** 0 empty/whitespace `description_text` across all 8,024 programs; 0
  exact-duplicate `(program_name, degree_type)` rows on all 40 catalogs; the FABRICATION name-realness
  scan returns ZERO CIP-rollup-TITLE / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other" /
  possessive-mint / bare-abbreviation names (the 19 BU / 8 NYU / 5 UCLA slash rows are VERIFIED REAL
  joint/dual degrees & combined majors, NOT rollups — run-93 carve-out); 0 tuition copy-downs. Every
  program-bearing node carries a ≥4-photo gallery AND a live feed. Deploy pipeline healthy (single head).
- **🔴 matcher-core master's / professional-tier tuition residual (HIGH — clear FIRST):** bachelor's
  ~100% everywhere, but the MASTER'S (and some PROFESSIONAL) tier ships a material null fraction so the
  matcher scores those programs' budget BLIND. Worst by master's null FRACTION (live run 93): **Georgetown
  master's 6/79 covered = 73 null + prof 10/17 = 7 null** (by far the dominant case) · **WashU masters 4/10
  = 6 null** · **UVA masters 8/16 = 8 null** · **UC-Irvine masters 10/21 = 11 null + prof 3/4 = 1 null** ·
  **UC-Davis masters 15/19 = 4 null**. **Professional-tier-only nulls (FAIL — professional publishes its
  own rate): Columbia prof 6/8 = 2 null · UT-Austin prof 2/5 = 3 null · NYU prof 4/6 = 2 null.** Low-fraction
  master's residuals (≤16% null — likely legitimate per-program funded/per-credit omits, re-verify before
  filling): USC 12 null/261 · UW-Seattle 14/152 · Cornell 6/85 · Penn 6/63 · Harvard 5/90 · Yale 6/38 ·
  UCSD 5/59 · NYU 5/232 · Dartmouth 3/16. **PhD nulls EXCLUDED** (largely funded → legitimate
  omit-with-reason); **certificate nulls** per-credit → omit-with-reason unless the school publishes a flat
  figure. Entry #1. Rule EXISTS (run 74) → COMPLIANCE GAP.
- **🔴 matcher-core `cip_code` — only MIT null:** `cip_code` (the CIP join key to `ref_majors` + the
  field-66 vocabulary) is NULL only on **MIT** (description control) — 65 programs scored field-blind. The
  other 39 catalogs are 100% in-sample. Entry #2. Rule EXISTS (run 82) → COMPLIANCE GAP; durable enforcement
  is FLAG #2.
- **🟢 PUBLIC resident-tuition scalar — CLEAN fleet-wide:** the CPEF budget feature reads the FLAT
  `program.tuition` scalar; all **15** publics ship the NON-RESIDENT (out-of-state) rate (Berkeley 50,547 ·
  UCLA 49,679 · UC-Davis 49,402 · UC-Irvine 50,958 · UCSD 50,958 · GT 32,938 · UT-Austin 44,908 · Michigan
  63,480 · UVA 59,512 · UW-Seattle 44,460 · Purdue 28,794 · UF 28,659 · UIUC 38,398 · UNC 43,152 · UW-Madison
  47,210). No public mis-signal remains.
- **🟡 `who_its_for` 0% (non-null) on 4 catalogs:** Georgia Tech · UT-Austin · Notre Dame · UW-Seattle.
  Entry #3a. Rule EXISTS (run 84/86) → COMPLIANCE GAP.
- **🟡 `who_its_for` TYPE-GAMING (9 catalogs 100%-filled but program-indistinct):** a DISTINCTNESS pass
  (distinct strings / 20 sampled) shows **Berkeley 0.05 · Penn 0.05 · Columbia 0.10 · Chicago 0.10 ·
  Caltech 0.11 · Princeton 0.15 · UF 0.15 · Michigan 0.15 · MIT 0.25** collapse `who_its_for` to ~one
  template per degree-type, passing the non-null coverage gate while a CS PhD and a Public-Policy PhD read
  identically. Entry #3b. Rule EXISTS (run 89) → COMPLIANCE GAP; FLAG #4.
- **🟢 `who_its_for` FIELD-SPECIFIC (distinct/total ≈1.0) on 25 catalogs:** Brown · Emory · Purdue ·
  Dartmouth · Georgetown · Vanderbilt · UC-Davis · UCLA · UC-Irvine · UNC · UVA · WashU · Rice · UIUC ·
  UW-Madison · CMU · Duke · JHU · Northwestern · BU · NYU · USC · UCSD · Stanford · Yale (the model for entry #3).
- **🟡 name-realness on otherwise-real catalogs (3 catalogs):** **(a) Penn ships 2 "Professional program
  in {field}" placeholder rows** ("Professional program in Law" → real J.D., "Professional program in
  Veterinary Medicine" → real V.M.D.). **(b) UT-Austin ships 70/338 SENTENCE-CASED names** ("Bachelor of
  Arts in American studies", "… in Art history"). **(c) NEW — UW-Madison ships the CIP-title slash
  "Zoology/Animal Biology" on 3 rows** (cert/bachelor's/master's; CIP 26.0701; real degree "Zoology"). All
  verified-REAL-or-resolvable fields in the wrong FORM/title. Entry #4. Rules EXIST (placeholder run 91;
  casing run 90; CIP-title slash miss #2) → COMPLIANCE GAP; FLAG #3.
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):** sampled
  20/catalog — thinnest **0/20 on Brown · Georgia Tech · NYU · UC-Davis · UCSD · UF · Michigan · USC ·
  UW-Seattle**, richest Rice 10/20 · Purdue 10/20 · Princeton 9/20 · Caltech 9/20 · MIT 8/20. Coverage-gated
  (even gold MIT is 8/20) → a depth-pass priority on structurally-clean catalogs, NOT a fabrication mandate.
  Entry #5.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The "deploy-safe" self-skipping data migration remains a latent cause of stranded enrichments.**
   A heavy per-program data migration wraps `<uni>_profile.apply(session)` in a `lock_timeout`-bounded
   SAVEPOINT, SKIPS the apply rather than hanging boot, yet records as applied so the chain advances —
   Deploy goes GREEN while the data may never run. No stranded enrichment this run, but the mechanism is
   non-deterministic. Durable fix: a prod execution path that ACTUALLY RUNS (one-off job / management
   command, or a migration that retries/blocks and FAILS the deploy if it cannot). (carried.)
2. **`cip_code` coverage — ~100% on all mature catalogs but STILL NO enforced gate.** The fleet reached
   parity by repair, not by a gate; gold MIT remains null. Durable fix = a `cip_code` coverage metric in the
   profile test (~100% non-null per mature catalog). (carried.)
3. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES, is BLIND to EMPTY
   descriptions, AND blind to name CASING + the degree-TYPE-noun placeholder + the CIP-title slash.**
   Fabrication + empties clean this run, but UT-Austin's 70 sentence-cased names, Penn's 2 "Professional
   program in {field}" rows, and UW-Madison's 3 "Zoology/Animal Biology" CIP-title-slash rows shipped
   undetected. Durable fix = a name-realness metric that scans NAMES for fabrication tells (CIP-rollup TITLE,
   `(CIP NN.NN)`, "…and Related", ", General/Other") AND a mid-name lowercase content word (casing) AND a
   leading degree-TYPE-noun placeholder, + a `description_text` NON-EMPTINESS assertion. **The slash sub-check
   MUST carve out a verified real JOINT/DUAL-degree ("MD/PhD"), COMBINED/DOUBLE major ("Mathematics/Economics"),
   and GENDER-INCLUSIVE ethnic-studies name ("Latina/Latino Studies") — flag ONLY a field byte-identical to a
   CIP rollup TITLE (run-93 carve-out), or it false-flags dozens of real degrees.** **The possessive-mint
   sub-metric MUST carve out a verified branded credential (GT's "Professional Master's in {field}" / PMASE) —
   key on the BARE LEADING possessive form (run-92 carve-out).** (carried + extended.)
4. **No `who_its_for` distinctness / hard-null regression gate.** The coverage metric asserts NON-NULL only —
   which TYPE-GAMING passes (every program one template). The metric must assert DISTINCTNESS (distinct
   `who_its_for` strings / programs ≈ 1.0, FAIL well under ~0.5) AND a lint/grep gate must FAIL on a literal
   `p.<coverable_field> = None` in an `apply()` loop. App/test code. (carried.)
5. **The catalog build dedups on `slug`, not the rendered `(program_name, degree_type)`, and
   `_catalog_errors` never asserts name uniqueness.** Clean this run (0 dups). Durable fix: dedup the build
   UNION on `(program_name, degree_type)` + a uniqueness assertion in `test_anti_stub_gate.py`. (carried.)
6. **The CPEF budget feature is RESIDENCY-BLIND:** `matching.py` reads the single `program.tuition` scalar
   with no in-state/out-of-state branch on the student's residency. The non-resident-scalar default (all 15
   publics) is the stopgap; the durable fix is residency-aware matching reading `tuition_in_state` vs
   `tuition_out_of_state` by the student's residency/country. (carried.)
7. **No enforced gate on tuition VALUE or COVERAGE.** Durable fix = a `tuition_value_artifacts` metric +
   per-tier coverage; key the copy-down FAIL on a professional row at the flat undergrad sticker ONLY when
   that school publishes a distinct higher rate (must NOT fail `grad==undergrad` unconditionally —
   false-flags BU's verified flat rate). A master's/professional COVERAGE sub-check (FAIL a whole
   master's/professional tier shipped >20% null beside a filled peer) makes entry #1 durable, while EXCLUDING
   PhD + per-credit certificate tiers (legitimate omit-with-reason). (carried.)
8. **The `test_alembic_has_single_head` gate asserts single-head on the PR branch, not the post-merge
   `origin/main` result.** Single head clean this run. Durable fix: assert single-head on the rebased merge
   result / `origin/main` POST-MERGE. (carried, lower priority.)
9. **A durable feed-staleness alert is still worth adding** — flag a node whose `content_sources` is set but
   whose post count stays 0 for N days post-ship. No node currently stranded (UC-Irvine recovered run 92).
   (carried, low priority.)

---

# HIGH — matcher-core master's / professional-tier tuition residual (clear FIRST — highest matcher leverage)

## 1. Georgetown · WashU · UVA · UC-Irvine · UC-Davis + professional-tier residuals — partial master's/professional tuition null — severity: high — first seen run 74 — 2026-06-30
Structurally + description clean catalogs whose bachelor's tier is ~100% but whose MASTER'S (and some
PROFESSIONAL) tier ships a material null fraction (the matcher scores those graduate programs' budget-fit
BLIND). Worst by master's null FRACTION (live run 93): **Georgetown master's 6/79 covered = 73 null + prof
10/17 = 7 null** (by far the dominant case) · **WashU masters 4/10 = 6 null** · **UVA masters 8/16 = 8 null** ·
**UC-Irvine masters 10/21 = 11 null + prof 3/4 = 1 null** · **UC-Davis masters 15/19 = 4 null**.
**Professional-tier-only nulls (these publish a rate → FAIL): Columbia prof 6/8 = 2 null · UT-Austin prof
2/5 = 3 null · NYU prof 4/6 = 2 null.** **Fix (per university):** group coverage by `degree_type`; stamp the
published per-program / per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate, rarely
funded). For a PhD or per-credit certificate, record `tuition` in `_standard.omitted` with a reason — never a
silent blanket null, and never the undergrad sticker copied onto a professional school that bills its own
higher rate. **PhD / certificate nulls EXCLUDED** (largely funded / per-credit → legitimate omit-with-reason).
Low-fraction (≤16% null) master's residuals on USC · UW-Seattle · Cornell · Penn · Harvard · Yale · UCSD · NYU ·
Dartmouth are likely legitimate per-program funded/per-credit omits — re-verify each before filling, never
fabricate. Re-measure LIVE per tier. Rule EXISTS (run 74) → compliance/repair. Durable enforcement = FLAG #7.

---

# HIGH — matcher-core `cip_code` (lone residual)

## 2. MIT — the last catalog shipping `cip_code` null — severity: high — first seen run 82 — 2026-06-30
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the
field-66 vocabulary. NULL remains only on **MIT** — 65 programs scored field-blind (the other 39 catalogs are
100% in-sample). **Fix:** stamp `p.cip_code = spec.get("cip")` (the IPEDS CIP already used for the breadth
cross-check), exactly as the 39 other catalogs do — never a guess, omit-with-reason only for a genuinely
uncodeable program. MIT is the DESCRIPTION 0-control, NOT a `cip_code` reference — its null must be repaired,
not imitated. Re-measure LIVE to ~100%. Rule EXISTS (run 82) → compliance/repair. Durable enforcement = FLAG #2.

---

# MEDIUM — `who_its_for` (0% + type-gamed) · name realness (placeholder + casing + CIP-title slash) · reviews · bulk seeds

## 3. `who_its_for` — 4 catalogs 0% (un-done) AND 9 catalogs TYPE-GAMED (coverage-passing, indistinct) — severity: medium — first seen run 84 (0%) / run 89 (type-gaming) — 2026-06-30
`who_its_for` ("Who it's for", a manifest field) is derivable for EVERY program from its own published
audience/fit material, so both failure modes below are un-done depth, not honest omission.
**(a) 0% (non-null) on 4 catalogs** — Georgia Tech · UT-Austin · Notre Dame · UW-Seattle.
**(b) TYPE-GAMED on 9 catalogs (100% non-null but ONE degree-type template per tier)** — Berkeley 0.05 · Penn
0.05 · Columbia 0.10 · Chicago 0.10 · Caltech 0.11 · Princeton 0.15 · UF 0.15 · Michigan 0.15 · MIT 0.25
(distinct strings / 20 sampled).
**Fix (per catalog, in the SAME pass as tuition):** build a `_WHO_BY_SLUG` dict of field-specific 1–2 sentence
statements (subject, methods, who it fits, next step) — the bar the 25 field-specific catalogs already meet
(distinct/total ≈1.0). The `_WHO_BY_TYPE` fallback is a narrow last resort, never the primary fill; never
`= None`. Re-measure LIVE for BOTH coverage (~100%) AND distinctness (≈1.0). Rule EXISTS run 84/86 (0%) + run
89 (distinctness) → compliance/repair. Durable enforcement = FLAG #4.

## 4. Name-realness on otherwise-real catalogs — (a) Penn degree-TYPE-noun placeholder · (b) UT-Austin sentence-casing · (c) UW-Madison CIP-title slash — severity: medium — first seen run 91 (placeholder) / run 90 (casing) / run 93 (CIP-title slash) — 2026-06-30
**(a) Penn degree-TYPE-noun placeholder NAMES (2 rows).** Penn ships "Professional program in Law" +
"Professional program in Veterinary Medicine" — the `degree_type` value ("professional") title-cased AS the
program name in place of Penn's published conferred designation. **Fix:** resolve each to the real conferred
designation — Penn "Professional program in Law" → "Juris Doctor (J.D.)", Penn "Professional program in
Veterinary Medicine" → "Veterinary Medical Doctor (V.M.D.)" — verify each against Penn's catalog; never the
degree_type label, never invent a degree. Baked into `penn_profile.py`. Re-measure LIVE: 0 "{DegreeType}
program in {field}" names. Rule EXISTS (run 91) → compliance/repair. **NOTE — Georgia Tech's 3 "Professional
Master's in {field}" rows are VERIFIED REAL (PMASE etc.), NOT this defect; do NOT "resolve" them (run-92
carve-out).**
**(b) UT-Austin sentence-casing (70/338, un-repaired since run 90).** 70 bachelor's rows ship the field part
SENTENCE-CASED — "Bachelor of Arts in American studies", "… in Art history", "… in Asian studies", "… in
Classical languages", "… in Behavioral and social data science". Verified-REAL degrees in the WRONG CASE — the
form the student reads on the explore card + detail page. **Fix:** re-case every `program_name` (and any
matching `department`) to UT-Austin's PUBLISHED title-case ("Bachelor of Arts in American Studies", "… in Art
History"), PRESERVING legitimate lowercase (parentheticals, post-positives, acronyms) — only its
capitalization, never a word. Baked into `ut_austin_profile.py`. Re-measure LIVE: 0 mid-name lowercase content
words. Rule EXISTS (run 90) → compliance/repair. Durable enforcement = FLAG #3.
**(c) NEW — UW-Madison CIP-title slash "Zoology/Animal Biology" (3 rows: cert/bachelor's/master's).** Byte-
identical to federal CIP 26.0701 "Zoology/Animal Biology", minted across three award levels of one field (the
IPEDS×award-level fingerprint); UW-Madison's real degree is "Zoology" (Department of Integrative Biology).
**Fix:** resolve the field to the real published degree name ("Bachelor of Science in Zoology", "Master of
Science in Zoology", "Graduate Certificate in Zoology") — never the CIP title. Baked into the UW-Madison
profile module. Re-measure LIVE: 0 CIP-rollup-title slashes. Rule EXISTS (miss #2 CIP-title) → compliance/repair.
**NOTE — the 19 BU / 8 NYU / 5 UCLA slash rows + the Latina/o & Chicana/o majors across ≥6 catalogs are
VERIFIED REAL joint/dual degrees, combined majors, and gender-inclusive names, NOT this defect; do NOT "resolve"
them (run-93 carve-out).**

## 5. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 — 2026-06-30
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass.
Sampled 20/catalog: 0/20 on Brown · Georgia Tech · NYU · UC-Davis · UCSD · UF · Michigan · USC · UW-Seattle;
richest Rice 10/20 · Purdue 10/20 · Princeton 9/20 · Caltech 9/20 · MIT 8/20. **Calibrate — reviews are
coverage-gated; do NOT fabricate (even gold MIT is 8/20).** **Enrich:** on a structurally-clean catalog, run
the reviews depth pass over programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports /
program outcomes reports) — program-specific summary + themes + resolvable sources, no synthesized-from-metadata
reviews (miss #8) — and record `external_reviews` in `_standard.omitted` with a reason where a program genuinely
has no coverage.

## 6. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first: Air Force Institute
of Technology · Arizona State (Campus + Digital Immersion) · Azusa Pacific · Colorado State-Fort Collins ·
James Madison · Keiser-Ft Lauderdale · Loyola Marymount · Loyola-Chicago · Miami-Oxford · Michigan Tech ·
Montclair State · Northcentral · Oakland · Oregon State · SUNY-ESF · Sacred Heart · Stephen F Austin ·
Texas A&M (Commerce + Corpus Christi) · Thomas Jefferson · Univ Ana G Mendez-Gurabo · UAB · Dayton ·
Houston · Kentucky · Louisville · Maryland-Baltimore County · Missouri-St Louis · Nebraska-Lincoln ·
Oklahoma-Norman · Utah · Virginia Commonwealth), plus 50 more at 1–3 photos. **Enrich (per university —
after the HIGH tier clears):** a full real-named, TITLE-CASED catalog with **field-specific
`description_text` on every program** + the real conferred degree designation (never "{DegreeType} program in
{field}", never a CIP-title slash) + PROGRAM-DISTINCT `who_its_for` (never a degree-type template, never
`= None`) + real departments + published tuition (non-resident scalar for publics; the master's/professional
tier filled, not just bachelor's) + `cip_code` · a working feed · a ≥4-photo verified gallery · reviews on
coverable programs · `_standard`. Pick a 0-photo seed once the higher tiers clear.

---

# CLEAN (structure + descriptions(pattern + NON-EMPTINESS) + names(fabrication) + tuition-value-copy-down + exact-dup + photos + feeds + public-scalar + cip_code(39/40) + deploy; no action) — verified LIVE run 93
- **Gold (description 0-control):** MIT (n=65, real "Science, Technology, and Society" major; but type-gamed
  `who_its_for` 0.25 + null cert/PhD tiers + null `cip_code` — MIT is a description control ONLY, not a
  tuition / `cip_code` / who-distinctness reference; its `cip_code` null is entry #2, not a model).
- **`cip_code`-COMPLETE (39 of 40, the model for entry #2):** every mature catalog EXCEPT MIT (100% in-sample).
- **`who_its_for` FIELD-SPECIFIC (the distinctness model for entry #3b — distinct/total ≈1.0, 25 catalogs):**
  Brown · Emory · Purdue · Dartmouth · Georgetown · Vanderbilt · UC-Davis · UCLA · UC-Irvine · UNC · UVA ·
  WashU · Rice · UIUC · UW-Madison · CMU · Duke · JHU · Northwestern · BU · NYU · USC · UCSD · Stanford · Yale.
- **PUBLIC non-resident scalar CORRECT (all 15):** Georgia Tech · UT-Austin · Berkeley · UCLA · UC-Davis ·
  UC-Irvine · UCSD · UNC · UVA · UW-Seattle · Michigan · Purdue · UF · UIUC · UW-Madison (bachelor `tuition`
  = oos, verified live).
- **EXACT-DUPLICATE / NAME-FABRICATION / EMPTY-DESC / TUITION-COPY-DOWN / PHOTO / FEED classes CLEAN
  fleet-wide:** 0 raw `(program_name, degree_type)` repeats, 0 fabricated names (the slash rows are VERIFIED
  REAL joint/dual/combined/inclusive degrees — run-93 carve-out — except UW-Madison's 3 CIP-title rows in
  entry #4c), 0 empty descriptions (0/8,024), no undergrad-sticker copy-down, every program-bearing node ≥4
  campus photos AND a live feed.
- **DEPLOY PIPELINE HEALTHY:** single head, migrations applying in prod.
