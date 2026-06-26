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
degree-TYPE-noun ("Professional program in {field}") OR sentence-CASED name on an otherwise-real
catalog, institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured THIS run by a direct
full-fleet crawl: all **300 LIVE institutions** fetched (campus-photo gallery length + posts-feed
count — **feed count read as a LIST length, not `.total`/`?page_size`; the endpoint ignores
`page_size` and returns the full list, so a 0 is verified by re-fetching directly to rule out a
concurrent-crawl timeout**) + the **40 program-bearing catalogs fully paginated (8,024 programs)**
and run through a per-catalog description-NON-EMPTINESS scan, an exact-duplicate
`(program_name, degree_type)` scan, a name-realness scan (CIP-rollup TITLE / "…and Related
Sciences/Services" / ", General/Other" / `(CIP NN.NN)` / possessive "Bachelor's in" /
bare-abbreviation / **NEW: generic "{DegreeType} program in {field}" placeholder** tells), a
name-CASING scan (mid-name lowercase content word, `as` added to the connective carve-out), and a
per-`degree_type` tuition COVERAGE measure. Over 20 program DETAILS/catalog (`GET /programs/{id}`,
deterministic id-sorted sample) I probed `cip_code` / `who_its_for` (coverage AND distinctness) /
`external_reviews` coverage and the public bachelor `tuition`-scalar-vs-`cost_data.breakdown`
resident/non-resident axis. Gold MIT (n=65) is the description 0-control but is NOT a tuition,
`cip_code`, OR `who_its_for`-distinctness control (it ships null cert tiers, grad rows at its own
undergrad sticker, null `cip_code`, AND a TYPE-GAMED `who_its_for` of 0.25 distinct).

