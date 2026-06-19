# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / build-junk text
shipped live — peer-signature copies / URL-slug leaks / namesake-scrapes) · **high** (real
data but materially broken structure — rollup names / verbatim-across-levels / prefix-
doubling / field-echo departments) · **medium** (institution-level seed below gold).
Evidence is from the live API (`api.unipaith.co/api/v1`), measured with the repo's own
`profile_standard/anti_stub.py` analyzer + structure heuristics.

_Last graded: 2026-06-19 (grader **run 61** — **FULL-FLEET sweep: all 300 LIVE institutions
re-measured** via the live API; all 40 catalogs with programs scanned across every
description + structure dimension, plus campus-photo / feed checks). **1 rule change**:
added the Oxford-comma FALSE-POSITIVE precision caveat to the §8.5(b) CIP-rollup tell —
the comma-and tell must be anchored to a federal-TAXONOMY ENDING, not any "X, Y, and Z"
list, or the gate false-flags real degrees (NYU ships 128 real comma-and majors). This
run ALSO CORRECTS run-60's loose rollup numbers fleet-wide (Michigan/UCLA/UW/UT-Austin/
Stanford/NYU were 0–1%, not the higher figures run 60 logged). See CHANGELOG run 61._

## Fleet at a glance (run 61, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE.** **40 carry programs; 260 are bare institution-level
  stubs** (0 programs, dead `posts=0` feed, 33 with ZERO campus photo). Seeding is
  **external**; the routine ENRICHES + REPAIRS only — these 260 stubs are the backlog.
