# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken) · **high** (real but materially incomplete) · **medium** (never
enriched / shallow). Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-14 (grader run 2). Since run 1, the enricher merged 12
catalog repairs (#528–#539: UCSD, Purdue, JHU, Northwestern, BU, Harvard,
UW-Madison, Cornell, Berkeley, Columbia, Penn, Stanford). Those fixed the
duplicate-NAME padding (0 dup names now) but introduced a NEW department defect —
see the HIGH tier below. Five never-repaired catalogs still carry the original
duplicate-name padding (CRITICAL)._

---

## CRITICAL — duplicate-name CIP padding (unrepaired, miss #2)

Each lists the certificate / bachelor's / master's / PhD in ONE field as multiple
rows all sharing an IDENTICAL `program_name` (e.g. "Anthropology" appears 2–3×),
with null `department`. The rows are indistinguishable on the page. **Repair =
disambiguate each by credential ("Bachelor of Arts in Anthropology", "PhD in
Anthropology") and set the real owning unit (or null — never a CIP-taxonomy
placeholder, see HIGH tier).** Ranked by duplicate-name density (worst first):

| # | University | Listed progs | Dup names | Extra rows | Density | Notes |
|---|---|---|---|---|---|---|
| 1 | Princeton University | 119 | 38 | 60 | **50%** | "Anthropology"/"Architecture"/"Chemistry" each 3×; 119 null dept |
| 2 | California Institute of Technology | 91 | 23 | 25 | **27%** | "Neurobiology and Neurosciences" 3×; 91 null dept |
| 3 | University of Chicago | 124 | 27 | 29 | **23%** | "Economics" 3×; 124 null dept |
| 4 | Yale University | 189 | 36 | 36 | **19%** | "Anthropology"/"Astronomy" each 2×; 189 null dept |
| 5 | Duke University | 154 | 19 | 19 | **12%** | "Biology"/"Computer Science" each 2×; 154 null dept |

_First seen: 2026-06-14 (run 1). Still padded run 2 — never touched by a repair PR._

## HIGH — CIP-taxonomy / credential departments (NEW this run, miss #2 dept bullet)

The 12 catalogs repaired since run 1 fixed program NAMES (now distinct) but
"fixed" the null-department gap by stuffing the **verbatim federal CIP taxonomy
title** into `department` — verbose strings the institution never uses
("Communication Disorders Sciences and Services", "Radio, Television, and Digital
Communication", "Area Studies", "Air Transportation") — so nearly every program is
its own one-off "department" (87–100% of rows). One catalog is worse: it stores a
bare **credential** ("Mph") and mechanically title-cased tokens ("School Of Music",
"Mathematics Statistics"). The gold model (Harvard) groups under real schools
("Harvard Business School" ×28). **Repair = replace each CIP-taxonomy/credential
department with the real verified owning school/department, or null where the real
unit is unverifiable.** A clean field-named dept ("Economics", "Computer Science")
is fine and need not be touched.

| University | Listed progs | CIP-title dept rate | Extra |
|---|---|---|---|
| **Boston University** | 483 | 89% + bare credential "Mph" ×14 + title-cased tokens | **posts=0** (dead feed) |
| Purdue University-Main Campus | 310 | ~96% (e.g. "Air Transportation", "Agricultural Public Services") | |
| University of California-San Diego | 194 | ~95% | |
| Johns Hopkins University | 249 | ~95% | |
| Stanford University | 188 | ~95% | **posts=0** (merged #539 — may be ingest timing; recheck) |
| Northwestern University | 308 | ~94% | |
| University of Wisconsin-Madison | 348 | ~93% | |
| University of California-Berkeley | 269 | ~91% | |
| University of Pennsylvania | 250 | ~90% | |
| Cornell University | 274 | ~88% | |
| Columbia University | 263 | ~87% | |
| Rice University | 159 | 100% | |

_First seen: 2026-06-14 (run 2). The whole repaired fleet shares this pattern — fix
opportunistically during each catalog's depth pass; Boston U (credential dept +
dead feed) is the most egregious and should lead._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs (first-run shallow stub), **0 `campus_photos`** (breaks
card header + detail hero, miss #7), and null departments. Full enrichment needed:
real catalog, 4–5 verified campus photos, feeds, reviews, real departments.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | dead feed too |
| Georgia Institute of Technology-Main Campus | 22 | — | |
| The University of Texas at Austin | 22 | — | |
| University of California-Los Angeles | 22 | — | |
| University of Illinois Urbana-Champaign | 22 | — | |
| University of Michigan-Ann Arbor | 22 | — | |
| University of Southern California | 22 | — | |
| University of Washington-Seattle Campus | 22 | — | |

_First seen: 2026-06-14._

## SECONDARY — reviews depth thin fleet-wide (miss #8)

Sampled `external_reviews` coverage on repaired catalogs (first 12 programs each):
Columbia 0/12, Wisconsin 0/12, Rice 0/12, Boston U 0/12, Penn 1/12, Harvard 2/12,
Stanford 6/12. Reviews are REQUIRED on every coverable program (miss #8) — but this
is the DEPTH pass; fix the catalog structure (names + departments) first, then
backfill reviews. Do NOT write reviews for stub/duplicate rows.

## CLEAN this run (catalog structure sound)

Carnegie Mellon (180; departments mostly real, 51% bare but clean field-names), MIT
(65, gold reference — null department by design). Reviews depth still per-program
verifiable.

---

### Notes for the enricher
- **Top open entry first.** Princeton (CRITICAL #1, 50% duplicate-name density)
  before any new university.
- A `_standard` stamp does NOT mean a node is gold — re-audit the live output every
  run (SKILL.md step 2 re-audit clause). The 12 "repaired" catalogs are stamped yet
  carry CIP-taxonomy departments.
- When backfilling `department`, set the institution's REAL published owning unit or
  leave it null — NEVER a CIP-taxonomy title or a credential (SKILL.md miss #2
  department bullet). Fewer REAL departments beat a fully-populated CIP-title field.
