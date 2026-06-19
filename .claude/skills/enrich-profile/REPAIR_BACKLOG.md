# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before deepening any
other university (repair-first, SKILL.md §2). This is the ONLY file where specific
schools appear. Severity: **critical** (fabricated / cross-contaminated / build-junk text
shipped live — peer-signature copies / URL-slug leaks / namesake-scrapes) · **high** (real
data but materially broken structure — rollup names / verbatim-across-levels / prefix-
doubling / field-echo departments) · **medium** (institution-level seed below gold).
Evidence is from the live API (`api.unipaith.co/api/v1`), measured with the repo's own
`profile_standard/anti_stub.py` analyzer + structure heuristics.

_Last graded: 2026-06-19 (grader **run 60** — **FULL-FLEET sweep: all 300 LIVE institutions
re-measured** via the live API; all 40 catalogs with programs scanned across every
description + structure dimension). **1 rule change**: extended the miss-#8 build-artifact
"leading internal token" tell (and the §9 pre-ship scan) to ALSO catch a **leading
kebab-case URL SLUG** in `description_text` — the live build-junk tell this run, 192 rows
across 3 catalogs (2 of them CERTIFIED_CLEAN), 0 caught by `machine_artifacts`. See
CHANGELOG run 60._

## Fleet at a glance (run 60, live `api.unipaith.co/api/v1`)

- **Fleet = 300 institutions LIVE** (the #813 bulk-seed added ~150 more on top of run-59's
  150). **40 carry programs; 260 are bare institution-level stubs** (0 programs, dead
  `posts=0` feed, 33 with ZERO campus photo). Seeding is **external**; the routine ENRICHES
  + REPAIRS only — these 260 stubs are the enrichment backlog.
- **🟢 HEADLINE WIN — the run-59 CRITICAL build-artifact-assembly tier is FULLY RESOLVED
  live.** UCLA, UW-Seattle, Michigan, and Stanford each shipped ~98% "Catalog entry <hex>:"
  + division-frame + namesake junk last run; all four are now **de-fabricated live** (real
  per-credential names, real owning departments/colleges, field-specific researched prose,
  **0 build artifacts**) and all four sit in `CERTIFIED_CLEAN`. Verified row-by-row on the
  live API. The repair model (UW/Michigan/UCLA/Stanford regenerated from verified sources)
  worked.
