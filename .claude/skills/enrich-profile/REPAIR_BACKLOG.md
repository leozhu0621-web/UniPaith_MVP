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
`who_its_for` — shipped 0% catalog-wide / type-GAMED to a degree-type template / REGRESSED to 0%,
institution-level seed below gold, or dead feed on an otherwise-enriched node).

Evidence is from the live API (`api.unipaith.co/api/v1`), measured THIS run by a direct
full-fleet crawl: all **300 LIVE institutions** fetched (campus-photo gallery length + posts-feed
count, threaded) + the **40 program-bearing catalogs fully paginated (8,024 programs)** and run
through a per-catalog description-NON-EMPTINESS scan, an exact-duplicate `(program_name,
degree_type)` scan, a name-realness scan (CIP-rollup TITLE / "…and Related Sciences/Services" /
", General/Other" / `(CIP NN.NN)` / possessive "Bachelor's in" / bare-abbreviation tells), a
per-`degree_type` tuition COVERAGE measure, and a grad==undergrad tuition-VALUE copy-down scan.
Over 12 program DETAILS/catalog (`GET /programs/{id}`) I probed `cip_code` / `who_its_for` /
`external_reviews` coverage, the public bachelor `tuition`-scalar-vs-`cost_data.breakdown`
resident/non-resident axis, AND — **new this run** — a `who_its_for` DISTINCTNESS measure (distinct
strings / sampled programs). The `who_its_for = None` hard-null grep, the missing-`.cip_code` grep,
and the fresh-migration `backfill_program_preferences` / `content_sources` calls were read via
`git` over `origin/main`. Gold MIT (n=65) is the description 0-control but is NOT a tuition,
`cip_code`, OR `who_its_for`-distinctness control (it ships null cert/PhD tiers, grad rows at its own
undergrad sticker, null `cip_code`, AND a TYPE-GAMED `who_its_for` of distinct-ratio 5/20).

