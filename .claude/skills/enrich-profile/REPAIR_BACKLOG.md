# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken) · **high** (real but materially incomplete) · **medium** (never
enriched / shallow). Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-14 (grader run 1). UCSD catalog repair shipped 2026-06-14
(ucsdprof2): 194 programs, 0 duplicate names, 0 null departments, 0 template desc._

---

## CRITICAL — fabricated catalogs (CIP × award-level padding, miss #2)

Each program's `program_name` is the bare CIP field title (so cert/BA/MA in one
field share an IDENTICAL name), `department` is **null**, and the description is a
degree-type template (`"{field} — a {Univ} {degree_type} program offered through
{school}"`). Real-program count is a small fraction of the listed total. **Repair =
resolve each CIP row to its real, per-degree, named program(s) with a real
department + field-specific description, or drop it.** Reviews are ~0–1/20 on these
(secondary — do not write reviews for stub rows; fix the catalog first).

Ranked by % padded (worst first):

| # | University | Listed progs | % padded | Notes |
|---|---|---|---|---|
| ~~1~~ | ~~University of California-San Diego~~ | ~~194~~ | ~~**97%**~~ | **REPAIRED 2026-06-14** (ucsdprof2) — credential-disambiguated names + departments |
| 1 | Purdue University-Main Campus | 310 | **95%** | merged #523 — 294 template, 300 null dept, 255 dup; posts=10 |
| 2 | Johns Hopkins University | 249 | **94%** | merged #521 — 235 template, 239 null dept, 213 dup |
| 3 | Northwestern University | 308 | **94%** | merged #522 — 291 template, 297 null dept, 260 dup |
| 4 | Columbia University | 263 | **89%** | 233 template, 263 null dept, 188 dup |
| 5 | Stanford University | 188 | **84%** | + **posts=0** (dead feed, miss #9) — 158 template, 188 null dept |
| 6 | University of California-Berkeley | 269 | **84%** | 170 template, 269 null dept, 226 dup |
| 7 | Princeton University | 119 | **82%** | 97 template, 119 null dept, 98 dup |
| 8 | University of Chicago | 124 | **81%** | 101 template, 124 null dept, 56 dup |
| 9 | Harvard University | 353 | **80%** | 281 template, 353 null dept, 249 dup |
| 10 | Cornell University | 275 | **77%** | 158 template, 275 null dept, 213 dup |
| 11 | University of Pennsylvania | 251 | **76%** | 167 template, 251 null dept, 191 dup |
| 12 | California Institute of Technology | 91 | **63%** | 57 template, 91 null dept, 48 dup |

_First seen: 2026-06-14._

## CRITICAL — Boston University (bare-abbreviation stub catalog, still live)

483 programs: **323 named just "BA"/"BS"/"MS"/"PhD"** etc., 436 duplicate names,
478 with `department == "Programs"`, boilerplate descriptions; **posts=0**. PR #520
claimed to enrich BU "to gold — 483-program catalog" but the catalog is the junk it
was supposed to replace (verify-rendered-output failure, miss #9). Clean to real
field-specific named programs with real departments, or shrink to the real catalog.
_First seen: 2026-06-14 (long-standing; named in SKILL.md as prior #1 target)._

## HIGH — null-department catalogs (partial padding)

| University | Listed progs | Issue |
|---|---|---|
| Yale University | 189 | 189 null `department`, 72 dup names (no template desc — names look real but undept'd) |
| Duke University | 154 | 154 null `department`, 38 dup names |

`department` is null on every program → owning-school grouping is broken on the page.
Backfill the real owning school/department per program. _First seen: 2026-06-14._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs (first-run shallow stub), **0 `campus_photos`** (breaks
card header + detail hero, miss #7), and null departments. Full enrichment needed:
real catalog, 4–5 verified campus photos, feeds, reviews, departments.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | dead feed too |
| Georgia Institute of Technology-Main Campus | 22 | 15 | |
| The University of Texas at Austin | 22 | 12 | |
| University of California-Los Angeles | 22 | 29 | |
| University of Illinois Urbana-Champaign | 22 | 7 | |
| University of Michigan-Ann Arbor | 22 | 10 | |
| University of Southern California | 22 | 23 | |
| University of Washington-Seattle Campus | 22 | 11 | |
| University of Wisconsin-Madison | 22 | 10 | |

_First seen: 2026-06-14._

## CLEAN this run (no catalog padding detected)

Carnegie Mellon (180), Rice (159), MIT (65, gold reference). Real departments, 0
duplicate/template stubs. (Reviews depth still per-program-verifiable, but the
catalogs themselves are sound.)

---

### Notes for the enricher
- **Top open entry first.** Purdue (CRITICAL #1) before any new university.
- A `_standard` stamp does NOT mean a node is gold — every padded catalog above is
  stamped. Re-audit the live output (SKILL.md step 2 re-audit clause).
- The padding came from reading "full IPEDS/Scorecard catalog" as "one row per
  CIP × award-level." That count is an upper-bound HINT, not a minting recipe
  (SKILL.md miss #2). Fewer REAL programs beat a padded total.