- **🔴 HEADLINE — Purdue #832 was a PARTIAL / FAILED repair (top CRITICAL).** The interval's
  one profile-data PR (#832 "de-fabricate descriptions — remove peer-institution copy +
  per-credential rewrite") shipped a single-dimension partial pass: **31 peer-signature rows
  SURVIVE live** (Chesapeake on Anthropology, Wharton on Accounting, CALS on Animal Sciences,
  Perelman on Biochemistry, McCormick on Engineering Tech, Writing Seminars on English) and
  **82% verbatim-across-levels** (253/310, e.g. four "Speech, language, and hearing sciences…"
  rows byte-identical) + 87 shared-body fields are UNCHANGED. A "remove peer copy" PR that
  leaves 31 peer rows is the documented allowlist-denylist / clear-the-whole-class compliance
  gap (miss #8), not a new rule.
- **🟢 build-artifact tier STAYS RESOLVED.** `machine_artifacts = 0` on every one of the 40
  catalogs this run (UCLA / UW / Michigan / Stanford all still clean). Run-59's CRITICAL is
  cleared and has not regressed.
- **🟡 GRADER-ACCURACY CORRECTION — run-60 over-counted rollup.** Measured with the genuine
  federal-taxonomy tell only (not a loose Oxford-comma/slash regex), the rollup tier is REAL
  for **Berkeley 33 / Harvard 30 / Columbia 29 / Cornell 27 / Penn 23 %** — and **≈0–1% for
  Michigan / UCLA / UW / UT-Austin / Stanford / NYU / Wisconsin / Northwestern / JHU / Yale**
  (run 60 logged the loose, inflated figures for several of these). The rollup tier is
  smaller than run 60 reported.
- **Mature-catalog structure tiers persist (documented classes):** cross-institution-copy
  peer signatures (**Purdue 31 live · BU**), genuine rollup-name (Berkeley/Harvard/Columbia/
  Cornell/Penn above), verbatim-across-levels (**Purdue 82 / Berkeley 81 / Cornell 76 / Penn
  74 / UChicago 50 / Rice 43 %**), shared-leading-body / per-field stamping (**Wisconsin 94f ·
  Harvard 82f · Purdue 87f · Penn 70f · Columbia 60f · Northwestern 59f**), field-echo
  department (USC real-defect 79% one-off; Cornell/Columbia/Penn echo the CIP rollup),
  prefix-doubling (**Yale 70%**), literal "(CIP NN.NN)" (**Penn 11%**), URL-slug leak (USC 19 /
  NYU 8 / UIUC 8 %).
- **Checklist on the 40 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" names on
  the 28 mature catalogs; **all 28 carry 5 campus photos + a live (non-zero) posts feed**. The
  12 five-program seeds remain 5/5 empty-`description_text` + null-`department` + DEAD FEED
  (posts=0); **7 of them have <4 photos** (Florida 1, Emory/Notre Dame 2, UC-Davis/UNC/
  Vanderbilt/WashU 3).

⚠️ **FLAG FOR HUMAN (code, out of grader scope):**
1. `anti_stub.py` is description-FORM-only and still misses, in CODE, what the rulebook now
   prescribes: (a) the **URL-slug pattern** in `machine_artifacts` / `_ARTIFACT_RES`
   (`^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s`), stripped before the share counts (USC + UIUC
   pass CI WHILE leaking it); (b) the §8.5 **STRUCTURE metrics** (dept-echo, rollup, CIP-code,
   concentration-split) — and the rollup metric must use the run-61 federal-taxonomy-ENDING
   anchor, NOT a naive comma-and match that false-flags real degrees; (c) a **peer-signature /
   foreign-unit ALLOWLIST scan** (Purdue #832 auto-merged green with 31 peer rows live — the
   enforced gate cannot see foreign units). USC + UIUC should be removed from `CERTIFIED_CLEAN`
   until the slug leak is stripped. None are grader-editable.
2. Auto-merge dual-head race (SKILL §8.5 step 8.5/5): the single-head assertion evaluates a
   PR's own base, not the post-merge `main`, so two migration PRs off the same base can leave
   `main` dual-headed after auto-merge (e.g. #835 had to merge purduedefab1 + schol1a2b3c4d).
   The durable fix is in the automerge/CI workflow.

---

# CRITICAL — fabricated / contaminated content shipped live (fix before any other deepening)

## 1. Purdue University-Main Campus — peer-signature copy SURVIVED a "repair" + verbatim-across-levels — severity: critical — first seen run 25 · 2026-06-15
310 programs. #832 ("remove peer-institution copy + per-credential rewrite") was a PARTIAL
pass: **31 rows STILL carry peer signatures live** — Chesapeake (JHU) on BA Anthropology,
Writing Seminars (JHU) on BA English, Wharton (Penn) on BS Accounting, CALS (Cornell) on BS
Animal Sciences, Perelman (Penn) on Biochemistry, McCormick (Northwestern) on Engineering
Tech. Structure unchanged: **82% verbatim-across-levels (253/310), 87 shared-body fields, 8%
rollup.** **Repair:** ALLOWLIST-scan every description against Purdue's OWN org chart (NOT a
peer denylist — miss #8 allowlist rule) and FAIL on ANY foreign unit/geography — clearing the
WHOLE class, not the rows a backlog named; research each description from Purdue's own catalog;
give each credential level its own researched body (gold MIT verbatim = 0%).

## 2. URL-slug-leak tier — USC · NYU · UIUC — severity: critical — first seen run 60 · 2026-06-19
A leading kebab-case **catalog/URL slug** bled into `description_text`, live, and invisible to
the built `machine_artifacts` gate (0 of 192 caught) — **USC + UIUC ship it while CERTIFIED_CLEAN**:

| Institution | n | slug-leak rows | % | certified? |
|---|---|---|---|---|
| **University of Southern California** | 613 | 118 | 19% | yes |
| **New York University** | 507 | 41 | 8% | yes |
| **University of Illinois Urbana-Champaign** | 419 | 33 | 8% | yes |

e.g. `"usc-american-studies-and-ethnicity-ba — African American Studies is…"`. **Repair:** strip
the leading `^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s` slug from every description and open on the
field fact (miss #8 build-artifact / §9). The slug is in the source data module, not a render bug.

## 3. Boston University — cross-institution-copy peer signatures + field-echo dept — severity: critical — first seen run 32 · 2026-06-16
376 programs. Descriptions carry another university's units (Perelman/Lick/Medill per prior scans).
Live structure: **dept-echo 81% (213 distinct depts / 376 = one-off per program), shared-body 10f,
cross-field clause 6, concentration-split 10%, rollup 6%.** **Repair:** allowlist-scan every
description against BU's own org chart; research from BU's catalog; real BU school in `department`;
collapse concentration-split rows.

---

# HIGH — real data, structurally broken (rollup · verbatim-across-levels · per-field stamping · field-echo dept · prefix)

## 4. University of Southern California — field-echo dept + concentration-split (+ slug-leak in #2) — severity: high — first seen run 58 · 2026-06-18
613 programs; in `CERTIFIED_CLEAN` (description metrics 0 live) yet **dept-echo-field 79% with 477
distinct departments / 613 rows = one-off per program** (the real owning USC school — Dornsife /
Marshall / Viterbi — named only in the description) + a BA decomposed into "Dramatic Arts, {Emphasis}"
concentration-split rows (4%). **Repair:** put the real USC school/college in `department`; collapse
the emphasis rows into one BA carrying the emphases as `tracks`.

## 5. University of California-Berkeley — severity: high — first seen run 22 · 2026-06-15
269 programs. **33% rollup names + 81% verbatim-across-levels + 82% field-echo dept + 13 cross-field
clauses + 47 shared-body fields.** De-roll-up the federal-CIP names; per-credential researched bodies;
real owning schools in `department`.

## 6. Cornell University — severity: high — first seen run 22 · 2026-06-15
274 programs. **27% rollup + 76% verbatim + 86% dept-echo (dept echoes the CIP rollup, e.g.
"Agriculture, General") + 76 shared-body fields.** De-roll-up the federal-CIP names; per-credential
bodies; real departments.

## 7. Harvard University — severity: high — first seen ≤run 24 · 2026-06-15
343 programs. **30% rollup + 82 shared-body fields + 68% dept-echo.** De-roll-up names; per-credential
bodies; verify the terse "Chemistry"/"Applied Mathematics" depts are the real owning unit (mostly
real — dept-echo heuristic over-count risk) vs a field echo.

## 8. University of Pennsylvania — severity: high — first seen run 24 · 2026-06-15
250 programs. **23% rollup + 11% literal "(CIP NN.NN)" in names + 74% verbatim + 88% dept-echo + 70
shared-body fields.** Strip the CIP codes (miss #2 CIP-code tell); de-roll-up; per-credential bodies;
real departments.

## 9. Columbia University — severity: high — first seen ≤run 24 · 2026-06-15
263 programs. **29% rollup + 88% dept-echo + 60 shared-body fields.** De-roll-up names; per-credential
bodies; real departments.

## 10. Wisconsin (Madison) — per-field stamping (shared leading body) — severity: high — first seen run 60 · 2026-06-19
348 programs. **94 fields where credential siblings share a ≥120-char leading body** (verbatim 0%,
rollup 1% — a suffix-diversifier evades the full-string count, miss #8). Give each credential level
(BA/BS/MS/PhD) its OWN researched body (gold MIT = 0).

## 11. Northwestern University — per-field stamping (shared leading body) — severity: high — first seen run 60 · 2026-06-19
308 programs. **59 fields share a ≥120-char leading body** across credential siblings (verbatim 0%,
rollup 1%). Per-credential researched bodies (gold MIT = 0).

## 12. Yale University — severity: high — first seen ≤run 30 · 2026-06-16
189 programs. **70% prefix-doubling (`description_text.startswith(program_name)`) + 75% dept-echo.**
Strip the name prefix; open on the field fact; per-credential bodies; real departments.

## 13. University of Chicago — severity: high — first seen run 30 · 2026-06-16
103 programs. **50% verbatim + 89% dept-echo + 22 shared-body fields.** Per-credential bodies; real
departments.

## 14. Rice University — severity: high — first seen run 30 · 2026-06-16
159 programs. **43% verbatim + 64% dept-echo + 25 shared-body fields.** Per-credential bodies; verify
departments.

---

# MEDIUM — institution-level seeds: the enrichment backlog (seeding is external)

## 15. The 12 earlier flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Each ships 5 flagship rows with **5/5 empty `description_text` + null `department`** + a **DEAD FEED
(posts=0)**; **7 have <4 campus photos** (Florida 1, Emory/Notre Dame 2, UC-Davis/UNC/Vanderbilt/
WashU 3). **Enrich (per university, one PR):** researched descriptions + real departments for the
flagship rows, a working feed (`posts`>0), a ≥4-photo verified+credited gallery, then deepen toward a
full catalog. Seeds: Florida · Emory · Notre Dame · Vanderbilt · WashU · UNC-Chapel Hill · UC-Davis ·
Brown · Georgetown · UC-Irvine · Dartmouth · UVA.

## 16. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead `posts=0` feed**, and **33 with ZERO
campus photos** (broken explore-card gradient header + detail hero — the acute sub-set to clear
first). **Enrich (per university, one PR):** a full real-named catalog + field-specific descriptions
+ real departments · a working feed · a ≥4-photo verified gallery · reviews on coverable programs ·
`_standard`. Pick the highest-priority (a 0-photo seed) once the CRITICAL/HIGH tiers are clear.

---

# CLEANUP / CLEAN (verify-only)

## Build-artifact tier — UCLA · UW-Seattle · Michigan · Stanford — RESOLVED, re-confirmed run 61
All four de-fabricated live (real per-credential names + real colleges + researched prose);
`machine_artifacts = 0` re-confirmed this run. CERTIFIED_CLEAN. No data repair needed.

## Genuinely clean (desc + structure; no action) — MIT (gold) · UCSD · Caltech · Princeton · CMU · Duke · UT-Austin · Georgia Tech · JHU · NYU(structure) · Michigan · UCLA · UW · Stanford
Verified clean on the description + rollup metrics this run (Michigan/UCLA/UW/UT-Austin/Stanford
rollup CORRECTED to 0–1% from run-60's loose over-count). The dept-echo substring heuristic
OVER-counts on small real-department catalogs (Caltech 88% / Princeton 74% / Harvard 68% / Duke 67% /
Rice 64% — "Chemistry"/"Anthropology" IS the real owning department, not a field echo) — treat as a
heuristic artifact UNLESS a row's `department` is literally the field copied from the name while a real
owning school is separately known (USC = real defect; Princeton/Caltech = not). NYU's structure is
clean (rollup 0% with the federal-taxonomy tell); its only residual is the slug-leak in CRITICAL #2.
