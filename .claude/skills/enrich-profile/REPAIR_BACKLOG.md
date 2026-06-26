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
`who_its_for` — shipped 0% catalog-wide / type-GAMED to a degree-type template, a sentence-CASED /
mis-cased name on an otherwise-real catalog, institution-level seed below gold, or dead feed on an
otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured THIS run by a direct
full-fleet crawl: all **300 LIVE institutions** fetched (campus-photo gallery length + posts-feed
count — **feed count read as a LIST, not `.total`**, the run-89 false-negative fixed) + the **40
program-bearing catalogs fully paginated (8,024 programs)** and run through a per-catalog
description-NON-EMPTINESS scan, an exact-duplicate `(program_name, degree_type)` scan, a
name-realness scan (CIP-rollup TITLE / "…and Related Sciences/Services" / ", General/Other" /
`(CIP NN.NN)` / possessive "Bachelor's in" / bare-abbreviation tells), a **NEW name-CASING scan
(mid-name lowercase content word)**, a per-`degree_type` tuition COVERAGE measure, and a
grad/prof-vs-undergrad tuition-VALUE copy-down scan. Over 20 program DETAILS/catalog
(`GET /programs/{id}`) I probed `cip_code` / `who_its_for` (coverage AND distinctness) /
`external_reviews` coverage and the public bachelor `tuition`-scalar-vs-`cost_data.breakdown`
resident/non-resident axis. The cip-null / `who_its_for = None` / `backfill_program_preferences`
greps were read via `git` over `origin/main`. Gold MIT (n=65) is the description 0-control but is
NOT a tuition, `cip_code`, OR `who_its_for`-distinctness control (it ships null cert tiers, grad
rows at its own undergrad sticker, null `cip_code`, AND a TYPE-GAMED `who_its_for` of 4/20).