_Last graded: 2026-06-26 (grader **run 89**). **FULL-FLEET sweep: all 300 LIVE institutions + all 40
catalogs re-measured via the live API.** **1 rule change** — a genuinely NEW gap-class surfaced by a
who_its_for DISTINCTNESS pass that prior runs (which measured only non-null coverage) missed:
**`who_its_for` TYPE-GAMING** — ~12 catalogs ship the field 100%-filled but collapsed to ONE
degree-type template per tier (every PhD reads "a funded <school> doctorate", every bachelor's "a top
public-research undergraduate education"), passing the coverage gate while telling a student nothing
program-distinct. The rule now requires `who_its_for` be PROGRAM-DISTINCT (distinct/total ≈1.0), not
just non-null, and reclassifies the old "gold-complete" exemplars (MIT/Princeton/.../Berkeley) as a
COVERAGE reference only. **🟢 BIG PROGRESS since run 88 — the enricher cleared backlog entries via
PRs #1182 (Purdue) · #1184 (Emory) · #1185 (Brown) · #1186/#1187 (Michigan):** all 4 gained
`cip_code` (cip-null 19→16) + `who_its_for` (who-0% 20→16); Purdue & Michigan gained the
non-resident tuition scalar (public-scalar mis-signal 6→4). Structure/descriptions(pattern +
NON-EMPTINESS)/NAMES/exact-dups/tuition-copy-down remain gold-clean fleet-wide (0/8,024 empty, 0 dups,
0 fabricated names). The run-88 BU-Law-JD spot-check is **RESOLVED CLEAN** — $69,870 is the VERIFIED
BU Law published tuition+fees, not a copy-down. **🔴 UC-Irvine dead feed ESCALATED** from run-88
watch: `content_sources` set + the RSS source live (HTTP 200, 421 KB), yet posts=0 a week+ on while
EVERY other program-bearing node has a live feed → an INGEST/OPS failure (FLAG #9), not a data or
rule defect. NO critical entries remain. See CHANGELOG run 89._

## Fleet at a glance (run 89, live `api.unipaith.co/api/v1` + `origin/main`)

- **Fleet = 300 institutions LIVE.** **40 carry programs (8,024 total, up from 7,639); 260 are bare
  institution-level stubs** (0 programs, dead feed, **33 with ZERO campus photo**, 50 more at 1–3
  photos, **217 at 4+** — up from 177). Seeding is **external**; the routine ENRICHES + REPAIRS only.
- **🟢 NO CRITICAL DEFECTS.** 0 empty/whitespace `description_text` across all 8,024 programs; 0
  exact-duplicate `(program_name, degree_type)` rows on all 40 catalogs; name-realness scan returns
  ZERO CIP-rollup / `(CIP NN.NN)` / "…and Related Sciences/Services" / ", General/Other" / possessive
  "Bachelor's in" / bare-abbreviation names (every multi-clause "comma-and" hit is a VERIFIED real
  interdisciplinary major — the documented run-77 false-positive). Deploy pipeline healthy (single
  head, migrations applying in prod). Every program-bearing node has a live feed EXCEPT UC-Irvine.
- **🆕 🟡 `who_its_for` TYPE-GAMING (NEW class — 12 catalogs 100%-filled but program-indistinct):**
  a DISTINCTNESS pass (distinct strings / 20 sampled) shows ~12 catalogs collapse `who_its_for` to
  ~one template per degree-type — **Berkeley 1/20 (0.05)** · Columbia/Cornell/Princeton/Stanford/Yale
  2/20 · Caltech/Chicago/Penn/**Michigan** 3/20 · Harvard 4/20 · **MIT 5/20** — passing the non-null
  coverage gate while a CS PhD and a Public-Policy PhD read identically. **Field-specific (≈1.0,
  distinct per program) on 12:** Brown · Emory · Purdue · Dartmouth · Georgetown · Vanderbilt ·
  UC-Davis · UCLA · UC-Irvine · UNC · UVA · WashU. The FRESH Michigan repair (#1186/#1187) gamed it,
  so the class is actively recurring. Entry #4b. Rule ADDED run 89 → enforce DISTINCTNESS; FLAG #4.
- **🔴 matcher-core `cip_code` STARVATION (15 mature catalogs null + MIT control, was 19):** `cip_code`
  (the CIP join key to `ref_majors` + the field-66 vocabulary) is NULL on **Brown[FIXED]→ no; now
  null on:** BU · CMU · Cornell · Duke · Harvard · JHU · NYU · Northwestern · Rice · Stanford · UF ·
  UIUC · USC · UW-Madison · Yale (+ MIT control) — so the matcher scores those ~4,300 programs
  field-blind. **CLEARED since run 88: Brown · Emory · Purdue · Michigan** (now 100% in-sample). The
  16 modules missing a `p.cip_code` assignment EXACTLY match the 16 cip-null catalogs (grep-confirmed)
  — one assignment, no research, highest matcher leverage. Entry #1. Rule EXISTS (run 82) → COMPLIANCE
  GAP, queued; durable enforcement is FLAG #2.
- **🔴 PUBLIC resident-tuition scalar MIS-SIGNAL (4 publics still in-state, was 6):** the CPEF budget
  feature reads the FLAT `program.tuition` scalar, NOT a residency-aware estimator. **STILL ship the
  IN-STATE rate** while `cost_data.breakdown` carries the higher out-of-state: **UCSD 16,758 (oos
  50,958)** · **Florida 6,381 (28,659)** · **Wisconsin 12,186 (44,210)** · **UIUC 12,992** (breakdown
  now carries `tuition_and_fees_out_of_state_range` [38,398–46,498] — a published number to stamp, no
  research). **CLEARED since run 88: Michigan (now 63,480=oos) · Purdue (28,794=oos).** 11 publics now
  correct. Entry #2. Rule EXISTS (run 83) → COMPLIANCE GAP; durable fix is FLAG #6.
- **🔴 master's / professional-tier tuition residual:** bachelor's ~100% everywhere, but the MASTER'S
  (and some PROFESSIONAL) tier ships a material null fraction — worst **Georgetown master's 6/79 (73
  null!) + prof 10/17** · **UW-Seattle** 138/152 (14) + prof 6/7 · **USC** 249/261 (12) · **UC-Irvine**
  10/21 (11) + prof 3/4 · **UT-Austin** 121/128 (7) + prof 2/5 · **Yale** 30/38 (8) · **UVA** 8/15 (7)
  · **NYU** 227/232 (5) + prof 4/6 · **Cornell** 79/85 (6) + prof 4/5 · **WashU** 4/10 (6) · **Penn**
  57/63 (6) · **UCSD** 54/59 (5) · **Harvard** 85/90 (5) · **UC-Davis** 15/19 (4) · small (Dartmouth,
  Columbia prof 6/8, Vanderbilt, Notre Dame, UCLA, Michigan). **PhD / certificate nulls EXCLUDED**
  (funded research doctorates / per-credit certs → legitimate omit-with-reason). BU's grad-flat $69,870
  is the VERIFIED BU Law tuition+fees (run-88 spot-check resolved), MD/DMD distinctly rated — no
  copy-down. Entry #3. Rule EXISTS (run 74) → COMPLIANCE GAP.
- **🟡 `who_its_for` 0% (non-null) on 16 catalogs (was 20):** BU · CMU · Duke · Georgia Tech · JHU ·
  NYU · Northwestern · Rice · UT-Austin · UCSD · UF · UIUC · Notre Dame · USC · UW-Seattle · Wisconsin.
  9 modules still carry the literal `p.who_its_for = None` (duke · georgia_tech · nyu · rice · ucla ·
  uiuc · usc · ut_austin · uw); the rest never assign it. ⚠️ **UCLA latent-masked:** reads who 100%
  LIVE only because the #1181 sibling overwrites the hard-null — `ucla_profile.py` STILL carries
  `= None`, a re-apply regression waiting to fire. Entry #4a. Rule EXISTS (run 84/86) → COMPLIANCE GAP.
- **🟢 EXACT-DUPLICATE + NAME-REALNESS + EMPTY-DESC + TUITION-COPY-DOWN clean fleet-wide.** 0 dups, 0
  fabricated names, 0 empty descriptions (0/8,024), no whole-grad-tree undergrad-sticker stamp anywhere
  (BU $69,870 + USC $73,260 grad-flat rows match the VERIFIED-FLAT-RATE signature — professional tier
  carried DISTINCT).
- **🟡 `external_reviews` sparse fleet-wide (DEPTH-pass priority — do NOT pressure fabrication):**
  sampled 12/catalog — richest Princeton 6/12 · Caltech/BU 5–6/12; thinnest **NYU 0/12**, 1/12 on
  Brown · Emory · GT · Northwestern · UF · UIUC. Coverage-gated (even gold MIT is 5/12) → a depth-pass
  priority on structurally-clean catalogs, NOT a fabrication mandate. Entry #5.
- **🔴 UC-Irvine DEAD FEED — ESCALATED (ingest/ops, not data):** UC-Irvine (160 programs, 5 photos)
  reads posts=0 a week+ after going live, the ONLY program-bearing node with a dead feed (every other
  has 10–2,380 posts). `uci_profile.py` sets `content_sources` (news_rss `https://news.uci.edu/feed/`
  at institution/school/program level — `git`-confirmed) AND that RSS source is LIVE (HTTP 200,
  421 KB). The enricher COMPLIED with miss #1; the background ingest pipeline simply has not populated
  UC-Irvine. Run-88 watched it ("escalate if still dead next run") — it is. NOT a rule/data defect →
  FLAG #9 (ops). Entry #6.

⚠️ **FLAG FOR HUMAN (code/workflow, out of grader scope — the grader edits only the 3 skill files):**
1. **The "deploy-safe" self-skipping data migration remains a latent cause of stranded enrichments.**
   A heavy per-program data migration wraps `<uni>_profile.apply(session)` in a `lock_timeout`-bounded
   SAVEPOINT, SKIPS the apply rather than hanging boot, yet records as applied so the chain advances —
   Deploy goes GREEN while the data may never run. No stranded enrichment this run, but the mechanism is
   non-deterministic. Durable fix: a prod execution path that ACTUALLY RUNS (one-off job / management
   command, or a migration that retries/blocks and FAILS the deploy if it cannot). (carried.)
2. **`cip_code` is populated on only ~24 of 40 modules — NO enforced coverage gate.** Durable fix = a
   `cip_code` coverage metric in the profile test (~100% non-null per mature catalog). (carried.)
3. **The enforced anti-stub gate is DESCRIPTION-PATTERN-only — it never scans NAMES and is BLIND to
   EMPTY descriptions.** Clean this run, but a future verbatim CIP-rollup name or empty `description_text`
   would ship undetected. Durable fix = a name-realness metric + a `description_text` NON-EMPTINESS
   assertion (~100% non-empty per catalog). (carried.)
4. **No `who_its_for` distinctness / hard-null regression gate.** The existing/proposed coverage metric
   asserts NON-NULL only — which TYPE-GAMING passes (every program one template). **Sharpened this run:**
   the metric must assert DISTINCTNESS (distinct `who_its_for` strings / programs ≈ 1.0, FAIL well under
   ~0.5) AND a lint/grep gate must FAIL on a literal `p.<coverable_field> = None` in an `apply()` loop
   (incl. `ucla_profile.py`, whose hard-null is sibling-masked). App/test code. (carried + sharpened.)
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
9. **🆕 The background feed-ingest pipeline stranded UC-Irvine.** `content_sources` is set and the RSS
   source is live, but `/institutions/{uci}/posts` has read 0 for a week+ while every other enriched node
   ingests. The enricher cannot fix an async ingest job from a profile module. Durable fix: a
   re-ingest / backfill trigger for a node whose `content_sources` is set but whose feed stays empty N
   days post-ship, + an alert when an enriched node's post count is 0. Ops/app code.

---

# HIGH — matcher-core `cip_code` STARVATION (clear FIRST — highest matcher leverage, one assignment)

## 1. The 15 mature catalogs shipping `cip_code` null — matcher field-signal starved — severity: high — first seen run 82 — 2026-06-26
`cip_code` is the CIP join key the CPEF matcher uses to resolve a program's field to `ref_majors` + the
field-66 vocabulary. NULL on **BU · CMU · Cornell · Duke · Harvard · JHU · NYU · Northwestern · Rice ·
Stanford · UF · UIUC · USC · UW-Madison · Yale** (+ MIT control) — ~4,300 programs scored field-blind.
The 16 modules missing a `p.cip_code` assignment EXACTLY match these 16 catalogs (`grep -L '\.cip_code'`).
**Fix (one fleet sweep, or per catalog):** stamp `p.cip_code = spec.get("cip")` (the IPEDS CIP already
used for the breadth cross-check), exactly as the fillers do — never a guess, omit-with-reason only for a
genuinely uncodeable program. Re-measure LIVE per catalog to ~100%. **CLEARED since run 88: Brown ·
Emory · Purdue · Michigan.** Rule EXISTS (run 82) → compliance/repair. Durable enforcement = FLAG #2.

---

# HIGH — PUBLIC-university resident-tuition scalar mis-signal (matcher budget veto)

## 2. The 4 public catalogs still shipping the IN-STATE rate as the matcher's `tuition` scalar — severity: high — first seen run 83 — 2026-06-26
The CPEF budget feature reads the FLAT `program.tuition` scalar, NOT a residency-aware estimator. STILL
in-state while `cost_data.breakdown` carries the higher non-resident rate:
- **UCSD** 16,758 vs **50,958** · **Florida** 6,381 vs **28,659** · **Wisconsin** 12,186 vs **44,210**.
- **UIUC** 12,992 = in_state; the breakdown now carries `tuition_and_fees_out_of_state_range`
  [38,398–46,498] — stamp the published non-resident figure (no research needed any more).
**CLEARED since run 88: Michigan (now 63,480) · Purdue (28,794).** 11 publics now correct (GT · UT-Austin
· Berkeley · UCLA · UC-Davis · UC-Irvine · UNC · UVA · UW-Seattle · Michigan · Purdue).
**Fix (per public catalog):** stamp the NON-RESIDENT sticker (the value already in
`cost_data.breakdown.tuition_out_of_state` / the oos range) into the scalar `tuition`, keeping BOTH rates
in the breakdown. Re-measure LIVE. See FLAG #6 — durable fix is residency-aware matching. Rule EXISTS
(run 83) → compliance/repair.

---

# HIGH — master's / professional-tier tuition residual (matcher grad-budget signal)

## 3. Georgetown · UW-Seattle · USC + residuals — partial master's/professional tuition null — severity: high — first seen run 74 — 2026-06-26
Structurally + description clean catalogs whose bachelor's tier is ~100% but whose MASTER'S (and some
PROFESSIONAL) tier ships a material null fraction (the matcher scores those graduate programs' budget-fit
BLIND). Worst by master's null count (live run 89): **Georgetown master's 6/79 (73!) + prof 10/17 (7)** ·
**UW-Seattle** 138/152 (14) + prof 6/7 · **USC** 249/261 (12) · **UC-Irvine** 10/21 (11) + prof 3/4 ·
**UT-Austin** 121/128 (7) + prof 2/5 · **Yale** 30/38 (8) · **UVA** 8/15 (7) · **NYU** 227/232 (5) + prof
4/6 · **Cornell** 79/85 (6) + prof 4/5 · **WashU** 4/10 (6) · **Penn** 57/63 (6) · **UCSD** 54/59 (5) ·
**Harvard** 85/90 (5) · **UC-Davis** 15/19 (4) · **Dartmouth** 13/16 (3) · small (Columbia prof 6/8,
Vanderbilt 24/25, Notre Dame 23/24, UCLA 144/145, Michigan 98/99). **Fix (per university):** group
coverage by `degree_type`; stamp the published per-program / per-credit rate for the null MASTER'S /
PROFESSIONAL tier (these publish a rate, rarely funded). For a PhD or per-credit certificate, record
`tuition` in `_standard.omitted` with a reason — never a silent blanket null, and never the undergrad
sticker copied onto a professional school that bills its own higher rate (BU's $69,870 = VERIFIED BU Law
tuition+fees, MD/DMD distinctly rated — that case is RESOLVED clean). **PhD / certificate nulls EXCLUDED**
(largely funded / per-credit → legitimate omit-with-reason). Re-measure LIVE per tier.

---

# MEDIUM — `who_its_for` (0% un-done AND type-gamed) · reviews depth pass · UC-Irvine feed · bulk seeds

## 4. `who_its_for` — 16 catalogs 0% (un-done) AND 12 catalogs TYPE-GAMED (coverage-passing, indistinct) — severity: medium — first seen run 84 (0%) / run 89 (type-gaming) — 2026-06-26
`who_its_for` ("Who it's for", a manifest field) is derivable for EVERY program from its own published
audience/fit material, so both failure modes below are un-done depth, not honest omission.
**(a) 0% (non-null) on 16 catalogs** — BU · CMU · Duke · Georgia Tech · JHU · NYU · Northwestern · Rice ·
UT-Austin · UCSD · UF · UIUC · Notre Dame · USC · UW-Seattle · Wisconsin. ROOT CAUSE: 9 modules carry the
literal `p.who_its_for = None` (duke · georgia_tech · nyu · rice · ucla · uiuc · usc · ut_austin · uw);
the rest never assign it. ⚠️ **UCLA latent-masked** — reads 100% LIVE only via the #1181 sibling overwrite;
`ucla_profile.py` STILL carries `= None`, so remove the hard-null from the base module.
**(b) 🆕 TYPE-GAMED on 12 catalogs (100% non-null but ONE degree-type template per tier)** — Berkeley 1/20
· Columbia/Cornell/Princeton/Stanford/Yale 2/20 · Caltech/Chicago/Penn/**Michigan** 3/20 · Harvard 4/20 ·
**MIT 5/20** (distinct strings / 20 sampled). Every PhD reads "a funded <school> doctorate", every
bachelor's "a top public-research undergraduate education" — passing the coverage gate while a CS PhD and a
Public-Policy PhD read identically. The FRESH Michigan repair (#1186/#1187) shipped it this way.
**Fix (per catalog, in the SAME pass as cip/tuition):** build a `_WHO_BY_SLUG` dict of field-specific 1–2
sentence statements (subject, methods, who it fits, next step) — the bar Brown/Emory/Purdue/Dartmouth/
Georgetown/Vanderbilt/UC-Davis/UCLA/UC-Irvine/UNC/UVA/WashU already meet (distinct/total ≈1.0). The
`_WHO_BY_TYPE` fallback is a narrow last resort, never the primary fill; never `= None`. Re-measure LIVE
for BOTH coverage (~100%) AND distinctness (≈1.0). Rule EXISTS run 84/86 (0%) + ADDED run 89 (distinctness)
→ compliance/repair. Durable enforcement = FLAG #4.

## 5. `external_reviews` depth pass on the (structurally-clean) mature catalogs — severity: medium — first seen run 65 — 2026-06-26
Structure is clean fleet-wide, so the miss-#8 STRUCTURE-BEFORE-DEPTH order unblocks the reviews depth pass.
Sampled 12/catalog: 0/12 on NYU; 1/12 on Brown · Emory · Georgia Tech · Northwestern · UF · UIUC; richest
Princeton 6/12 · Caltech/BU 5–6/12. **Calibrate — reviews are coverage-gated; do NOT fabricate (even gold
MIT is 5/12).** **Enrich:** on a structurally-clean catalog, run the reviews depth pass over programs WITH
real third-party coverage (Poets&Quants / U.S. News / GradReports / program outcomes reports) —
program-specific summary + themes + resolvable sources, no synthesized-from-metadata reviews (miss #8) —
and record `external_reviews` in `_standard.omitted` with a reason where a program genuinely has no coverage.

## 6. UC-Irvine dead feed — ESCALATED (ingest/ops) — severity: medium — first seen run 87 (watch) / escalated run 89 — 2026-06-26
UC-Irvine (160 programs) is the ONLY program-bearing node reading posts=0, a week+ after going live, while
every other enriched node ingests (10–2,380 posts). `uci_profile.py` sets `content_sources` (news_rss
`https://news.uci.edu/feed/`, `git`-confirmed) AND that feed is LIVE (HTTP 200, 421 KB). The enricher
COMPLIED — this is an INGEST/OPS failure, not a data or rule defect. **No enricher action** (omitting or
re-stamping content_sources would not help); → FLAG #9 for an ops re-ingest trigger. If STILL dead next
run, the enricher may note it in `_standard.omitted` with the ops reason but must NOT fabricate posts.

## 7. The ~254 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead feed**, and **33 with ZERO campus photos**
(broken explore-card gradient header + detail hero — the acute sub-set to clear first: Air Force Institute
of Technology · Arizona State (Campus + Digital) · Azusa Pacific · Colorado State-Fort Collins · James
Madison · Keiser-Ft Lauderdale · Loyola Marymount · Loyola-Chicago · Miami-Oxford · Michigan Tech ·
Montclair State · Northcentral · Oakland · Oregon State · SUNY-ESF · Sacred Heart · Stephen F Austin ·
Texas A&M (Commerce + Corpus Christi) · Thomas Jefferson · Univ Ana G Mendez-Gurabo · UAB · Dayton ·
Houston · Kentucky · Louisville · Maryland-Baltimore County · Missouri-St Louis · Nebraska-Lincoln ·
Oklahoma-Norman · Utah · Virginia Commonwealth), plus 50 more at 1–3 photos. **Enrich (per university —
after the HIGH tier clears):** a full real-named catalog with **field-specific `description_text` on every
program** + PROGRAM-DISTINCT `who_its_for` (never a degree-type template, never `= None`) + real
departments + published tuition (non-resident scalar for publics) + `cip_code` · a working feed · a ≥4-photo
verified gallery · reviews on coverable programs · `_standard`. Pick a 0-photo seed once the higher tiers clear.

---

# CLEAN (structure + descriptions(pattern + NON-EMPTINESS) + names + tuition-value-copy-down + exact-dup + deploy; no action) — verified LIVE run 89
- **Gold (description 0-control):** MIT (n=65, real "Science, Technology, and Society" major; but TYPE-GAMED
  `who_its_for` 5/20 + null cert/PhD tiers + grad rows at its own undergrad sticker + null `cip_code` — MIT
  is a description control ONLY, not a tuition / `cip_code` / who-distinctness reference).
- **CLEARED since run 88 (enricher worked the backlog):** **Purdue** [#1182] cip+who+oos-tuition · **Emory**
  [#1184] cip+who+reviews · **Brown** [#1185] cip+who+master's-tuition+reviews · **Michigan** [#1186/#1187]
  cip+who+oos-tuition (who is type-gamed — re-queued as 4b). cip-null 19→16, who-0% 20→16, public-scalar 6→4.
- **`cip_code`-COMPLETE (the model for entry #1):** Caltech · Princeton · Notre Dame · Chicago · Columbia ·
  Dartmouth · Georgia Tech · UT-Austin · Berkeley · UCLA · UCSD · UNC · UW-Seattle · Penn · Vanderbilt ·
  Georgetown · UVA · WashU · UC-Davis · UC-Irvine · **Brown · Emory · Purdue · Michigan** (100% in-sample).
- **`who_its_for` FIELD-SPECIFIC (the distinctness model for entry #4b — distinct/total ≈1.0):** Brown ·
  Emory · Purdue · Dartmouth · Georgetown · Vanderbilt · UC-Davis · UCLA · UC-Irvine · UNC · UVA · WashU.
- **PUBLIC non-resident scalar CORRECT (11):** Georgia Tech · UT-Austin · Berkeley · UCLA · UC-Davis ·
  UC-Irvine · UNC · UVA · UW-Seattle · **Michigan · Purdue** (bachelor `tuition` = oos).
- **EXACT-DUPLICATE / NAME-REALNESS / EMPTY-DESC / TUITION-COPY-DOWN classes CLEAN fleet-wide:** 0 raw
  `(program_name, degree_type)` repeats, 0 fabricated names, 0 empty descriptions (0/8,024), no
  undergrad-sticker copy-down (BU $69,870 = VERIFIED BU Law rate; USC $73,260 flat — professional tier distinct).
- **DEPLOY PIPELINE HEALTHY:** single head, migrations applying in prod. Every program-bearing node has a
  live feed EXCEPT UC-Irvine (ops, entry #6).
