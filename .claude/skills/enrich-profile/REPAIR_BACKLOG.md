# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated content shipped live — invented
units / synthesized reviews / school-blurb stubs) · **high** (real data but materially
broken structure — rollup names / prefix-doubling / verbatim-across-levels / field-echo
departments) · **medium** (shallow / acutely-incomplete seed). Evidence is from the
live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-18 (grader **run 58** — **FULL-FLEET sweep: all 40 LIVE institutions
re-measured across every structural dimension** via the live API). **1 rule change**: the
§8.5 enforced anti-stub gate tightened — `CERTIFIED_CLEAN` must also assert the miss-#2
STRUCTURE metrics (field-echo department · CIP-rollup name/dept · literal CIP code ·
concentration-split rows), not descriptions only. See CHANGELOG run 58._

## Fleet at a glance (run 58, live `api.unipaith.co/api/v1`)

- **Fleet = 40 institutions LIVE** (28 mature catalogs + the 12 institution-level seeds).
- **Wins since run 57 (verified live):** **USC #759** + **UIUC #763/#764** de-fabricated — the
  school-blurb frame is GONE live (USC connects 100%→0 / double-period 0; UIUC connects 0).
  **Northwestern #760** removed the synthesized reviews — structure reads clean (verbatim 0 /
  rollup 2%). **Duke #757** certified clean (prefix 0 / verbatim 0). **Georgia Tech #765**
  de-fabricated AT SOURCE (`catalog.gatech.edu` field-specific descriptions, real departments,
  58 synthesized reviews removed) and joined `CERTIFIED_CLEAN` — its **Deploy Backend is
  in_progress at grade time, so the LIVE API still returns the pre-#765 #730 stubs** (100%
  prefix-double / 66% dept-echo); the live will flip when the deploy completes (the standard
  merged-≠-deployed lag).
- **The school-blurb tier is now 3 still-live (down from 6):** **UCLA · UW-Seattle · UT-Austin**
  remain 100% "connects to" / 93–98% double-period LIVE. **Michigan** is the 4th but has an
  OPEN repair PR (**#766**, in-flight).
- **NEW this run (drives the run-58 rule change): `CERTIFIED_CLEAN` is description-only.** A
  certified 613-program catalog (USC) scores 0 on every `anti_stub.analyze` description metric
  LIVE yet ships **~62% field-echo departments** + **concentration-split rows** (one BA split
  into four "…, {Emphasis}" rows) — neither caught, because the enforced gate has no STRUCTURE
  metric. See the new HIGH band #17.
- **Checklist on the 28 mature catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs"-rollup
  names; all 28 carry 5 campus photos; all 28 have a non-zero feed.
- **The 12 seeds (#746) remain HALF-BUILT** (run-57 SEED FLOOR): each 5/5 empty-`description_text`
  null-`department` flagship rows, 7/12 a <4-photo gallery, 12/12 `posts=0`. See the MEDIUM band.

---

# CRITICAL — fabricated content shipped live (fix before any new university)

## 1. School-blurb fabrication tier — 3 catalogs still LIVE (run-43 miss #8 + run-9 synthesized reviews)
One school-level blurb stamped across every field in the frame `"{Uni}'s {field} program connects
to {SCHOOL blurb}.. Students build depth in {field} through seminars, research, and {City} industry
and community partnerships."` + synthesized institution-ranking reviews. Live measures this run
(connects-to / double-period / dept-echo):

| Institution | n | connects | dbl-period | dept-echo | first seen |
|---|---|---|---|---|---|
| **University of California-Los Angeles** | 373 | 100% | 96% | 59% | run 48 · 2026-06-18 |
| **University of Washington-Seattle** | 365 | 100% | 98% | 74% | run 49 · 2026-06-18 |
| **The University of Texas at Austin** | 338 | 100% | 96% | 56% | run 50 · 2026-06-18 |

**Repair each (one university per run, all dimensions):** research each program's description from
the university's OWN catalogue/department page (one paragraph per PROGRAM, not one school-blurb
stamped across its fields) → connects/double-period/cross-field-clause to 0; real owning
school/college in `department`, not the field echoed from the name; REMOVE the synthesized reviews,
re-gather genuine program-specific coverage or omit-with-reason; then join `CERTIFIED_CLEAN`
(now including the STRUCTURE metrics per the run-58 rule). Do what USC #759 / UIUC #763 / NYU #753
/ Rice #663 did, not the stub-swap.
**In-flight:** **University of Michigan-Ann Arbor** (379, still 100% blurb live) has OPEN PR **#766**
("catalogue descriptions … anti-stub clean") — let it land + verify live; if it ships field-echo
departments, it is NOT done (run-58 rule).

## 2. Stanford University — fabricated units + synthesized reviews + rollup names — severity: critical — first seen ≤run 24 · 2026-06-15
188 programs. Live this run: **36% rollup names, 94% dept-echo**, carried fabricated-unit +
synthesized-review breaches (feed `posts=269`). **Repair:** verify every named school/center is a
real Stanford unit that houses the program; de-roll-up names; real departments; remove synthesized
reviews; then certify (structure metrics included).

## 3. Purdue University-Main Campus — cross-institution-copy descriptions + verbatim-across-levels — severity: critical — first seen run 25 · 2026-06-15
310 programs. #661's "field-first" descriptions were built by COPYING peer catalogs + find-replacing
the campus name (JHU "Chesapeake"/"Writing Seminars", Penn "SAS"/"Wharton"/"Perelman", re-labeled
peer landmarks). Live this run: **82% verbatim-across-levels, 11% rollup.** **Repair:** research each
description from Purdue's OWN catalog — never adapt a peer's by find-replace; scan for peer signatures
and FAIL on any hit; give each credential level its own body.

## 4. Boston University — cross-institution-copy peer signatures — severity: critical — first seen run 32 · 2026-06-16
376 programs. #675's field-specific descriptions INTRODUCED a no-fabrication breach (run-25 class):
~31 rows carry ANOTHER university's unit ("Perelman" ×22, "Lick Observatory" ×4, "Medill" ×2). Live
structure this run: dept-echo 63%, rollup 6%, verbatim 0%. **Repair:** scan every description for a
location-mismatched place-name / peer-signature / re-labeled peer landmark and FAIL on any hit;
research each from BU's OWN catalog; real BU school in `department`. (Peer-signature strings not
re-scanned this run — carried from run 32 at unchanged confidence.)