_Last graded: 2026-06-26 (grader **run 90**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — a genuinely NEW gap-class: **program-name
CASING.** UT-Austin ships **70 of 338** rows SENTENCE-CASED ("Bachelor of Arts in American studies",
"… in Art history", "… in Asian studies") — verified-REAL degrees in the wrong CASE, which evades every
prior name gate because those all key on FABRICATION tells (CIP rollups, abbreviations, the possessive
mint), none on casing. The new rule requires the institution's PUBLISHED title-case, with carve-outs that
PRESERVE legitimate lowercase (parentheticals, post-positives, acronyms). **🟢 BIG PROGRESS since run 89 —
the enricher cleared backlog entries via PRs #1188 (UF) · #1190/#1191 (UIUC) · #1192 (Rice) · #1193/#1194
(UW-Madison):** cip-null 15→11, who-0% 16→12, who-field-specific 12→15, public resident-scalar mis-signal
4→**1 (UCSD only)**. Structure / descriptions(pattern + NON-EMPTINESS) / NAMES(fabrication) / exact-dups /
tuition-copy-down remain gold-clean fleet-wide (0/8,024 empty, 0 dups, 0 fabricated names, 0 copy-downs).
**🔴 UC-Irvine dead feed PERSISTS** — posts=0 a week+ on (run-89 "no dead feeds" was a crawler
`.get("total")`-on-a-list false negative; corrected this run) while EVERY other program-bearing node
ingests → an INGEST/OPS failure (FLAG #9), not a data or rule defect. **🆕 🟡 `who_its_for` TYPE-GAMING
recurred on fresh UF** (#1188, merged before the run-89 distinctness rule; post-rule UIUC/Rice/UW-Madison
all did it field-specific, so the rule WORKS). NO critical entries remain. See CHANGELOG run 90._

## Fleet at a glance (run 90, live `api.unipaith.co/api/v1` + `origin/main`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (8,024 total); 260 are bare institution-level
  stubs** (0 programs, dead feed, **33 with ZERO campus photo**, 50 more at 1–3 photos, **217 at 4+**).
  Seeding is **external**; the routine ENRICHES + REPAIRS only.
- **🟢 NO CRITICAL DEFECTS.** 0 empty/whitespace `description_text` across all 8,024 programs; 0
  exact-duplicate `(program_name, degree_type)` rows on all 40 catalogs; the FABRICATION name-realness scan
  returns ZERO CIP-rollup / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other" /
  possessive "Bachelor's in" / bare-abbreviation names (every multi-clause "comma-and" hit is a VERIFIED
  real interdisciplinary major — the documented run-77 false-positive); 0 tuition copy-downs (the 4
  single-value professional tiers — Brown/Dartmouth/JHU/Notre Dame — carry a DISTINCT, HIGHER rate than the
  undergrad sticker). Deploy pipeline healthy (single head, migrations applying in prod).
- **🆕 🟡 program-name CASING (NEW class — 1 catalog, 70 rows):** UT-Austin ships **70/338** SENTENCE-CASED
  field names ("Bachelor of Arts in American studies", "… in Art history", "… in Asian studies", "… in
  Classical languages", "… in Behavioral and social data science") — verified-real degrees, mis-CASED, the
  form the student reads on the card + detail page. Every other catalog title-cases (gold MIT 0/65). Entry
  #4. Rule ADDED run 90 → name-casing gate; FLAG #3 (extend the name-realness metric to casing).
- **🔴 matcher-core `cip_code` STARVATION (11 mature catalogs null + MIT control, was 15):** `cip_code`
  (the CIP join key to `ref_majors` + the field-66 vocabulary) is NULL on **BU · CMU · Cornell · Duke ·
  Harvard · JHU · NYU · Northwestern · Stanford · USC · Yale** (+ MIT control) — so the matcher scores those
  ~3,900 programs field-blind. **CLEARED since run 89: Rice · UF · UIUC · UW-Madison** (100% in-sample). The
  12 modules missing a `p.cip_code` assignment EXACTLY match these 11 + MIT (grep-confirmed) — one
  assignment, no research, highest matcher leverage. Entry #1. Rule EXISTS (run 82) → COMPLIANCE GAP,
  queued; durable enforcement is FLAG #2.
- **🔴 PUBLIC resident-tuition scalar MIS-SIGNAL (1 public still in-state, was 4):** the CPEF budget feature
  reads the FLAT `program.tuition` scalar, NOT a residency-aware estimator. Only **UCSD** still ships the
  IN-STATE rate (scalar **16,758** while `cost_data.breakdown.tuition_out_of_state` = **50,958**). **CLEARED
  since run 89: UF (28,659=oos) · UIUC (38,398=oos) · UW-Madison/Wisconsin (47,410=oos).** 14 publics now
  correct. Entry #2. Rule EXISTS (run 83) → COMPLIANCE GAP; durable fix is FLAG #6.
- **🔴 master's / professional-tier tuition residual:** bachelor's ~100% everywhere, but the MASTER'S
  (and some PROFESSIONAL) tier ships a material null fraction (matcher scores those programs' budget BLIND).
  Worst — **Georgetown master's 73/79 + prof 7/17** · **UW-Seattle** 14/152 + prof 1/7 · **USC** 12/261 ·
  **UC-Irvine** 11/21 + prof 1/4 · **BU** 7/167 + prof 5/25 · **UT-Austin** 7/128 + prof 3/5 · **UVA** 7/15
  · **Cornell** 6/85 + prof 1/5 · **WashU** 6/10 · **Penn** 6/63 · **UCSD** 5/59 · **NYU** 5/232 · **Harvard**
  5/90 · **Yale** 4/38 · **UC-Davis** 4/19 · **Dartmouth** 3/16 · small (Vanderbilt 1/25, Michigan 1/99,
  UCLA 1/145). **Professional-tier-only nulls (FAIL — professional publishes its own rate): Stanford prof
  2/2, Columbia prof 2/8.** **PhD / certificate nulls EXCLUDED** (funded research doctorates / per-credit
  certs → legitimate omit-with-reason). Entry #3. Rule EXISTS (run 74) → COMPLIANCE GAP.
- **🟡 `who_its_for` 0% (non-null) on 12 catalogs (was 16):** BU · CMU · Duke · Georgia Tech · JHU · NYU ·
  Northwestern · USC · UT-Austin · UCSD · Notre Dame · UW-Seattle. 7 modules still carry the literal
  `p.who_its_for = None` (duke · georgia_tech · nyu · ucla · usc · ut_austin · uw). ⚠️ **UCLA latent-masked:**
  reads who 100% / distinct ≈1.0 LIVE only because the #1181 sibling overwrites the hard-null —
  `ucla_profile.py` STILL carries `= None`, a re-apply regression waiting to fire. Entry #4a. Rule EXISTS
  (run 84/86) → COMPLIANCE GAP.
- **🟡 `who_its_for` TYPE-GAMING (13 catalogs 100%-filled but program-indistinct, was 12):** a DISTINCTNESS
  pass (distinct strings / 20 sampled) shows ~13 catalogs collapse `who_its_for` to ~one template per
  degree-type — **Stanford 1/20 · Berkeley 1/20** · Caltech 2/18 · Cornell/Chicago/Penn 2/20 ·
  Columbia/Princeton/Yale 3/20 · Harvard/**MIT**/Michigan/**Florida** 4/20 — passing the non-null coverage
  gate while a CS PhD and a Public-Policy PhD read identically. **🆕 Florida (#1188)** gamed it; but UF
  merged BEFORE the run-89 distinctness rule, and every POST-rule repair (UIUC/Rice/UW-Madison) did it
  field-specific (≈1.0) — so the rule WORKS, this is a residual, not a regression of the rule. Entry #4b.
  Rule EXISTS (run 89) → COMPLIANCE GAP; FLAG #4.
- **🟢 `who_its_for` FIELD-SPECIFIC (distinct/total ≈1.0) on 15 (was 12):** Brown · Emory · Purdue ·
  Dartmouth · Georgetown · Vanderbilt · UC-Davis · UCLA · UC-Irvine · UNC · UVA · WashU · **Rice · UIUC ·
  UW-Madison** (the distinctness model for entry #4b).
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):**
  sampled 20/catalog — richest Princeton 11/20 · Caltech/MIT 10/20; thinnest **0/20 on Dartmouth ·
  Georgetown · NYU · UC-Davis · UCLA · UIUC · Notre Dame**, 1/20 on GT · Stanford · UT-Austin · UC-Irvine ·
  UF. Coverage-gated (even gold MIT is 10/20) → a depth-pass priority on structurally-clean catalogs, NOT a
  fabrication mandate. Entry #5.
- **🔴 UC-Irvine DEAD FEED — PERSISTS (ingest/ops, not data):** UC-Irvine (160 programs, 5 photos) reads
  posts=0 a week+ after going live, the ONLY program-bearing node with a dead feed (every other has
  183–1,103+ posts on page 1). `uci_profile.py` sets `content_sources` (news_rss `https://news.uci.edu/feed/`
  at institution/school/program level — `git`-confirmed) AND that RSS source is LIVE. The enricher COMPLIED
  with miss #1; the background ingest pipeline simply has not populated UC-Irvine. (The run-89 backlog's "no
  dead feeds" was a crawler bug — the posts endpoint returns a LIST, and `.get("total")` on it threw and the
  node was dropped from the dead-feed filter; corrected this run.) NOT a rule/data defect → FLAG #9 (ops).
  Entry #6.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The "deploy-safe" self-skipping data migration remains a latent cause of stranded enrichments.**
   A heavy per-program data migration wraps `<uni>_profile.apply(session)` in a `lock_timeout`-bounded
   SAVEPOINT, SKIPS the apply rather than hanging boot, yet records as applied so the chain advances —
   Deploy goes GREEN while the data may never run. No stranded enrichment this run, but the mechanism is
   non-deterministic. Durable fix: a prod execution path that ACTUALLY RUNS (one-off job / management
   command, or a migration that retries/blocks and FAILS the deploy if it cannot). (carried.)
2. **`cip_code` is populated on only ~28 of 40 modules — NO enforced coverage gate.** Durable fix = a
   `cip_code` coverage metric in the profile test (~100% non-null per mature catalog). (carried.)
3. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES, is BLIND to EMPTY
   descriptions, AND blind to name CASING.** Fabrication + empties clean this run, but UT-Austin's 70
   sentence-cased names shipped undetected. Durable fix = a name-realness metric that scans NAMES for both
   fabrication tells AND a mid-name lowercase content word (casing) + a `description_text` NON-EMPTINESS
   assertion (~100% non-empty per catalog). (carried + extended to casing.)
4. **No `who_its_for` distinctness / hard-null regression gate.** The existing/proposed coverage metric
   asserts NON-NULL only — which TYPE-GAMING passes (every program one template). The metric must assert
   DISTINCTNESS (distinct `who_its_for` strings / programs ≈ 1.0, FAIL well under ~0.5) AND a lint/grep gate
   must FAIL on a literal `p.<coverable_field> = None` in an `apply()` loop (incl. `ucla_profile.py`, whose
   hard-null is sibling-masked). App/test code. (carried.)
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
   source is live, but `/institutions/{uci}/posts` has read 0 for a week+ while every other enriched node
   ingests. The enricher cannot fix an async ingest job from a profile module. Durable fix: a
   re-ingest / backfill trigger for a node whose `content_sources` is set but whose feed stays empty N
   days post-ship, + an alert when an enriched node's post count is 0. Ops/app code. (carried.)

---

# HIGH — matcher-core `cip_code` STARVATION (clear FIRST — highest matcher leverage, one assignment)

## 1. The 11 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 — 2026-06-26
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the
field-66 vocabulary. NULL on **BU · CMU · Cornell · Duke · Harvard · JHU · NYU · Northwestern · Stanford ·
USC · Yale** (+ MIT control) — ~3,900 programs scored field-blind. The 12 modules missing a `p.cip_code`
assignment EXACTLY match these 11 + MIT (`grep -L '\.cip_code'`: bu · carnegie_mellon · cornell · duke ·
harvard · jhu · mit · northwestern · nyu · stanford · usc · yale). **Fix (one fleet sweep, or per catalog):**
stamp `p.cip_code = spec.get("cip")` (the IPEDS CIP already used for the breadth cross-check), exactly as the
fillers do — never a guess, omit-with-reason only for a genuinely uncodeable program. Re-measure LIVE per
catalog to ~100%. **CLEARED since run 89: Rice · UF · UIUC · UW-Madison.** Rule EXISTS (run 82) →
compliance/repair. Durable enforcement = FLAG #2.

---

# HIGH — PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 2. UCSD — the last public catalog shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 — 2026-06-26
The CPEF budget feature reads the FLAT `program.tuition` scalar, NOT a residency-aware estimator. Only
**UCSD** is still in-state: scalar **16,758** while `cost_data.breakdown.tuition_out_of_state` = **50,958**
(in-state and out-of-state both honest in the breakdown; only the exposed scalar is wrong). **CLEARED since
run 89: UF (28,659) · UIUC (38,398) · UW-Madison/Wisconsin (47,410).** 14 publics now correct (GT · UT-Austin
· Berkeley · UCLA · UC-Davis · UC-Irvine · UNC · UVA · UW-Seattle · Michigan · Purdue · UF · UIUC · UW-Madison).
**Fix:** stamp the NON-RESIDENT sticker (`breakdown.tuition_out_of_state` = 50,958) into the scalar `tuition`,
keeping BOTH rates in the breakdown. Re-measure LIVE. See FLAG #6 — durable fix is residency-aware matching.
Rule EXISTS (run 83) → compliance/repair.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 3. Georgetown · UW-Seattle · USC + residuals — partial master's/professional tuition null — severity: high — first seen run 74 — 2026-06-26
Structurally + description clean catalogs whose bachelor's tier is ~100% but whose MASTER'S (and some
PROFESSIONAL) tier ships a material null fraction (the matcher scores those graduate programs' budget-fit
BLIND). Worst by master's null count (live run 90): **Georgetown master's 73/79 + prof 7/17** · **UW-Seattle**
14/152 + prof 1/7 · **USC** 12/261 · **UC-Irvine** 11/21 + prof 1/4 · **BU** 7/167 + prof 5/25 · **UT-Austin**
7/128 + prof 3/5 · **UVA** 7/15 · **Cornell** 6/85 + prof 1/5 · **WashU** 6/10 · **Penn** 6/63 · **UCSD**
5/59 · **NYU** 5/232 · **Harvard** 5/90 · **Yale** 4/38 · **UC-Davis** 4/19 · **Dartmouth** 3/16 · small
(Vanderbilt 1/25, Michigan 1/99, UCLA 1/145). **Professional-tier-only nulls (these publish a rate → FAIL):
Stanford prof 2/2, Columbia prof 2/8.** **Fix (per university):** group coverage by `degree_type`; stamp the
published per-program / per-credit rate for the null MASTER'S / PROFESSIONAL tier (these publish a rate,
rarely funded). For a PhD or per-credit certificate, record `tuition` in `_standard.omitted` with a reason —
never a silent blanket null, and never the undergrad sticker copied onto a professional school that bills its
own higher rate (BU's $69,870 = VERIFIED BU Law tuition+fees, MD/DMD distinctly rated — that case is RESOLVED
clean; the 4 single-value prof tiers Brown/Dartmouth/JHU/Notre Dame are DISTINCT-and-higher, not copy-downs).
**PhD / certificate nulls EXCLUDED** (largely funded / per-credit → legitimate omit-with-reason). Re-measure
LIVE per tier.

---

# MEDIUM — `who_its_for` (0% + type-gamed) · name casing · reviews depth · UC-Irvine feed · bulk seeds

## 4. `who_its_for` — 12 catalogs 0% (un-done) AND 13 catalogs TYPE-GAMED (coverage-passing, indistinct) — severity: medium — first seen run 84 (0%) / run 89 (type-gaming) — 2026-06-26
`who_its_for` ("Who it's for", a manifest field) is derivable for EVERY program from its own published
audience/fit material, so both failure modes below are un-done depth, not honest omission.
**(a) 0% (non-null) on 12 catalogs** — BU · CMU · Duke · Georgia Tech · JHU · NYU · Northwestern · USC ·
UT-Austin · UCSD · Notre Dame · UW-Seattle. ROOT CAUSE: 7 modules carry the literal `p.who_its_for = None`
(duke · georgia_tech · nyu · ucla · usc · ut_austin · uw); the rest never assign it. ⚠️ **UCLA latent-masked**
— reads 100% / distinct ≈1.0 LIVE only via the #1181 sibling overwrite; `ucla_profile.py` STILL carries
`= None`, so remove the hard-null from the base module.
**(b) TYPE-GAMED on 13 catalogs (100% non-null but ONE degree-type template per tier)** — Stanford 1/20 ·
Berkeley 1/20 · Caltech 2/18 · Cornell/Chicago/Penn 2/20 · Columbia/Princeton/Yale 3/20 · Harvard/**MIT**/
Michigan/**Florida** 4/20 (distinct strings / 20 sampled). Every PhD reads "a funded <school> doctorate",
every bachelor's "a top public-research undergraduate education" — passing the coverage gate while a CS PhD
and a Public-Policy PhD read identically. **Florida (#1188)** gamed it, but UF merged BEFORE the run-89
distinctness rule; every POST-rule repair (UIUC/Rice/UW-Madison) is field-specific (≈1.0).
**Fix (per catalog, in the SAME pass as cip/tuition):** build a `_WHO_BY_SLUG` dict of field-specific 1–2
sentence statements (subject, methods, who it fits, next step) — the bar Brown/Emory/Purdue/Dartmouth/
Georgetown/Vanderbilt/UC-Davis/UCLA/UC-Irvine/UNC/UVA/WashU/Rice/UIUC/UW-Madison already meet (distinct/total
≈1.0). The `_WHO_BY_TYPE` fallback is a narrow last resort, never the primary fill; never `= None`.
Re-measure LIVE for BOTH coverage (~100%) AND distinctness (≈1.0). Rule EXISTS run 84/86 (0%) + run 89
(distinctness) → compliance/repair. Durable enforcement = FLAG #4.

## 5. UT-Austin — 70 SENTENCE-CASED program names (NEW name-casing class) — severity: medium — first seen run 90 — 2026-06-26
UT-Austin ships **70 of 338** rows with the field part SENTENCE-CASED — only the first word capitalized, the
rest lowercased: "Bachelor of Arts in American studies", "… in Art history", "… in Asian studies", "… in
Asian cultures and languages", "… in Classical languages", "… in Behavioral and social data science", "… in
Race, indigeneity, and migration", "… in Russian, East European, and Eurasian studies". These are
verified-REAL degrees in the WRONG CASE — the form the student reads on the explore card + detail page — and
they EVADE every prior name gate (all key on fabrication tells, none on casing). Every other catalog
title-cases its field names (gold MIT 0/65). **Fix (UT-Austin):** re-case every `program_name` (and any
matching `department`) to UT-Austin's PUBLISHED title-case degree name ("Bachelor of Arts in American
Studies", "… in Art History", "… in Asian Studies", "… in Classical Languages"), PRESERVING legitimate
lowercase (parenthetical qualifiers, post-positives, acronyms) — never invent or change a word, only its
capitalization. The defect is baked into `ut_austin_profile.py` (the `program_name` strings are stored
sentence-cased verbatim). Re-measure LIVE: 0 mid-name lowercase content words. Rule ADDED run 90 →
compliance after the rule lands. Durable enforcement = FLAG #3 (extend the name-realness metric to casing).

## 6. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 — 2026-06-26
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass.
Sampled 20/catalog: 0/20 on Dartmouth · Georgetown · NYU · UC-Davis · UCLA · UIUC · Notre Dame; 1/20 on GT ·
Stanford · UT-Austin · UC-Irvine · UF; richest Princeton 11/20 · Caltech/MIT 10/20. **Calibrate — reviews are
coverage-gated; do NOT fabricate (even gold MIT is 10/20).** **Enrich:** on a structurally-clean catalog, run
the reviews depth pass over programs WITH real third-party coverage (Poets&Quants / U.S. News / GradReports /
program outcomes reports) — program-specific summary + themes + resolvable sources, no synthesized-from-metadata
reviews (miss #8) — and record `external_reviews` in `_standard.omitted` with a reason where a program
genuinely has no coverage.

## 7. UC-Irvine dead feed — PERSISTS (ingest/ops) — severity: medium — first seen run 87 (watch) / escalated run 89 / persists run 90 — 2026-06-26
UC-Irvine (160 programs) is the ONLY program-bearing node reading posts=0, a week+ after going live, while
every other enriched node ingests (183–1,103+ posts on page 1). `uci_profile.py` sets `content_sources`
(news_rss `https://news.uci.edu/feed/`, `git`-confirmed) AND that feed is LIVE. The enricher COMPLIED — this
is an INGEST/OPS failure, not a data or rule defect. **No enricher action** (omitting or re-stamping
content_sources would not help); → FLAG #9 for an ops re-ingest trigger. The enricher may note it in
`_standard.omitted` with the ops reason but must NOT fabricate posts.

## 8. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first: Air Force Institute
of Technology · Arizona State (Campus + Digital) · Azusa Pacific · Colorado State-Fort Collins · James
Madison · Keiser-Ft Lauderdale · Loyola Marymount · Loyola-Chicago · Miami-Oxford · Michigan Tech ·
Montclair State · Northcentral · Oakland · Oregon State · SUNY-ESF · Sacred Heart · Stephen F Austin ·
Texas A&M (Commerce + Corpus Christi) · Thomas Jefferson · Univ Ana G Mendez-Gurabo · UAB · Dayton ·
Houston · Kentucky · Louisville · Maryland-Baltimore County · Missouri-St Louis · Nebraska-Lincoln ·
Oklahoma-Norman · Utah · Virginia Commonwealth), plus 50 more at 1–3 photos. **Enrich (per university —
after the HIGH tier clears):** a full real-named, TITLE-CASED catalog with **field-specific `description_text`
on every program** + PROGRAM-DISTINCT `who_its_for` (never a degree-type template, never `= None`) + real
departments + published tuition (non-resident scalar for publics) + `cip_code` · a working feed · a ≥4-photo
verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the higher tiers clear.

---

# CLEAN (structure + descriptions(pattern + NON-EMPTINESS) + names(fabrication) + tuition-value-copy-down + exact-dup + deploy; no action) — verified LIVE run 90
- **Gold (description 0-control):** MIT (n=65, real "Science, Technology, and Society" major; but TYPE-GAMED
  `who_its_for` 4/20 + null cert tiers + grad rows at its own undergrad sticker + null `cip_code` — MIT is a
  description control ONLY, not a tuition / `cip_code` / who-distinctness reference).
- **CLEARED since run 89 (enricher worked the backlog):** **UF** [#1188] cip+oos-tuition+who(but type-gamed,
  pre-rule) · **UIUC** [#1190/#1191] cip+oos-tuition+distinct-who · **Rice** [#1192] cip+distinct-who ·
  **UW-Madison** [#1193/#1194] cip+oos-tuition+distinct-who. cip-null 15→11, who-0% 16→12, public-scalar 4→1.
- **`cip_code`-COMPLETE (the model for entry #1):** Caltech · Princeton · Notre Dame · Chicago · Columbia ·
  Dartmouth · Georgia Tech · UT-Austin · Berkeley · UCLA · UCSD · UNC · UW-Seattle · Penn · Vanderbilt ·
  Georgetown · UVA · WashU · UC-Davis · UC-Irvine · Brown · Emory · Purdue · Michigan · **Rice · UF · UIUC ·
  UW-Madison** (100% in-sample).
- **`who_its_for` FIELD-SPECIFIC (the distinctness model for entry #4b — distinct/total ≈1.0):** Brown ·
  Emory · Purdue · Dartmouth · Georgetown · Vanderbilt · UC-Davis · UCLA · UC-Irvine · UNC · UVA · WashU ·
  **Rice · UIUC · UW-Madison**.
- **PUBLIC non-resident scalar CORRECT (14):** Georgia Tech · UT-Austin · Berkeley · UCLA · UC-Davis ·
  UC-Irvine · UNC · UVA · UW-Seattle · Michigan · Purdue · **UF · UIUC · UW-Madison** (bachelor `tuition` = oos).
- **EXACT-DUPLICATE / NAME-FABRICATION / EMPTY-DESC / TUITION-COPY-DOWN classes CLEAN fleet-wide:** 0 raw
  `(program_name, degree_type)` repeats, 0 fabricated names, 0 empty descriptions (0/8,024), no
  undergrad-sticker copy-down (BU $69,870 = VERIFIED BU Law rate; USC $73,260 flat — professional tier
  distinct; Brown/Dartmouth/JHU/Notre Dame single-value prof tiers DISTINCT-and-higher than undergrad).
- **DEPLOY PIPELINE HEALTHY:** single head, migrations applying in prod. Every program-bearing node has a
  live feed EXCEPT UC-Irvine (ops, entry #7).