_Last graded: 2026-06-26 (grader **run 91**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — a genuinely NEW name-realness tell:
the **generic degree-TYPE-noun placeholder** "{DegreeType} program in {field}". Cornell ships
"Professional program in Music" + "Professional program in Veterinary Medicine" and Penn ships
"Professional program in Law" + "Professional program in Veterinary Medicine" — the `degree_type`
value title-cased AS the program name, in place of the real conferred designation (J.D. / D.V.M. /
V.M.D. / D.M.A.). It evades the possessive-mint tells (those key on "Bachelor's/Master's/Doctorate
in"), so the rule was added as a sibling tell under miss #2's designation bullet. **🟢 BIG PROGRESS
since run 90 — the enricher cleared backlog entries via PRs #1195 (Northwestern) · #1197 (Duke) ·
#1198/#1199 (CMU) · #1200 (JHU):** cip-null **11→7**, who-0% **12→8**, all four now ship distinct
field-specific `who_its_for` (distinct ≈1.0). Structure / descriptions(pattern + NON-EMPTINESS) /
NAMES(fabrication) / exact-dups / tuition-copy-down / photos(program-bearing all 4+) remain
gold-clean fleet-wide (0/8,024 empty, 0 dups, 0 fabricated names, 0 copy-downs). **🔴 UC-Irvine
dead feed PERSISTS** — posts=0 (directly verified, list len 0) a week+ while every other
program-bearing node ingests (Cornell 2,067 · Chicago 1,478) → an INGEST/OPS failure (FLAG #9), not
a data or rule defect. **🟡 UT-Austin casing 70/338 + the new Cornell/Penn placeholder rows remain
un-repaired** (the casing rule landed run 90; the placeholder rule lands this run). NO critical
entries remain. See CHANGELOG run 91._

## Fleet at a glance (run 91, live `api.unipaith.co/api/v1` + `origin/main`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (8,024 total); 260 are bare institution-level
  stubs** (0 programs, dead feed, **33 with ZERO campus photo**, 50 more at 1–3 photos, **177 at 4+**).
  Seeding is **external**; the routine ENRICHES + REPAIRS only.
- **🟢 NO CRITICAL DEFECTS.** 0 empty/whitespace `description_text` across all 8,024 programs; 0
  exact-duplicate `(program_name, degree_type)` rows on all 40 catalogs; the FABRICATION name-realness
  scan returns ZERO CIP-rollup / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other" /
  possessive "Bachelor's in" / bare-abbreviation names; 0 tuition copy-downs. Every program-bearing node
  carries a ≥4-photo gallery. Deploy pipeline healthy (single head, migrations applying in prod).
- **🆕 🟡 generic degree-TYPE-noun placeholder NAME (NEW class — 2 catalogs, 4 rows):** Cornell +
  Penn ship "Professional program in Music / Law / Veterinary Medicine" — the `degree_type` value
  ("professional") title-cased AS the program name in place of the real conferred designation (J.D. /
  D.V.M. / V.M.D. / D.M.A.). Verified-real programs, generic-NAMED; evades every prior name gate (those
  key on possessive-mint or fabrication tells, none on the degree-type-noun form). Entry #5a. Rule ADDED
  run 91 → name-realness "{DegreeType} program in {field}" tell; FLAG #3 (extend the name-realness
  metric to this tell + casing).
- **🟡 program-name CASING (1 catalog, 70 rows, un-repaired since run 90):** UT-Austin ships **70/338**
  SENTENCE-CASED field names ("Bachelor of Arts in American studies", "… in Art history", "… in Asian
  studies"). Every other catalog title-cases (gold MIT 0/65). Entry #5b. Rule EXISTS (run 90) →
  COMPLIANCE GAP, queued; FLAG #3.
- **🔴 matcher-core `cip_code` STARVATION (7 mature catalogs null + MIT control, was 11):** `cip_code`
  (the CIP join key to `ref_majors` + the field-66 vocabulary) is NULL on **BU · Cornell · Harvard ·
  NYU · Stanford · USC · Yale** (+ MIT control) — so the matcher scores those ~3,200 programs
  field-blind. **CLEARED since run 90: CMU · Duke · JHU · Northwestern** (100% in-sample). Entry #1.
  Rule EXISTS (run 82) → COMPLIANCE GAP, queued; durable enforcement is FLAG #2.
- **🔴 PUBLIC resident-tuition scalar MIS-SIGNAL (1 public still in-state, unchanged):** the CPEF
  budget feature reads the FLAT `program.tuition` scalar, NOT a residency-aware estimator. Only **UCSD**
  still ships the IN-STATE rate (scalar **16,758** while `cost_data.breakdown.tuition_out_of_state` =
  **50,958**). All 14 other publics correct (oos scalar verified live). Entry #2. Rule EXISTS (run 83)
  → COMPLIANCE GAP; durable fix is FLAG #6.
- **🔴 master's / professional-tier tuition residual:** bachelor's ~100% everywhere, but the MASTER'S
  (and some PROFESSIONAL) tier ships a material null fraction (matcher scores those programs' budget
  BLIND). Worst — **Georgetown master's 73/79 + prof 7/17** · **UW-Seattle** masters 14/152 + prof 1/7
  **+ bachelors 1/114** · **USC** masters 12/261 · **UC-Irvine** masters 11/21 + prof 1/4 · **BU**
  masters 7/167 + prof 5/25 · **UT-Austin** masters 7/128 + prof 3/5 · **Yale** masters 8/38 · **UVA**
  masters 7/15 · **NYU** masters 5/232 + prof 2/6 · **Cornell** masters 6/85 + prof 1/5 · **WashU**
  masters 6/10 · **Penn** masters 6/63 · **UCSD** masters 5/59 · **Harvard** masters 5/90 · **UC-Davis**
  masters 4/19 · **Dartmouth** masters 3/16 · small (Vanderbilt 1/25, Notre Dame 1/24, Michigan 1/99,
  UCLA 1/145). **Professional-tier-only nulls (FAIL — professional publishes its own rate): Stanford
  prof 2/2, Columbia prof 2/8.** **PhD / certificate nulls EXCLUDED** (funded / per-credit → legitimate
  omit-with-reason). Entry #3. Rule EXISTS (run 74) → COMPLIANCE GAP.
- **🟡 `who_its_for` 0% (non-null) on 8 catalogs (was 12):** BU · NYU · USC · Georgia Tech · UCSD ·
  UT-Austin · Notre Dame · UW-Seattle. **CLEARED since run 90: CMU · Duke · JHU · Northwestern** (now
  distinct ≈1.0). ⚠️ **UCLA latent-masked:** reads who 100% / distinct ≈1.0 LIVE only because the #1181
  sibling overwrites a hard-null — `ucla_profile.py` may STILL carry `= None`, a re-apply regression
  waiting to fire. Entry #4a. Rule EXISTS (run 84/86) → COMPLIANCE GAP.
- **🟡 `who_its_for` TYPE-GAMING (13 catalogs 100%-filled but program-indistinct, unchanged):** a
  DISTINCTNESS pass (distinct strings / 20 sampled) shows ~13 catalogs collapse `who_its_for` to ~one
  template per degree-type — **Stanford 0.05 · Berkeley 0.05 · Penn 0.05** · Cornell/Chicago/Columbia
  0.10 · Caltech 0.11 · Yale/Princeton/UF/Michigan 0.15 · Harvard 0.20 · **MIT 0.25** — passing the
  non-null coverage gate while a CS PhD and a Public-Policy PhD read identically. Entry #4b. Rule EXISTS
  (run 89) → COMPLIANCE GAP; FLAG #4.
- **🟢 `who_its_for` FIELD-SPECIFIC (distinct/total ≈1.0) on 19 (was 15):** Brown · Emory · Purdue ·
  Dartmouth · Georgetown · Vanderbilt · UC-Davis · UCLA · UC-Irvine · UNC · UVA · WashU · Rice · UIUC ·
  UW-Madison · **CMU · Duke · JHU · Northwestern** (the distinctness model for entry #4b).
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):**
  sampled 20/catalog — thinnest **0/20 on NYU · USC · Georgia Tech · UCSD · UW-Seattle · UF · Michigan ·
  Brown · UC-Davis**, 1/20 on Notre Dame · Georgetown · UC-Irvine · UNC · UVA · WashU · UIUC; richest
  Rice/Purdue 10/20 · Caltech/Princeton 9/20 · MIT 8/20. Coverage-gated (even gold MIT is 8/20) → a
  depth-pass priority on structurally-clean catalogs, NOT a fabrication mandate. Entry #6.
- **🔴 UC-Irvine DEAD FEED — PERSISTS (ingest/ops, not data):** UC-Irvine (160 programs, 5 photos)
  reads posts=0 (directly verified, list length 0) a week+ after going live, the ONLY program-bearing
  node with a dead feed (Cornell 2,067 · Chicago 1,478 · every other node populated). `uci_profile.py`
  sets `content_sources` (news_rss `https://news.uci.edu/feed/`, `git`-confirmed) AND that RSS is LIVE.
  The enricher COMPLIED with miss #1; the background ingest pipeline simply has not populated UC-Irvine.
  NOT a rule/data defect → FLAG #9 (ops). Entry #7.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The "deploy-safe" self-skipping data migration remains a latent cause of stranded enrichments.**
   A heavy per-program data migration wraps `<uni>_profile.apply(session)` in a `lock_timeout`-bounded
   SAVEPOINT, SKIPS the apply rather than hanging boot, yet records as applied so the chain advances —
   Deploy goes GREEN while the data may never run. No stranded enrichment this run, but the mechanism is
   non-deterministic. Durable fix: a prod execution path that ACTUALLY RUNS (one-off job / management
   command, or a migration that retries/blocks and FAILS the deploy if it cannot). (carried.)
2. **`cip_code` is populated on only ~33 of 40 modules — NO enforced coverage gate.** Durable fix = a
   `cip_code` coverage metric in the profile test (~100% non-null per mature catalog). (carried.)
3. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES, is BLIND to EMPTY
   descriptions, AND blind to name CASING + the degree-TYPE-noun placeholder.** Fabrication + empties
   clean this run, but UT-Austin's 70 sentence-cased names and Cornell/Penn's 4 "Professional program
   in {field}" rows shipped undetected. Durable fix = a name-realness metric that scans NAMES for
   fabrication tells AND a mid-name lowercase content word (casing) AND a leading degree-TYPE-noun
   placeholder ("{DegreeType} program in {field}"), + a `description_text` NON-EMPTINESS assertion
   (~100% non-empty per catalog). (carried + extended to the placeholder tell.)
4. **No `who_its_for` distinctness / hard-null regression gate.** The existing/proposed coverage metric
   asserts NON-NULL only — which TYPE-GAMING passes (every program one template). The metric must assert
   DISTINCTNESS (distinct `who_its_for` strings / programs ≈ 1.0, FAIL well under ~0.5) AND a lint/grep
   gate must FAIL on a literal `p.<coverable_field> = None` in an `apply()` loop (incl. `ucla_profile.py`,
   whose hard-null is sibling-masked). App/test code. (carried.)
5. **The catalog build dedups on `slug`, not the rendered `(program_name, degree_type)`, and
   `_catalog_errors` never asserts name uniqueness.** Clean this run (0 dups). Durable fix: dedup the
   build UNION on `(program_name, degree_type)` + a uniqueness assertion in `test_anti_stub_gate.py`.
   (carried.)
6. **The CPEF budget feature is RESIDENCY-BLIND:** `matching.py` reads the single `program.tuition`
   scalar with no in-state/out-of-state branch on the student's residency. The non-resident-scalar
   default (entry #2) is the stopgap; the durable fix is residency-aware matching reading
   `tuition_in_state` vs `tuition_out_of_state` by the student's residency/country. (carried.)
7. **No enforced gate on tuition VALUE or COVERAGE.** Durable fix = a `tuition_value_artifacts` metric +
   per-tier coverage; key the copy-down FAIL on a professional row at the flat undergrad sticker ONLY
   when that school publishes a distinct higher rate (must NOT fail `grad==undergrad` unconditionally —
   false-flags BU's + USC's verified flat rates). A public-scalar sub-check (FAIL when the bachelor
   `tuition` scalar == `breakdown.tuition_in_state` while a higher `tuition_out_of_state` exists) makes
   entry #2 durable. (carried.)
8. **The `test_alembic_has_single_head` gate asserts single-head on the PR branch, not the post-merge
   `origin/main` result.** Single head clean this run. Durable fix: assert single-head on the rebased
   merge result / `origin/main` POST-MERGE. (carried, lower priority.)
9. **The background feed-ingest pipeline stranded UC-Irvine.** `content_sources` is set and the RSS
   source is live, but `/institutions/{uci}/posts` has read 0 (list length 0) for a week+ while every
   other enriched node ingests. The enricher cannot fix an async ingest job from a profile module.
   Durable fix: a re-ingest / backfill trigger for a node whose `content_sources` is set but whose feed
   stays empty N days post-ship, + an alert when an enriched node's post count is 0. Ops/app code.
   (carried.)

---

# HIGH — matcher-core `cip_code` STARVATION (clear FIRST — highest matcher leverage, one assignment)

## 1. The 7 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 — 2026-06-26
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the
field-66 vocabulary. NULL on **BU · Cornell · Harvard · NYU · Stanford · USC · Yale** (+ MIT control) —
~3,200 programs scored field-blind. **Fix (one fleet sweep, or per catalog):** stamp `p.cip_code =
spec.get("cip")` (the IPEDS CIP already used for the breadth cross-check), exactly as the cleared modules
(CMU/Duke/JHU/Northwestern/Rice/UF/UIUC/UW-Madison + the long-clean fillers) do — never a guess,
omit-with-reason only for a genuinely uncodeable program. Re-measure LIVE per catalog to ~100%.
**CLEARED since run 90: CMU · Duke · JHU · Northwestern.** Rule EXISTS (run 82) → compliance/repair.
Durable enforcement = FLAG #2.

---

# HIGH — PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 2. UCSD — the last public catalog shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 — 2026-06-26
The CPEF budget feature reads the FLAT `program.tuition` scalar, NOT a residency-aware estimator. Only
**UCSD** is still in-state: scalar **16,758** while `cost_data.breakdown.tuition_out_of_state` = **50,958**
(both rates honest in the breakdown; only the exposed scalar is wrong). 14 publics now correct (GT ·
UT-Austin · Berkeley · UCLA · UC-Davis · UC-Irvine · UNC · UVA · UW-Seattle · Michigan · Purdue · UF ·
UIUC · UW-Madison — all verified live with oos scalar). **Fix:** stamp the NON-RESIDENT sticker
(`breakdown.tuition_out_of_state` = 50,958) into the scalar `tuition`, keeping BOTH rates in the
breakdown. Re-measure LIVE. See FLAG #6 — durable fix is residency-aware matching. Rule EXISTS (run 83) →
compliance/repair.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 3. Georgetown · UW-Seattle · USC + residuals — partial master's/professional tuition null — severity: high — first seen run 74 — 2026-06-26
Structurally + description clean catalogs whose bachelor's tier is ~100% but whose MASTER'S (and some
PROFESSIONAL) tier ships a material null fraction (the matcher scores those graduate programs' budget-fit
BLIND). Worst by master's null count (live run 91): **Georgetown master's 73/79 + prof 7/17** ·
**UW-Seattle** masters 14/152 + prof 1/7 **+ a stray bachelors 1/114** · **USC** masters 12/261 ·
**UC-Irvine** masters 11/21 + prof 1/4 · **BU** masters 7/167 + prof 5/25 · **UT-Austin** masters 7/128 +
prof 3/5 · **Yale** masters 8/38 · **UVA** masters 7/15 · **NYU** masters 5/232 + prof 2/6 · **Cornell**
masters 6/85 + prof 1/5 · **WashU** masters 6/10 · **Penn** masters 6/63 · **UCSD** masters 5/59 ·
**Harvard** masters 5/90 · **UC-Davis** masters 4/19 · **Dartmouth** masters 3/16 · small (Vanderbilt
1/25, Notre Dame 1/24, Michigan 1/99, UCLA 1/145). **Professional-tier-only nulls (these publish a rate →
FAIL): Stanford prof 2/2, Columbia prof 2/8.** **Fix (per university):** group coverage by `degree_type`;
stamp the published per-program / per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish
a rate, rarely funded). Check the lone bachelors null (UW-Seattle 1/114) — fill it or record
`_standard.omitted` with a reason. For a PhD or per-credit certificate, record `tuition` in
`_standard.omitted` with a reason — never a silent blanket null, and never the undergrad sticker copied
onto a professional school that bills its own higher rate (BU's $69,870 = VERIFIED BU Law; the 4
single-value prof tiers Brown/Dartmouth/JHU/Notre Dame are DISTINCT-and-higher, not copy-downs). **PhD /
certificate nulls EXCLUDED** (largely funded / per-credit → legitimate omit-with-reason). Re-measure LIVE
per tier.

---

# MEDIUM — `who_its_for` (0% + type-gamed) · name realness (placeholder + casing) · reviews · UC-Irvine feed · bulk seeds

## 4. `who_its_for` — 8 catalogs 0% (un-done) AND 13 catalogs TYPE-GAMED (coverage-passing, indistinct) — severity: medium — first seen run 84 (0%) / run 89 (type-gaming) — 2026-06-26
`who_its_for` ("Who it's for", a manifest field) is derivable for EVERY program from its own published
audience/fit material, so both failure modes below are un-done depth, not honest omission.
**(a) 0% (non-null) on 8 catalogs** — BU · NYU · USC · Georgia Tech · UCSD · UT-Austin · Notre Dame ·
UW-Seattle. **CLEARED since run 90: CMU · Duke · JHU · Northwestern** (now distinct ≈1.0). ⚠️ **UCLA
latent-masked** — reads 100% / distinct ≈1.0 LIVE only via the #1181 sibling overwrite; check
`ucla_profile.py` for a residual `= None` and remove it from the base module.
**(b) TYPE-GAMED on 13 catalogs (100% non-null but ONE degree-type template per tier)** — Stanford 0.05 ·
Berkeley 0.05 · Penn 0.05 · Cornell/Chicago/Columbia 0.10 · Caltech 0.11 · Yale/Princeton/UF/Michigan
0.15 · Harvard 0.20 · **MIT 0.25** (distinct strings / 20 sampled). Every PhD reads "a funded <school>
doctorate", every bachelor's "a top public-research undergraduate education" — passing the coverage gate
while a CS PhD and a Public-Policy PhD read identically.
**Fix (per catalog, in the SAME pass as cip/tuition):** build a `_WHO_BY_SLUG` dict of field-specific 1–2
sentence statements (subject, methods, who it fits, next step) — the bar Brown/Emory/Purdue/Dartmouth/
Georgetown/Vanderbilt/UC-Davis/UCLA/UC-Irvine/UNC/UVA/WashU/Rice/UIUC/UW-Madison/CMU/Duke/JHU/Northwestern
already meet (distinct/total ≈1.0). The `_WHO_BY_TYPE` fallback is a narrow last resort, never the primary
fill; never `= None`. Re-measure LIVE for BOTH coverage (~100%) AND distinctness (≈1.0). Rule EXISTS run
84/86 (0%) + run 89 (distinctness) → compliance/repair. Durable enforcement = FLAG #4.

## 5. Name-realness on otherwise-real catalogs — (a) Cornell/Penn degree-TYPE-noun placeholder + (b) UT-Austin sentence-casing — severity: medium — first seen run 91 (placeholder) / run 90 (casing) — 2026-06-26
**(a) NEW — generic degree-TYPE-noun placeholder NAMES (Cornell + Penn, 4 rows).** Cornell ships
"Professional program in Music" + "Professional program in Veterinary Medicine"; Penn ships "Professional
program in Law" + "Professional program in Veterinary Medicine" — the `degree_type` value ("professional")
title-cased AS the program name in place of the institution's published conferred designation. These are
verified-REAL programs named with a generic placeholder, and they evade every prior name gate (those key
on possessive-mint / fabrication tells, none on the degree-type-noun form). **Fix:** resolve each to the
real conferred designation — Cornell "Professional program in Veterinary Medicine" → "Doctor of Veterinary
Medicine (D.V.M.)", Penn "Professional program in Law" → "Juris Doctor (J.D.)", Penn "Professional program
in Veterinary Medicine" → "Veterinary Medical Doctor (V.M.D.)", Cornell "Professional program in Music" →
the school's published professional-music degree (e.g. "Doctor of Musical Arts (D.M.A.)") — verify each
designation against the school's catalog; never the degree_type label, never invent a degree. The defect
is baked into `cornell_profile.py` / `penn_profile.py`. Re-measure LIVE: 0 "{DegreeType} program in
{field}" names. Rule ADDED run 91 → compliance after the rule lands. Durable enforcement = FLAG #3.
**(b) UT-Austin sentence-casing (70/338, un-repaired since run 90).** 70 bachelor's rows ship the field
part SENTENCE-CASED — "Bachelor of Arts in American studies", "… in Art history", "… in Asian studies",
"… in Classical languages", "… in Behavioral and social data science". Verified-REAL degrees in the WRONG
CASE — the form the student reads on the explore card + detail page. **Fix:** re-case every `program_name`
(and any matching `department`) to UT-Austin's PUBLISHED title-case ("Bachelor of Arts in American
Studies", "… in Art History", "… in Asian Studies"), PRESERVING legitimate lowercase (parentheticals,
post-positives, acronyms) — only its capitalization, never a word. Baked into `ut_austin_profile.py`.
Re-measure LIVE: 0 mid-name lowercase content words. Rule EXISTS (run 90) → compliance/repair. Durable
enforcement = FLAG #3 (extend the name-realness metric to casing + the placeholder tell).

## 6. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 — 2026-06-26
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass.
Sampled 20/catalog: 0/20 on NYU · USC · Georgia Tech · UCSD · UW-Seattle · UF · Michigan · Brown ·
UC-Davis; 1/20 on Notre Dame · Georgetown · UC-Irvine · UNC · UVA · WashU · UIUC; richest Rice/Purdue
10/20 · Caltech/Princeton 9/20 · MIT 8/20. **Calibrate — reviews are coverage-gated; do NOT fabricate
(even gold MIT is 8/20).** **Enrich:** on a structurally-clean catalog, run the reviews depth pass over
programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports / program outcomes
reports) — program-specific summary + themes + resolvable sources, no synthesized-from-metadata reviews
(miss #8) — and record `external_reviews` in `_standard.omitted` with a reason where a program genuinely
has no coverage.

## 7. UC-Irvine dead feed — PERSISTS (ingest/ops) — severity: medium — first seen run 87 (watch) / escalated run 89 / persists run 90–91 — 2026-06-26
UC-Irvine (160 programs) is the ONLY program-bearing node reading posts=0 (directly verified, list length
0), a week+ after going live, while every other enriched node ingests (Cornell 2,067 · Chicago 1,478 · all
others populated). `uci_profile.py` sets `content_sources` (news_rss `https://news.uci.edu/feed/`,
`git`-confirmed) AND that feed is LIVE. The enricher COMPLIED — this is an INGEST/OPS failure, not a data
or rule defect. **No enricher action** (omitting or re-stamping content_sources would not help); → FLAG #9
for an ops re-ingest trigger. The enricher may note it in `_standard.omitted` with the ops reason but must
NOT fabricate posts.

## 8. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first: Air Force Institute
of Technology · Arizona State (Campus + Digital) · Azusa Pacific · Colorado State-Fort Collins · James
Madison · Keiser-Ft Lauderdale · Loyola Marymount · Loyola-Chicago · Miami-Oxford · Michigan Tech ·
Montclair State · Northcentral · Oakland · Oregon State · SUNY-ESF · Sacred Heart · Stephen F Austin ·
Texas A&M (Commerce + Corpus Christi) · Thomas Jefferson · Univ Ana G Mendez-Gurabo · UAB · Dayton ·
Houston · Kentucky · Louisville · Maryland-Baltimore County · Missouri-St Louis · Nebraska-Lincoln ·
Oklahoma-Norman · Utah · Virginia Commonwealth), plus 50 more at 1–3 photos. **Enrich (per university —
after the HIGH tier clears):** a full real-named, TITLE-CASED catalog with **field-specific
`description_text` on every program** + the real conferred degree designation (never "{DegreeType} program
in {field}") + PROGRAM-DISTINCT `who_its_for` (never a degree-type template, never `= None`) + real
departments + published tuition (non-resident scalar for publics) + `cip_code` · a working feed · a
≥4-photo verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the
higher tiers clear.

---

# CLEAN (structure + descriptions(pattern + NON-EMPTINESS) + names(fabrication) + tuition-value-copy-down + exact-dup + photos + deploy; no action) — verified LIVE run 91
- **Gold (description 0-control):** MIT (n=65, real "Science, Technology, and Society" major; but
  TYPE-GAMED `who_its_for` 0.25 + null cert tiers + grad rows at its own undergrad sticker + null
  `cip_code` — MIT is a description control ONLY, not a tuition / `cip_code` / who-distinctness reference).
- **CLEARED since run 90 (enricher worked the backlog):** **Northwestern** [#1195] cip+distinct-who ·
  **Duke** [#1197] cip+distinct-who · **CMU** [#1198/#1199] cip+distinct-who(+CIP fix) · **JHU** [#1200]
  cip+distinct-who. cip-null 11→7, who-0% 12→8, who-field-specific 15→19.
- **`cip_code`-COMPLETE (the model for entry #1):** Caltech · Princeton · Notre Dame · Chicago · Columbia ·
  Dartmouth · Georgia Tech · UT-Austin · Berkeley · UCLA · UCSD · UNC · UW-Seattle · Penn · Vanderbilt ·
  Georgetown · UVA · WashU · UC-Davis · UC-Irvine · Brown · Emory · Purdue · Michigan · Rice · UF · UIUC ·
  UW-Madison · **CMU · Duke · JHU · Northwestern** (100% in-sample).
- **`who_its_for` FIELD-SPECIFIC (the distinctness model for entry #4b — distinct/total ≈1.0):** Brown ·
  Emory · Purdue · Dartmouth · Georgetown · Vanderbilt · UC-Davis · UCLA · UC-Irvine · UNC · UVA · WashU ·
  Rice · UIUC · UW-Madison · **CMU · Duke · JHU · Northwestern**.
- **PUBLIC non-resident scalar CORRECT (14):** Georgia Tech · UT-Austin · Berkeley · UCLA · UC-Davis ·
  UC-Irvine · UNC · UVA · UW-Seattle · Michigan · Purdue · UF · UIUC · UW-Madison (bachelor `tuition` = oos,
  verified live).
- **EXACT-DUPLICATE / NAME-FABRICATION / EMPTY-DESC / TUITION-COPY-DOWN / PHOTO classes CLEAN fleet-wide:**
  0 raw `(program_name, degree_type)` repeats, 0 fabricated names, 0 empty descriptions (0/8,024), no
  undergrad-sticker copy-down (BU $69,870 = VERIFIED BU Law rate; the single-value prof tiers
  Brown/Dartmouth/JHU/Notre Dame DISTINCT-and-higher), every program-bearing node ≥4 campus photos.
- **DEPLOY PIPELINE HEALTHY:** single head, migrations applying in prod. Every program-bearing node has a
  live feed EXCEPT UC-Irvine (ops, entry #7).
