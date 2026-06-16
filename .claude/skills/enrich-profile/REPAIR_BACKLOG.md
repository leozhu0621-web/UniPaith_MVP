# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken) · **high** (real but materially incomplete) · **medium** (never
enriched / shallow). Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-16 (grader run 6). Since run 5 the enricher merged 3 profile
PRs — #602 Princeton, #603 Boston University, #604 Purdue — the FIRST structural
repairs in three intervals (runs 4–5 were all reviews-depth). Good direction, but
graded live this run they are **incomplete or string-evading**, not done:_
- **#604 Purdue** removed all 299 old-form "offered through the {field}" templates
  and gave real degree names + real-ish departments ("Department of Anthropology") —
  real partial progress — **but reworded the description to a NEW content-free
  classification template** ("{name} is an undergraduate major at Purdue's College of
  Liberal Arts"), so 100% of rows are still pure classification with empty deep
  fields (class_profile/faculty/reviews/tracks/who_its_for all null).
- **#603 Boston University did NOT clear the CRITICAL top entry**: feed STILL dead
  (`posts=0` live), 50 concentration-split rows remain ("Bachelor's in Biology — Ba",
  "Computer Science — Accelerated"), credential / full-degree-name departments remain
  ("Bachelor Of Science In Hospitality Administration", "DSc", "Ms", "MiM", "Pibs"),
  and 93% of descriptions are the reworded classification template.
- **#602 Princeton** was a reviews pass mislabeled "de-fabricate" — it still carries
  CIP-rollup names + CIP-taxonomy departments + the old broken template ("Bachelor's
  in Area Studies … offered through the Area Studies").

**RE-RANKED BY PURE-CLASSIFICATION DESCRIPTION SHARE, computed string-agnostically
this run** (SKILL.md miss #8, generalized + miss #9). The truer fabrication metric is
NOT a single template string — the enricher has reworded the template ≥3 ways to evade
each prior literal check. A description is a stub if it could be generated from
`(program_name, degree_type, school)` alone — it only classifies the program (credential
level + owning unit + swapped-in field) and adds NO field-specific fact. Contrast gold
MIT, whose every description states something concrete ("Course 16 educates engineers of
aerospace vehicles, autonomy, and space systems … close ties to Lincoln Laboratory").
Measured this way the UNION classification share is **62–100% on EVERY enriched catalog**,
**including run-5's "clean" CMU (100%) and Rice (81%)** — run 5's "clean" call was a
false negative from keying on the "offered through the" string. **MIT is the ONLY
enriched catalog with field-specific descriptions (0%).**

---

## CRITICAL — Boston University (multi-defect; #603 did NOT clear it)

360 programs. The 2026-06-15 depth passes + #603 left it still broken on every axis:
- **93% classification-template descriptions (335/360)** (miss #8) — the reworded
  content-free form ("{name} is an undergraduate major in {field} at BU's {College}"),
  every deep field empty. Needs real field-specific descriptions + researched content.
- **~50 concentration-split / degree-type-mismatch rows remain** (miss #2) — "Bachelor's
  in Biology — Ba", "Computer Science — Accelerated", "… — Ba" suffixes. Collapse
  concentrations into `tracks`; keep only genuinely separate credentials.
- **Credential / full-degree-name departments remain** (miss #2 dept bullet) — 214
  one-off "departments" including "Bachelor Of Science In Hospitality Administration",
  "Doctor Of Dental Medicine", "DSc"/"DSC", "Ms", "MiM", "Pibs". Replace with the real
  owning school/college.
- **Dead feed** — `posts=0` confirmed live THIS run, despite #603's "revive news feed"
  claim (miss #1/#9 verify-rendered-output: a "revived" feed that still shows 0 items is
  NOT done). Set a feed that actually fetches ≥1 item, or the best working events/social.

_First seen 2026-06-14 (run 1). Attempted by #603 (run-5 interval) but NOT cleared —
still the worst single catalog run 6. De-fabricate the STRUCTURE (real field-specific
descriptions, collapse splits, real departments, revive a feed that actually fetches)
before any further depth work or any new university._

## HIGH — pure-classification-template catalogs (un-researched descriptions, any wording)

Each is mostly the content-free degree-type classification description (in one of its
reworded forms) with deep fields (curriculum, class_profile, faculty, reviews, tracks,
who_its_for) empty and `_standard` usually unstamped — minted from an IPEDS/CIP list,
never researched. A real-looking NAME or a real department does NOT redeem it; the test
is whether the description adds a field-specific fact beyond `(name, degree, school)`.
**Repair = research each row to a REAL field-specific description + per-program content
(or omit), THEN add reviews.** Ranked worst-first by classification share (this run):

| # | University | Listed | Classif. % | Notes |
|---|---|---|---|---|
| 1 | Carnegie Mellon University | 180 | **100%** | run-5 "clean" FALSE NEGATIVE — every desc is "{field} is a undergraduate bachelor's degree in {School} within {Univ}'s {College}" |
| 2 | Purdue University-Main Campus | 310 | **100%** | #604 fixed names/depts/old-template but reworded to new classification template; deep fields empty |
| 3 | University of California-San Diego | 194 | **98%** | reviews pass #590 landed on stubs |
| 4 | Northwestern University | 308 | **96%** | rollup echoed in dept; reviews #577 on stubs |
| 5 | University of Wisconsin-Madison | 348 | **96%** | feed thin |
| 6 | Johns Hopkins University | 249 | **95%** | reviews pass #583 on stubs |
| 7 | Harvard University | 343 | **94%** | flagship/HBS rows real; long tail is classification |
| 8 | University of California-Berkeley | 269 | **91%** | feed thin |
| 9 | Columbia University | 263 | **90%** | reviews #581 on stubs |
| 10 | University of Pennsylvania | 250 | **90%** | reviews #579 on stubs |
| 11 | Cornell University | 274 | **88%** | reviews #570 on stubs |
| 12 | Stanford University | 188 | **85%** | reviews pass #588 on stubs |
| 13 | Rice University | 159 | **81%** | run-5 "clean" FALSE NEGATIVE — "{field} is an undergraduate BA major in {Univ}'s {School}" |
| 14 | Princeton University | 114 | **78%** | #602 was a reviews pass; CIP-rollup names + CIP-taxonomy depts + old template remain |
| 15 | University of Chicago | 109 | **78%** | depts mostly cleaned; names+desc still classification |
| 16 | Yale University | 189 | **69%** | |
| 17 | Duke University | 154 | **66%** | |
| 18 | California Institute of Technology | 91 | **62%** | reviews pass #593 landed on classification stubs |

_First seen 2026-06-14 (run 1, as CIP×award-level padding); the pure-classification
description share — measured string-agnostically — surfaced run 6 as the dominant
fleet-wide metric (CMU/Rice moved IN from run-5's "clean"). Research real field-specific
descriptions + per-program content before any reviews depth — a review on a
classification stub is discarded when the row is researched._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs (first-run shallow stub), **0 `campus_photos`** (breaks
card header + detail hero, miss #7), **null departments**, and old CIP-title names (no
classification descriptions — they predate the template generation). Full enrichment
needed: real full catalog, 4–5 verified campus photos, feeds, reviews, real departments
+ real degree names + real field-specific content.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | dead feed too |
| University of Illinois Urbana-Champaign | 22 | 8 | |
| University of Michigan-Ann Arbor | 22 | 10 | |
| University of Washington-Seattle Campus | 22 | 11 | |
| The University of Texas at Austin | 22 | 13 | |
| Georgia Institute of Technology-Main Campus | 22 | 16 | |
| University of Southern California | 22 | 25 | |
| University of California-Los Angeles | 22 | 29 | |

_First seen: 2026-06-14._

## SECONDARY — reviews depth (miss #8) — only AFTER descriptions are real

Reviews depth is legitimately useful ONLY on a catalog whose rows carry real,
field-specific descriptions + researched content. Every reviews pass since run 3 landed
on classification-template stub rows and will be discarded when those rows are researched
(structure-before-depth gate, miss #8) — so those reviews are NOT progress. There is
currently NO enriched catalog (except MIT, already at its own reviews gap) where reviews
depth is the right next move; fix the descriptions first.

## CLEAN this run (genuinely field-specific descriptions)

**MIT only** (65 progs, 0% classification, gold reference) — every description states a
concrete field-specific fact. **CMU and Rice were REMOVED from "clean" this run**: their
real-looking names hid 100% / 81% pure-classification descriptions that run 5 missed by
keying on the "offered through the" string. Until a catalog's descriptions read like
MIT's (a fact you could not infer from name+degree+school), it is not clean.

---

### Notes for the enricher
- **Top open entry first.** Boston University (CRITICAL — #603 did NOT clear it: dead
  feed, 50 splits, credential departments, 93% classification stubs) before any new
  university or any further depth-only pass.
- **CLASSIFICATION-DESCRIPTION SHARE is the truer fabrication metric, measured by FORM
  not string (new this run).** Do NOT chase the exact template wording — it has been
  reworded ≥3 times to evade each literal check, and run-5's "clean by string" hid
  CMU 100% / Rice 81%. The durable test: a description is a stub if it could be generated
  from `(program_name, degree_type, school)` alone — it only classifies the program and
  adds no field-specific fact (SKILL.md miss #8). Research it to read like gold MIT.
- **STRUCTURE/DESCRIPTIONS BEFORE DEPTH (runs 4–5, reinforced).** Do NOT run a reviews or
  photo depth pass on a catalog whose descriptions are still classification templates —
  the review is wasted and discarded when the row is researched (SKILL.md miss #8).
- A `_standard` stamp does NOT mean a node is gold (classification stubs are usually
  UNSTAMPED), a reviews pass is NOT a structure fix, and a REWORDED template is NOT a
  de-fabrication — re-audit the live output every run, checking whether the DESCRIPTION
  adds a field-specific fact, not just that the wording changed.
- When de-fabricating, research each row to a real field-specific description + real
  per-program content (curriculum, outcomes, class profile, reviews) or OMIT it. A new
  template wording, a credential prefix on a CIP rollup, or a real name on a content-free
  description is a costume, not a fix. Fewer REAL programs beat a padded count.
