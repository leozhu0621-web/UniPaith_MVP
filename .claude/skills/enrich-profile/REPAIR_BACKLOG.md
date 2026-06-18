# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated content shipped live — build-artifact
assemblies / invented units / synthesized reviews / namesake-scrapes) · **high** (real
data but materially broken structure — rollup names / prefix-doubling / verbatim-across-
levels / field-echo departments) · **medium** (institution-level seed below gold).
Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-18 (grader **run 59** — **FULL-FLEET sweep: all 150 LIVE institutions
re-measured** via the live API, using the repo's own `profile_standard/anti_stub.py`
analyzer + structure metrics). **1 rule change**: a new miss-#8 + §9 gate for the
**BUILD-ARTIFACT ASSEMBLY** description class (a per-row "Catalog entry &lt;hex&gt;:" nonce +
school-division frame + namesake-scrape that ZEROES every anti_stub metric and auto-merged
3 catalogs into CERTIFIED_CLEAN). See CHANGELOG run 59._

## Fleet at a glance (run 59, live `api.unipaith.co/api/v1`)

- **Fleet = 150 institutions LIVE** — the external bulk-seed (#779) added **110 institution-
  level stubs (US-News ranks 37–152)** on top of the 28 mature catalogs + the 12 earlier
  seeds (#746). Seeding is now **external** (#780): the routine ENRICHES + REPAIRS only,
  never adds — these 122 stubs are the enrichment backlog.
- **🔴 HEADLINE (drives the run-59 rule): run-58's school-blurb "wins" REGRESSED into a NEW
  fabrication form on 3 of 4 catalogs.** The #766/#770/#790 "de-fabricate" PRs auto-merged
  green and joined `CERTIFIED_CLEAN`, but **UCLA / UW-Seattle / Michigan** ship a per-row
  **"Catalog entry &lt;hex&gt;:" build-artifact assembly** (~98% of rows) — a debug-id nonce
  (often DOUBLED) + a "draws on {Division}… Published through {School} on the **Westwood**
  campus" frame (UW's rows wrongly say UCLA's campus) + scraped **namesake** text (an
  Astronomy degree described as a *journal's* editorial board). The per-row nonce makes
  every row unique, so it scored **0 on every anti_stub metric** and CI passed garbage.
  Only **UT-Austin #768** of the four de-fabricated genuinely (0 artifacts).
- **Mature-catalog structure tiers persist (documented classes):** rollup-name (Berkeley
  37 / Stanford 35 / Harvard 35 / Columbia 34 / Cornell 33 / Penn 27 %), verbatim-across-
  levels (Purdue 82 / Berkeley 81 / JHU 80 / Cornell 76 / Penn 74 / UChicago 50 / Rice 43 %),
  field-echo department (Stanford 95 / UChicago 89 / Columbia 88 / Penn 88 / Cornell 86 /
  Berkeley 82 / USC 80 %), prefix-doubling (Yale 70 %), literal "(CIP NN.NN)" (Penn 11 %).
- **Checklist on the 28 mature catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs"
  names; all carry 5 campus photos & a non-zero feed. **Genuinely clean (desc + structure):**
  MIT (gold), NYU, UCSD, JHU(names), UT-Austin, UIUC, Northwestern, Wisconsin, Georgia Tech.
- **The 110 new seeds (#779) are bare:** 0 programs each, **all 110 `posts=0`**, **19 with
  ZERO campus photos** (broken explore card + hero), **38 with &lt;4 photos**. The 12 earlier
  seeds (#746) remain 5/5 empty-`description_text` null-`department` flagship rows, dead feeds.

⚠️ **FLAG FOR HUMAN (code, out of grader scope):** the CI gate `anti_stub.py` is
description-FORM-only and was defeated twice now (run-55 stub-swap, run-59 nonce-assembly).
It needs (1) a leading-id-token / division-frame / namesake metric, (2) a **nonce-strip**
(`^Catalog entry [0-9a-f]+:` + any leading id) BEFORE the verbatim/shared-body counts, and
(3) **UCLA · UW · Michigan removed from `CERTIFIED_CLEAN`** until genuinely repaired —
otherwise a re-stub of them re-passes CI. None of these are grader-editable (app/test code).

---

# CRITICAL — fabricated content shipped live (fix before any other deepening)

## 1. Build-artifact-assembly tier — UCLA · UW-Seattle · Michigan — severity: critical — first seen run 59 · 2026-06-18
Per-row machine assembly shipped as "de-fabrication", live, ~98% of rows; all 3 in
`CERTIFIED_CLEAN` (CI green on garbage). Live measures (n / "Catalog entry" prefix / doubled):

> **UPDATE 2026-06-18 (enricher, PR #802 / `uwdefab1`):** **UW-Seattle is DONE** — all 365
> descriptions regenerated from the verified English-Wikipedia lead per discipline (258 fields,
> disambiguation-guarded, 9 namesake-journal/society mismatches corrected after Codex review),
> per-credential, real Seattle college, no "Catalog entry"/Westwood junk. A `machine_artifacts()`
> gate + CI test was added so the class can't recur, and **Michigan, UCLA, and Stanford were
> removed from `CERTIFIED_CLEAN`** (they fail the new gate). **Michigan (374) + UCLA (364) +
> Stanford (150) remain LIVE with the same junk — they are the top repair targets**; regenerate
> each the same way, then re-add to `CERTIFIED_CLEAN`. (Stanford #803 was certified clean before
> this gate existed; its 150 "Catalog entry <hex>:" rows are the same build-script artifact.)

| Institution | n | catID prefix | doubled | div-frame | namesake scrape |
|---|---|---|---|---|---|
| **University of California-Los Angeles** | 373 | 364 (98%) | 120 | 364 | yes (e.g. Astronomy→journal) |
| **University of Washington-Seattle Campus** | 365 | 350 (96%) | 316 | 350 | yes + "Westwood campus" geo-lie |
| **University of Michigan-Ann Arbor** | 379 | 374 (99%) | 109 | 109 | yes (e.g. Archaeology→list article) |

**Repair each (one university, all dimensions):** delete the "Catalog entry &lt;hex&gt;:" nonce
+ the "draws on…/Published through…/Westwood campus" division frame + every namesake scrape;
RESEARCH each description from the university's OWN catalog/department page (one paragraph per
PROGRAM); verify no peer geography/units; then re-certify ONLY after the analyzer can see this
form (see human-flag). Model: UT-Austin #768 / NYU #753 / UIUC #763 — NOT the stub-swap.

## 2. Stanford University — fabricated units + synthesized reviews + rollup + field-echo dept — severity: critical — first seen ≤run 24 · 2026-06-15
188 programs. Live: **35% rollup names, 95% field-echo dept, 28% shared-body**; carried
fabricated-unit + synthesized-review breaches. **Repair:** verify every named school/center is
a real Stanford unit housing the program; de-roll-up names; real owning schools in `department`;
remove synthesized reviews; per-credential bodies.

## 3. Purdue University-Main Campus — cross-institution-copy + verbatim-across-levels — severity: critical — first seen run 25 · 2026-06-15
310 programs. #661's descriptions were COPIED from peer catalogs + find-replaced (JHU
"Chesapeake"/"Writing Seminars", Penn "SAS"/"Wharton"/"Perelman", re-labeled peer landmarks).
Live: **82% verbatim-across-levels, 11% rollup, 28% shared-body.** **Repair:** research each
description from Purdue's OWN catalog; scan for peer signatures/geography and FAIL on any hit;
give each credential level its own body.

## 4. Boston University — cross-institution-copy peer signatures + field-echo dept — severity: critical — first seen run 32 · 2026-06-16
376 programs. #675's descriptions carry ANOTHER university's units ("Perelman" ×22, "Lick
Observatory" ×4, "Medill" ×2). Live structure: **dept-echo 80%, csplit 13%, rollup 2%.**
**Repair:** allowlist-scan every description against BU's own org chart (NOT a peer denylist);
research from BU's catalog; real BU school in `department`; collapse the concentration-split rows.

---

# HIGH — real data, structurally broken (rollup · verbatim-across-levels · field-echo dept · prefix)

## 5. University of California-Berkeley — severity: high — first seen run 22 · 2026-06-15
269 programs. **37% rollup + 81% verbatim-across-levels + 82% field-echo dept.** De-roll-up
names; per-credential researched bodies; real owning schools in `department`.

## 6. University of Pennsylvania — severity: high — first seen run 24 · 2026-06-15
250 programs. **27% rollup + 11% literal "(CIP NN.NN)" in names + 74% verbatim + 88% dept-echo.**
Strip the CIP codes (miss #2 CIP-code tell); de-roll-up; per-credential bodies; real departments.

## 7. Cornell University — severity: high — first seen run 22 · 2026-06-15
274 programs. **33% rollup + 76% verbatim + 86% dept-echo.** De-roll-up the federal-CIP names;
per-credential bodies; real departments.

## 8. Columbia University — severity: high — first seen ≤run 24 · 2026-06-15
263 programs. **34% rollup + 88% dept-echo + 23% shared-body.** De-roll-up names; per-credential
bodies; real departments.

## 9. Harvard University — severity: high — first seen ≤run 24 · 2026-06-15
343 programs. **35% rollup + 68% dept-echo + 24% shared-body.** De-roll-up names; real departments.

## 10. Johns Hopkins University — severity: high — first seen run 30 · 2026-06-16
246 programs. Clean names (rollup 0%) but **80% verbatim-across-levels** — descriptions TRUE but
stamped per-FIELD, shared by a credential sibling (gold MIT 0%). Give each credential level its
own researched body.

## 11. University of Chicago — severity: high — first seen run 30 · 2026-06-16
103 programs. **50% verbatim + 89% dept-echo.** Per-credential bodies; real departments.

## 12. Rice University — severity: high — first seen run 30 · 2026-06-16
159 programs. **43% verbatim + 64% dept-echo + 4% csplit.** Per-credential bodies; real departments.

## 13. Yale University — severity: high — first seen ≤run 30 · 2026-06-16
189 programs. **70% prefix-doubling (`description_text.startswith(program_name)`) + 75% dept-echo.**
Strip the name prefix; per-credential bodies; real departments.

## 14. University of Southern California — field-echo departments + concentration-split — severity: high — first seen run 58 · 2026-06-18
613 programs; in `CERTIFIED_CLEAN` (every anti_stub description metric 0 live) but ships the
structure defects the gate is blind to: **~80% field-echo departments** (`department` = the
degree's field verbatim while the real owning USC school is named only in the description) + a BA
decomposed into **"Dramatic Arts, {Emphasis}" concentration-split rows**. **Repair:** put the real
USC school/college in `department`; collapse the emphasis rows into one BA carrying the emphases as
`tracks`.
- _Verify-then-classify:_ Stanford 95 / UChicago 89 / Caltech 88 / Princeton 74 % dept-echo —
  confirm whether `department` is the field VERBATIM with a real school known (a defect) or a
  genuinely real "Department of {field}" the substring heuristic over-counts (no action) before repairing.

---

# MEDIUM — institution-level seeds: the enrichment backlog (seeding is external, #779/#746)

## 15. The 110 bulk seeds (#779, US-News ranks 37–152) — severity: medium — first seen run 59 · 2026-06-18
Each entered at institution level with **0 programs, a dead `posts=0` feed**, and (for 38 of them)
a **&lt;4-photo gallery**. **19 have ZERO campus photos** — these break BOTH the explore-card
gradient header and the detail hero, so they are the **acute** sub-set to clear first: Arizona
State (Campus Immersion), Colorado State-Fort Collins, James Madison, Loyola Marymount, Loyola
Chicago, Miami-Oxford, Michigan Tech, Oregon State, SUNY-ESF, Thomas Jefferson, UAB, Dayton,
Houston, Kentucky, UMBC, Nebraska-Lincoln, Oklahoma-Norman, Utah, VCU. **Enrich (per university,
one PR):** full real-named catalog + field-specific descriptions + real departments · a working
feed (`posts`>0) · a ≥4-photo verified-and-credited gallery · reviews on coverable programs ·
`_standard`. Pick the highest-priority (a 0-photo seed) once the CRITICAL tier is clear.

## 16. The 12 earlier seeds (#746) — severity: medium — first seen run 57 · 2026-06-18
Each ships 5 flagship rows with **5/5 empty `description_text` + null `department`** and a dead feed;
galleries 1–5 photos (Florida 1, Emory/Notre Dame 2). Florida also mis-credentials Law/Pharmacy.
Same enrichment as #15: researched descriptions + real departments for the flagship rows, a working
feed, a ≥4-photo gallery, then deepen to a full catalog. Seeds: Florida · Emory · Notre Dame ·
Vanderbilt · WashU · UNC-Chapel Hill · UC-Davis · Brown · Georgetown · UC-Irvine · Dartmouth · UVA.

---

# CLEANUP — clean / low priority (verify-only)

## NYU — slug-prefix leak on combined-major rows — severity: low — first seen run 57 · 2026-06-18
NYU #753 is clean live (0 artifacts / verbatim 0 / dept-echo 0). Residual: ~7% of combined-major
rows open with the URL slug bled into the body; strip the leading `slug — ` prefix; add the connector.

## Georgia Tech — deploy flipped, now clean — first seen run 58 · 2026-06-18 — RESOLVED
#765's field-specific descriptions are LIVE (143 programs, 0 artifacts, dept-echo 0, rollup 4%).
No data repair needed.

## Genuinely clean (desc + structure; no action) — MIT (gold) · NYU · UCSD · UT-Austin · UIUC · Northwestern · Wisconsin · Georgia Tech · JHU(names) · CMU · Princeton · Caltech · Duke
Verified clean on the description metrics this run; the dept-echo substring heuristic over-counts on
small real-department catalogs (Princeton/Caltech) — treat as a heuristic artifact unless a row's
`department` is literally the field copied from the name while a real school is known.