- **🔴 NEW (drives the run-60 rule): a leading URL-SLUG leak in description prose, live on
  CERTIFIED_CLEAN catalogs.** USC (118 rows / 19%), NYU (41 / 8%), UIUC (33 / 8%) ship
  descriptions that OPEN with the program's kebab-case catalog slug
  (`"usc-american-studies-and-ethnicity-ba — African American Studies is…"`). It is a
  build artifact leaked to the page — and it is **invisible to the built `machine_artifacts`
  gate** (no "Catalog entry" string, no hex run), so **USC + UIUC carry it while
  CERTIFIED_CLEAN**. 0 of 192 caught. Same class as the hex nonce; the rulebook now
  enumerates the slug form (miss #8 + §9), and the gate needs it (human-flag).
- **Mature-catalog structure tiers persist (documented classes):** cross-institution-copy
  peer signatures (**Purdue 52 rows live** — Chesapeake/SAS/Writing Seminars), rollup-name
  (Berkeley 37 / Harvard 34 / Columbia 33 / Cornell 32 / Penn 26 %), verbatim-across-levels
  (Purdue 82 / Berkeley 81 / Cornell 76 / Penn 74 / UChicago 50 / Rice 43 %), shared-leading-
  body / per-field stamping (**Wisconsin 94f, Harvard 82f, Northwestern 59f** — Wisconsin +
  Northwestern were MIS-GRADED "clean" in run 59), field-echo department (USC/Columbia/Penn/
  Cornell/Berkeley — real-defect where one-off + real school hidden in desc), prefix-doubling
  (Yale 70 %), literal "(CIP NN.NN)" (Penn 11 %).
- **Checklist on the 40 catalogs:** 0 duplicate / 0 bare-abbreviation / 0 "Programs" names on
  the 28 mature catalogs; all 28 carry 5 campus photos + a non-zero feed. The 12 five-program
  seeds remain 5/5 empty-`description_text` + null-`department`; 7 of them have <4 photos.

⚠️ **FLAG FOR HUMAN (code, out of grader scope):**
1. `anti_stub.py` is description-FORM-only and was defeated AGAIN this run by the URL-slug
   form. It needs (a) the **URL-slug pattern** added to `machine_artifacts` / `_ARTIFACT_RES`
   (`^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s`) and stripped before the share counts; (b) the
   STRUCTURE metrics §8.5 has prescribed since run 58 but that are STILL unbuilt (dept-echo,
   rollup, CIP-code, concentration-split); (c) **USC + UIUC removed from `CERTIFIED_CLEAN`**
   until the slug leak is stripped (otherwise a re-leak re-passes CI). None are grader-editable.
2. Auto-merge dual-head race (SKILL §8.5 step 8.5/5): the single-head assertion evaluates a
   PR's own base, not the post-merge `main`, so two migration PRs off the same base can leave
   `main` dual-headed after auto-merge. The durable fix is in the automerge/CI workflow.

---

# CRITICAL — fabricated / contaminated / build-junk content shipped live (fix before any other deepening)

## 1. Purdue University-Main Campus — cross-institution-copy peer signatures + verbatim-across-levels — severity: critical — first seen run 25 · 2026-06-15
310 programs. #661's descriptions were COPIED from peer catalogs + find-replaced and the peer
signatures SURVIVE live: **52 rows carry "Chesapeake" (JHU), "SAS"/"Writing Seminars" (JHU/Penn),
"Perelman"** — e.g. "Bachelor of Arts in Anthropology" → Chesapeake, BA English → Writing Seminars.
Live structure: **82% verbatim-across-levels, 87 shared-body fields, 10% rollup names.**
**Repair:** research each description from Purdue's OWN catalog; ALLOWLIST-scan every description
against Purdue's own org chart (NOT a peer denylist — miss #8 allowlist rule) and FAIL on any
foreign unit/geography; give each credential level its own researched body.

## 2. URL-slug-leak tier — USC · NYU · UIUC — severity: critical — first seen run 60 · 2026-06-19
A leading kebab-case **catalog/URL slug** bled into `description_text`, live, and invisible to the
built `machine_artifacts` gate (0 of 192 caught) — **USC + UIUC ship it while CERTIFIED_CLEAN**:

| Institution | n | slug-leak rows | % | certified? |
|---|---|---|---|---|
| **University of Southern California** | 613 | 118 | 19% | yes |
| **New York University** | 507 | 41 | 8% | yes |
| **University of Illinois Urbana-Champaign** | 419 | 33 | 8% | yes |

e.g. `"usc-american-studies-and-ethnicity-ba — African American Studies is…"`,
`"anthropology-classical-civilization — The Department of Anthropology…"`,
`"uiuc-agricultural-biological-engineering-bs — …"`. **Repair:** strip the leading
`^[a-z0-9]+(-[a-z0-9]+){2,}\s*[—–-]\s` slug from every description and open on the field fact
(miss #8 build-artifact / §9). The slug is in the source data module, not a render bug.

## 3. Boston University — cross-institution-copy peer signatures + field-echo dept — severity: critical — first seen run 32 · 2026-06-16
376 programs. #675's descriptions carry another university's units (Perelman/Lick/Medill per prior
scans). Live structure: **dept-echo 80%, shared-body 10f, cross-field clause 6, rollup 6%.**
**Repair:** allowlist-scan every description against BU's own org chart; research from BU's catalog;
real BU school in `department`; collapse concentration-split rows.

---

# HIGH — real data, structurally broken (rollup · verbatim-across-levels · per-field stamping · field-echo dept · prefix)

## 4. University of Southern California — field-echo dept + concentration-split (+ slug-leak in #2) — severity: high — first seen run 58 · 2026-06-18
613 programs; in `CERTIFIED_CLEAN` (description metrics 0 live) yet **dept-echo 79% with 477
distinct departments / 613 rows = one-off per program** (the real owning USC school — Dornsife /
Marshall / Viterbi — named only in the description) + a BA decomposed into "Dramatic Arts, {Emphasis}"
concentration-split rows. **Repair:** put the real USC school/college in `department`; collapse the
emphasis rows into one BA carrying the emphases as `tracks`.

## 5. University of California-Berkeley — severity: high — first seen run 22 · 2026-06-15
269 programs. **37% rollup names + 81% verbatim-across-levels + 82% field-echo dept + 13 cross-field
clauses.** De-roll-up the federal-CIP names; per-credential researched bodies; real owning schools in
`department`.

## 6. Harvard University — severity: high — first seen ≤run 24 · 2026-06-15
343 programs. **34% rollup + 68% dept-echo + 82 shared-body fields.** De-roll-up names; per-credential
bodies; verify the terse "Chemistry"/"Applied Mathematics" depts are the real owning unit (mostly
real — over-count risk) vs a field echo.

## 7. Cornell University — severity: high — first seen run 22 · 2026-06-15
274 programs. **32% rollup + 76% verbatim + 86% dept-echo (dept echoes the CIP rollup, e.g.
"Agriculture, General").** De-roll-up the federal-CIP names; per-credential bodies; real departments.

## 8. University of Pennsylvania — severity: high — first seen run 24 · 2026-06-15
250 programs. **26% rollup + 11% literal "(CIP NN.NN)" in names + 74% verbatim + 88% dept-echo.**
Strip the CIP codes (miss #2 CIP-code tell); de-roll-up; per-credential bodies; real departments.

## 9. Columbia University — severity: high — first seen ≤run 24 · 2026-06-15
263 programs. **33% rollup + 88% dept-echo + 60 shared-body fields.** De-roll-up names; per-credential
bodies; real departments.

## 10. Wisconsin (Madison) — per-field stamping (shared leading body) — severity: high — first seen run 60 · 2026-06-19
348 programs. **94 fields where credential siblings share a ≥120-char leading body** (verbatim 0%,
so a suffix-diversifier evades the full-string count — miss #8). Run-59 graded Wisconsin "clean"; it
is NOT. Give each credential level (BA/BS/MS/PhD) its OWN researched body.

## 11. Northwestern University — per-field stamping (shared leading body) — severity: high — first seen run 60 · 2026-06-19
308 programs. **59 fields share a ≥120-char leading body** across credential siblings (verbatim 0%).
Also mis-graded "clean" in run 59. Per-credential researched bodies (gold MIT = 0).

## 12. Yale University — severity: high — first seen ≤run 30 · 2026-06-16
189 programs. **70% prefix-doubling (`description_text.startswith(program_name)`) + 75% dept-echo.**
Strip the name prefix; open on the field fact; per-credential bodies; real departments.

## 13. University of Chicago — severity: high — first seen run 30 · 2026-06-16
103 programs. **50% verbatim + 89% dept-echo.** Per-credential bodies; real departments.

## 14. Rice University — severity: high — first seen run 30 · 2026-06-16
159 programs. **43% verbatim + 64% dept-echo.** Per-credential bodies; verify departments.

---

# MEDIUM — institution-level seeds: the enrichment backlog (seeding is external)

## 15. The 12 earlier flagship seeds (5 programs each) — severity: medium — first seen run 57 · 2026-06-18
Each ships 5 flagship rows with **5/5 empty `description_text` + null `department`** + a dead feed;
**7 have <4 campus photos** (Florida 1, Emory/Notre Dame 2, UC-Davis/UNC/Vanderbilt/WashU 3). Florida
also mis-credentials Law. **Enrich (per university, one PR):** researched descriptions + real
departments for the flagship rows, a working feed (`posts`>0), a ≥4-photo verified+credited gallery,
then deepen toward a full catalog. Seeds: Florida · Emory · Notre Dame · Vanderbilt · WashU ·
UNC-Chapel Hill · UC-Davis · Brown · Georgetown · UC-Irvine · Dartmouth · UVA.

## 16. The ~260 bulk institution-level seeds (0 programs) — severity: medium — first seen run 59/60
Each entered at institution level with **0 programs, a dead `posts=0` feed**, and **33 with ZERO
campus photos** (broken explore-card gradient header + detail hero — the acute sub-set to clear
first). **Enrich (per university, one PR):** a full real-named catalog + field-specific descriptions
+ real departments · a working feed · a ≥4-photo verified gallery · reviews on coverable programs ·
`_standard`. Pick the highest-priority (a 0-photo seed) once the CRITICAL/HIGH tiers are clear.

---

# CLEANUP / CLEAN (verify-only)

## Stanford University — build-artifact tier RESOLVED — first seen ≤run 24 — RESOLVED run 60
stanfordprof11 de-fabricated live: 178 programs, real degree names, real `Department of {field}`
departments, field-specific researched descriptions, **0 build artifacts, rollup 1%**, CERTIFIED_CLEAN.
The old fabricated-unit / synthesized-review claims predate the full regeneration — no data repair
needed; a final fabricated-unit re-scan is the only residual.

## UCLA · UW-Seattle · Michigan — build-artifact tier RESOLVED — first seen run 59 — RESOLVED run 60
All three de-fabricated live (real per-credential names + real colleges + researched prose, 0
artifacts) and CERTIFIED_CLEAN. No data repair needed.

## Genuinely clean (desc + structure; no action) — MIT (gold) · UCSD · Caltech · Princeton · CMU · Duke · UT-Austin · Georgia Tech · JHU · NYU(structure)
Verified clean on the description metrics this run. The dept-echo substring heuristic OVER-counts on
small real-department catalogs (Caltech 88% / Princeton 74% / Harvard 68% / Duke 67% / Rice 64% —
"Chemistry"/"Anthropology" IS the real owning department, not a field echo) — treat as a heuristic
artifact UNLESS a row's `department` is literally the field copied from the name while a real owning
school is separately known (USC = real defect; Princeton/Caltech = not). NYU's structure is clean; its
only residual is the slug-leak in CRITICAL #2.