---

# HIGH — real data, structurally broken (rollup names · prefix · verbatim-across-levels · dept-echo)

## 5. University of California-Berkeley — severity: high — first seen run 22 · 2026-06-15
269 programs. **38% rollup names + 81% verbatim-across-levels + 54% dept-echo.** De-roll-up names;
per-credential researched bodies; real departments.

## 6. Columbia University — severity: high — first seen ≤run 24 · 2026-06-15
263 programs. **36% rollup names + 87% dept-echo.** De-roll-up names; real departments.

## 7. Harvard University — severity: high — first seen ≤run 24 · 2026-06-15
343 programs. **36% rollup names + 64% dept-echo.** De-roll-up names; real departments.

## 8. Cornell University — severity: high — first seen run 22 · 2026-06-15
274 programs. **34% rollup names + 76% verbatim-across-levels + 56% dept-echo.** De-roll-up the
federal-CIP names; per-credential bodies; real departments.

## 9. University of Pennsylvania — severity: high — first seen run 24 · 2026-06-15
250 programs. **28% rollup names + 28% literal "(CIP NN.NN)" codes left in names + 74%
verbatim-across-levels + 65% dept-echo.** Strip the CIP codes (miss #2 CIP-code tell); de-roll-up
names; per-credential bodies; real departments.

## 10. Johns Hopkins University — severity: high — first seen run 30 · 2026-06-16
246 programs. Near-clean names (rollup 1%) but **80% verbatim-across-levels** — descriptions TRUE
but stamped per-FIELD, shared verbatim by a credential sibling (gold MIT 0%). Give each credential
level its own researched body.

## 11. University of Chicago — severity: high — first seen run 30 · 2026-06-16
103 programs. **50% verbatim-across-levels + 89% dept-echo.** Per-credential bodies; real departments.

## 12. Rice University — severity: high — first seen run 30 · 2026-06-16
159 programs. **43% verbatim-across-levels + 50% dept-echo.** Per-credential bodies; real departments.

## 13. Yale University — severity: high — first seen ≤run 30 · 2026-06-16
189 programs. **70% prefix-doubling (`description_text.startswith(program_name)`) + 46% dept-echo.**
Strip the name prefix; per-credential bodies; real departments.

## 14. CERTIFIED-but-structure-incomplete — the run-58 class — severity: high — first seen run 58 · 2026-06-18
A catalog that joined `CERTIFIED_CLEAN` (descriptions genuinely de-fabricated, every `anti_stub.analyze`
description metric 0 live) but still ships the miss-#2 STRUCTURE defects the enforced gate is blind to:
- **University of Southern California** (613) — **~62% field-echo departments** (`department` = the
  degree's field verbatim while the real owning USC school is named only in the description) + a BA
  decomposed into **four "Dramatic Arts, {Comedy/Design/Directing/Musical Theatre} Emphasis"
  concentration-split rows** (each its own program, `department` = the emphasis). **Repair:** put the
  real USC school/college in `department`; collapse the emphasis rows into one BA carrying the
  emphases as `tracks`; then re-certify under the tightened gate.
- _Verify-then-classify:_ other certified catalogs show high dept-echo (Princeton 72%, Caltech 56%)
  but on SMALL real-department catalogs that the substring heuristic over-counts — confirm whether
  `department` is the field VERBATIM with a real school known (a defect, as USC) or a genuinely
  shared real "Department of {field}" (a heuristic artifact, no action) before repairing.

---

# MEDIUM — the 12 institution-level seeds (#746): shallow AND half-built (run-57 SEED FLOOR)
All twelve entered at institution level (5 flagship programs, no `_standard`) but shipped **below the
seed floor** — each must reach floor (≥4 credited photos + a live feed + flagship programs that each
carry a researched `description_text` and a real `department`) before the fleet grows to #41. First
seen **run 57 · 2026-06-18** (live; unchanged this run):

| Institution | flagship rows | empty desc / null dept | photos | feed |
|---|---|---|---|---|
| University of Florida | 5 | 5/5 / 5/5 | **1** | dead (`posts=0`) |
| Emory University | 5 | 5/5 / 5/5 | **2** | dead |
| University of Notre Dame | 5 | 5/5 / 5/5 | **2** | dead |
| Vanderbilt University | 5 | 5/5 / 5/5 | **3** | dead |
| Washington University in St Louis | 5 | 5/5 / 5/5 | **3** | dead |
| University of North Carolina-Chapel Hill | 5 | 5/5 / 5/5 | **3** | dead |
| University of California-Davis | 5 | 5/5 / 5/5 | **3** | dead |
| Brown University | 5 | 5/5 / 5/5 | 4 | dead |
| Georgetown University | 5 | 5/5 / 5/5 | 4 | dead |
| University of California-Irvine | 5 | 5/5 / 5/5 | 4 | dead |
| Dartmouth College | 5 | 5/5 / 5/5 | 5 | dead |
| University of Virginia-Main Campus | 5 | 5/5 / 5/5 | 5 | dead |

**Repair (per seed, in one PR):** write a researched `description_text` + real `department` for each
flagship program (fix Florida's mis-credentialed Law=JD / Pharmacy=PharmD); top every gallery to ≥4
verified-and-credited campus photos; configure a working, actually-fetching `news_rss`/`events_feed`
so `posts` > 0. (A `posts=0` on a real configured-but-pre-ingest feed satisfies that one sub-item;
the empty descriptions + short galleries are set at seed time and do not.)

---

# CLEANUP — near-clean, low priority

## NYU — slug-prefix leak on combined-major rows — severity: low — first seen run 57 · 2026-06-18
NYU #753 de-fabricated the catalog (clean live: connects 0 / verbatim 0 / dept-echo 0). Residual:
~7% of rows open with the URL slug bled into the body on dual-field combined-major rows; the
combined-major names also miss a connector. Strip the leading `slug — ` prefix; add the connector.

## Georgia Tech — verify the deploy flipped — first seen run 58 · 2026-06-18
#765 de-fabricated GT at source + certified it clean; the Deploy Backend was in_progress at grade
time. Next run: confirm the LIVE API now returns the field-specific descriptions + real departments
(not the pre-#765 #730 stubs). No data repair needed if the deploy landed.

## Clean / gold-equal (no structural action) — MIT (gold), NYU, UCSD, CMU, Princeton, Caltech, Duke, UIUC, USC*, Northwestern
Verified clean on the description metrics this run. *USC carries the run-58 structure defect (HIGH
#14). The dept-echo substring heuristic over-counts on small real-department catalogs
(Princeton/Caltech) — treat as a heuristic artifact unless a row's `department` is literally the
field copied from the name while a real school is known.
