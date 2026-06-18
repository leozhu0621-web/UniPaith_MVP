# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated content shipped live — invented
units / synthesized reviews / school-blurb stubs) · **high** (real data but materially
broken structure — rollup names / prefix-doubling / verbatim-across-levels) ·
**medium** (shallow / acutely-incomplete seed). Evidence is from the live API
(`api.unipaith.co/api/v1`).

_Last graded: 2026-06-18 (grader **run 57** — **FULL-FLEET sweep: all 40 LIVE institutions
re-measured across every dimension** via the live API). **1 rule change**: the institution-level
**SEED FLOOR** (SKILL.md §2 growth block) tightened — see CHANGELOG run 57._

## Fleet at a glance (run 57, live `api.unipaith.co/api/v1`)

- **Fleet = 40 institutions LIVE** (run-56's stuck deploy is RESOLVED; the 12 seeds from #746 are now live).
- **Checklist GREEN on the 28 mature catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs"-rollup program
  names anywhere; all 28 carry 5 campus photos; all 28 have a non-zero feed.
- **Wins since run 56 (verified live):** **NYU #753** de-fabricated (real per-program descriptions + real
  departments — the Rice-#663 pattern; connects 0% / verbatim 0% / dept-echo 0%); **CMU #755** de-prefixed
  (prefix 100%→0%); **Princeton #754/#756** de-fabricated (0 rollup / 0 verbatim / cip_code persisted);
  **Caltech + UCSD de-padded #751** (Caltech 90→43, UCSD 194→137) and **UCSD per-credential #749** (verbatim
  80%→0%). These leave the school-blurb tier at **6** catalogs (NYU exited).
- **NEW this run — the 12 institution-level seeds (#746) shipped HALF-BUILT** (drives the run-57 rule change):
  every one has **5/5 empty-`description_text` null-`department` flagship rows**; **7/12 a <4-photo gallery**
  (Florida 1, Emory/Notre Dame 2, Vanderbilt/WashU/UNC/UC-Davis 3); **12/12 a dead `posts=0` feed**. See the
  MEDIUM band — these are ACUTE growth-blockers under the tightened SEED FLOOR.

---

# CRITICAL — fabricated content shipped live (fix before any new university)

## 1. School-blurb fabrication tier — 6 catalogs, ~2,500 programs (run-43 miss #8 + run-9 synthesized reviews)
The enricher's recurrent "repair to gold" default: replace #646 stubs with **one school-level blurb stamped
across every field**, in the frame `"{Uni}'s {field} program connects to {SCHOOL blurb}.. Students build depth
in {field} through seminars, research, and {City} industry and community partnerships."` — plus **synthesized
reviews** citing institution-level "U.S. News — {Uni} rankings" under a false "aggregated/paraphrased"
disclaimer. Live measures this run (connects-to / double-period / dept-echo):

| # | Institution | n | connects | dbl-period | dept-echo | first seen |
|---|---|---|---|---|---|---|
| 1a | **University of Southern California** | 613 | 100% | 96% | 99% | run 43 · 2026-06-17 |
| 1b | **University of Illinois Urbana-Champaign** | 419 | 100% | 96% | 98% | run 46 · 2026-06-18 |
| 1c | **University of Michigan-Ann Arbor** | 379 | 100% | 93% | 100% | run 47 · 2026-06-18 |
| 1d | **University of California-Los Angeles** | 373 | 100% | 96% | 100% | run 48 · 2026-06-18 |
| 1e | **University of Washington-Seattle** | 365 | 100% | 98% | 99% | run 49 · 2026-06-18 |
| 1f | **The University of Texas at Austin** | 338 | 100% | 96% | 98% | run 50 · 2026-06-18 |

**Repair each:** (1) RESEARCH each program's description from the university's OWN catalogue/department page —
one paragraph per PROGRAM, not one school-blurb stamped across its fields; re-count cross-field shared bodies +
double-period rows → 0. (2) Put the real owning school/college in `department`, not the field echoed from the
name. (3) REMOVE the synthesized reviews — re-gather genuine program-specific coverage or omit-with-reason.
Do what NYU #753 / Rice #663 did (now the proven in-fleet template), not what #696/#706/#710/#714/#716/#718 did.
✅ feeds + name-disambiguation already done on all six.

## 2. Georgia Institute of Technology-Main Campus — classification-stub + 58 synthesized reviews — severity: critical — first seen run 53 · 2026-06-18
143 programs. Live: **100% prefix-doubled, 73% classification stubs** ("…is an undergraduate major offered
through Georgia Tech's College of Engineering."), **99% dept=field-echo**, 6 rollup names. #730 bolted **58
synthesized reviews** (identical institution-level "Georgia Tech — Rankings" theme on 49/58, verbatim theme
details, dept-homepage/discipline-ranking "sources") onto this still-fabricated structure. 4 hand-crafted
flagship reviews (BS CS, MBA, OMS Analytics, OMSCS) are genuine — the right model.
**Repair:** de-fabricate STRUCTURE first (kill 100% classification + 100% prefix, real `department`, de-roll-up
6 names); THEN keep the 4 genuine flagships, remove the 58 synthesized reviews, re-gather or omit (miss #8).

## 3. Boston University — cross-institution-copy peer signatures + verbatim-across-levels — severity: critical — first seen run 32 · 2026-06-16
376 programs. #675's field-specific descriptions INTRODUCED a no-fabrication breach (run-25 class): ~31 rows
carry ANOTHER university's unit — "Perelman" (Penn med) ×22 on BU chem/neuro rows, "Lick Observatory"
(Berkeley) ×4 on BU astronomy, "Medill" (Northwestern) ×2, "Whiting"/"Weinberg"/"Kellogg" — plus **~51%
identical-across-credential-levels** descriptions and **86% dept-echo** (live structural this run: dept-echo 86%
+ 6% rollup).
**Repair:** scan every description for a location-mismatched place-name / peer-signature string / re-labeled
peer landmark and FAIL on any hit; research each from BU's OWN catalog; give each credential level its own body;
put the real BU school in `department`.

## 4. Stanford University — fabricated units + synthesized reviews + rollup names — severity: critical — first seen ≤run 24 · 2026-06-15
188 programs. Live: **20% rollup names, 95% dept-echo**, carried fabricated-unit + synthesized-review breaches
(feed now `posts=269`). **Repair:** verify every named school/center is a real Stanford unit that houses the
program; de-roll-up names; real departments; remove synthesized reviews.

## 5. Purdue University-Main Campus — cross-institution-copy descriptions + verbatim-across-levels — severity: critical — first seen run 25 · 2026-06-15
310 programs. #661's "field-first" descriptions were built by COPYING peer catalogs + find-replacing the campus
name: ~52/310 rows carried JHU's "Chesapeake"/"Writing Seminars", Penn's "SAS"/"Wharton"/"Perelman", Cornell's
"CALS"/"Weill", plus re-labeled peer landmarks ("Purdue Lab of Ornithology" ← Cornell's). Live this run: **42%
verbatim-across-levels, 9% rollup**. **Repair:** research each description from Purdue's OWN catalog — never
adapt a peer's by find-replace; scan for peer signatures and FAIL on any hit.

## 6. Northwestern University — synthesized reviews on an otherwise-clean structure — severity: critical — first seen ≤run 24 · 2026-06-15
308 programs. Structure now reads clean (rollup 1% / dept-echo 2% / 0 verbatim), but the carried synthesized-
review breach (run-9 class) persists. **Repair:** remove synthesized reviews; re-gather genuine program-specific
coverage or omit-with-reason. (Closest to a single-dimension clear of the CRITICAL band.)

---

# HIGH — real data, structurally broken (rollup names · prefix · verbatim-across-levels · dept-echo)

## 7. University of Pennsylvania — severity: high — first seen run 24 · 2026-06-15
250 programs. **28% rollup names + literal "(CIP NN.NN)" codes left in names + 89% dept-echo** (descriptions +
prefix already cleared by #659). Strip the CIP codes, de-roll-up names, switch generic "Bachelor's in {field}"
to Penn's real designation, put the real school in `department`.

## 8. University of California-Berkeley — severity: high — first seen run 22 · 2026-06-15
269 programs. **26% rollup names + 90% dept-echo** (descriptions + prefix cleared by #652). De-roll-up names;
real departments.

## 9. Harvard University — severity: high — first seen ≤run 24 · 2026-06-15
343 programs. **23% rollup names + 68% dept-echo.** De-roll-up names; real departments.

## 10. Columbia University — severity: high — first seen ≤run 24 · 2026-06-15
263 programs. **23% rollup names + 88% dept-echo.** De-roll-up names; real departments.

## 11. Cornell University — severity: high — first seen run 22 · 2026-06-15
274 programs. **22% rollup names + 87% dept-echo** (descriptions + prefix cleared by #654/#615). De-roll-up the
federal-CIP names (", General"; embedded slash; ", Area Studies"); real departments; switch generic credential
form to Cornell's designation.

## 12. Yale University — severity: high — first seen ≤run 30 · 2026-06-16
189 programs. **70% prefix-doubling (`description_text.startswith(program_name)`) + 75% dept-echo.** Strip the
name prefix; real departments.

## 13. Duke University — severity: high — first seen ≤run 30 · 2026-06-16
154 programs. **66% prefix-doubling + 72% dept-echo** + carried synthesized-review concern. Strip prefix; real
departments; verify/replace reviews.

## 14. Johns Hopkins University — severity: high — first seen run 30 · 2026-06-16
246 programs. Near-clean structure (0 dup/prefix/rollup) but **43% verbatim-across-levels** — descriptions are
TRUE but stamped per-FIELD, shared verbatim by a credential sibling (gold MIT 0%). Give each credential level
its own researched body; then it is reviews-ready. (3 "Area Studies" rollup rows remain.)

## 15. Rice University — severity: high — first seen run 30 · 2026-06-16
159 programs. **43% verbatim-across-levels + 77% dept-echo.** Per-credential bodies; real departments.

## 16. University of Chicago — severity: high — first seen run 30 · 2026-06-16
103 programs. **41% verbatim-across-levels + 89% dept-echo** (2 "Area Studies" rollup names). Per-credential
bodies; real departments.

---

# MEDIUM — the 12 institution-level seeds (#746): shallow AND half-built (ACUTE growth-blockers per the run-57 SEED FLOOR)
All twelve entered at institution level (5 flagship programs, no `_standard`) but were shipped **below the seed
floor** — each must be brought to floor (≥4 credited photos + a live feed + flagship programs that each carry a
researched `description_text` and a real `department`) before the fleet grows to #41. First seen **run 57 ·
2026-06-18** (live). Per-seed state this run:

| Institution | flagship rows | empty desc / null dept | photos | feed | extra |
|---|---|---|---|---|---|
| University of Florida | 5 | 5/5 / 5/5 | **1** | dead | "Law"/"Pharmacy" mis-typed as PhD |
| Emory University | 5 | 5/5 / 5/5 | **2** | dead | |
| University of Notre Dame | 5 | 5/5 / 5/5 | **2** | dead | |
| Vanderbilt University | 5 | 5/5 / 5/5 | **3** | dead | |
| Washington University in St Louis | 5 | 5/5 / 5/5 | **3** | dead | |
| University of North Carolina-Chapel Hill | 5 | 5/5 / 5/5 | **3** | dead | |
| University of California-Davis | 5 | 5/5 / 5/5 | **3** | dead | |
| Brown University | 5 | 5/5 / 5/5 | 4 | dead | |
| Georgetown University | 5 | 5/5 / 5/5 | 4 | dead | |
| University of California-Irvine | 5 | 5/5 / 5/5 | 4 | dead | |
| Dartmouth College | 5 | 5/5 / 5/5 | 5 | dead | |
| University of Virginia-Main Campus | 5 | 5/5 / 5/5 | 5 | dead | |

**Repair (per seed, in one PR):** write a researched `description_text` + real `department` for each flagship
program (fix Florida's mis-credentialed Law=JD / Pharmacy=PharmD); top every gallery to ≥4 verified-and-credited
campus photos; configure a working `news_rss`/`events_feed` so `posts` > 0. (Note: a `posts=0` here may be a
configured-but-pre-ingest feed; if a real feed is configured and merely awaiting the daily ingest, that one
sub-item is satisfied — but the empty descriptions + short galleries are set at seed time and are not.)

---

# CLEANUP — near-clean, low priority

## NYU — slug-prefix leak on combined-major rows — severity: low — first seen run 57 · 2026-06-18
NYU #753 genuinely de-fabricated the catalog (the win above). Residual: **36/507 rows (7%)** open with the URL
slug bled into the body — `"anthropology-classical-civilization — The Department of Anthropology…"` — almost all
on dual-field combined-major rows (also missing a connector in the name, e.g. "…in Anthropology Classical
Civilization"). Strip the leading `slug — ` prefix; add the connector to the combined-major names.

## Clean / gold-equal (no action) — MIT (gold), CMU, Princeton, Caltech, UCSD
Verified clean on structure this run (0 connects / 0 verbatim / 0 prefix). The dept-echo substring heuristic
over-counts on small real-department catalogs (Princeton/Caltech 93%, UChicago/Stanford/Berkeley high) — treat
as a heuristic artifact, not a defect, unless a row's `department` is literally the field copied from the name.
