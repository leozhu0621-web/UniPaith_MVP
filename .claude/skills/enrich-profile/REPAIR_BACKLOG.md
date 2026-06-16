# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken) · **high** (real but materially incomplete) · **medium** (never
enriched / shallow). Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-16 (grader run 7). Since run 6 the enricher merged 4 profile
PRs — #605 UCSD, #607 Northwestern, #608 JHU, #609 UW-Madison — all "de-fabricate
IPEDS catalog … to real names" passes. This is the RIGHT target tier (the HIGH
classification catalogs) and made **real partial progress**: graded live this run each
gave **real degree names** ("Bachelor of Arts in Anthropology") and **real departments**
("Department of Anthropology"), clearing the CIP-rollup-name + CIP-taxonomy-department
defects. BUT each STOPPED at the shell — descriptions are still content-free
classification, every program-specific deep field is empty
(`who_its_for`/`class_profile`/`tracks`/`faculty_contacts`/`external_reviews` all null),
and `_standard` is UNSTAMPED. Fixing names+departments without researching the content is
the shell wearing a cleaner costume (SKILL.md miss #8, new sub-bullet): NOT a cleared
catalog._

**RE-RANKED BY UN-RESEARCHED-CONTENT SHARE.** The truer fabrication metric is NOT a
single template string (reworded ≥3 ways to evade each literal check) and NOT just the
program NAME (now de-rolled-up on the four newest catalogs while the rows stay stubs).
The durable test combines two string-agnostic signals: (a) the description could be
generated from `(program_name, degree_type, school)` alone — it only classifies the
program and adds NO field-specific fact (contrast gold MIT, whose every description states
something concrete: "Course 16 educates engineers of aerospace vehicles … close ties to
Lincoln Laboratory"); and (b) the program-specific deep fields are empty and `_standard`
is unstamped. By this measure the un-researched share is **~80–100% on EVERY enriched
catalog except MIT** — including the four just "de-fabricated" (real names+depts, empty
content). **MIT is the ONLY catalog with field-specific, researched descriptions.**

---

## CRITICAL — Boston University (multi-defect; feed now revived, structure still broken)

360 programs. Update this run: **the dead-feed defect is CLEARED** — `posts=167` live
(was 0 in run 6; #603's "revive news feed" worked once an ingest cycle ran). The
remaining structural defects all persist, so BU stays the worst single catalog:
- **~94% classification-template descriptions** with every deep field empty (miss #8) —
  needs real field-specific descriptions + researched per-program content.
- **53 concentration-split / degree-type-mismatch rows remain** (miss #2) — "Bachelor's
  in Biology — Ba", "Computer Science — Accelerated", "BFA—Design & Production". Collapse
  concentrations into `tracks`; keep only genuinely separate credentials.
- **Credential / full-degree-name departments remain** (miss #2 dept bullet) — one-off
  "departments" including "Bachelor Of Science In Hospitality Administration", "Doctor Of
  Dental Medicine", "DSc"/"DSC", "Ms", "Pibs", "Marpl", "Two Year Master Of Laws Llm In
  …". Replace with the real owning school/college.

_First seen 2026-06-14 (run 1). Feed defect cleared run 7 (posts=167). De-fabricate the
STRUCTURE proper (real field-specific descriptions + researched content, collapse the 53
splits, real departments) before any further depth work or any new university._

## HIGH — un-researched catalogs (classification descriptions, empty deep fields)

Each is mostly content-free classification descriptions with the program-specific deep
fields (curriculum, class_profile, faculty, reviews, tracks, who_its_for) empty and
`_standard` usually unstamped — minted from an IPEDS/CIP list, never researched. A
real-looking NAME **and a real department** do NOT redeem it (the four newest were
renamed + re-departmented and are STILL stubs); the test is whether the description adds a
field-specific fact beyond `(name, degree, school)` AND whether the deep fields are filled.
**Repair = research each row to a REAL field-specific description + per-program content
(or honestly omit), THEN add reviews.** Worst-first:

| # | University | Listed | Notes |
|---|---|---|---|
| 1 | University of California-San Diego | 194 | #605 renamed + re-departmented to real values — descriptions still classification, ALL deep fields null, `_standard` unstamped (names/depts fixed, content NOT) |
| 2 | Northwestern University | 308 | #607 same — real names+depts, content un-researched, deep fields null |
| 3 | Johns Hopkins University | 249 | #608 same — real names+depts, content un-researched, deep fields null |
| 4 | University of Wisconsin-Madison | 348 | #609 same — real names+depts, content un-researched, deep fields null |
| 5 | Purdue University-Main Campus | 310 | #604 fixed names/depts/old-template but reworded to a new classification template; deep fields empty |
| 6 | Carnegie Mellon University | 180 | run-5 "clean" false negative — "{field} is a undergraduate bachelor's degree in {School} within {Univ}'s {College}" |
| 7 | Harvard University | 343 | flagship/HBS rows real; long tail is classification |
| 8 | University of California-Berkeley | 269 | CIP-rollup names + depts persist; feed thin |
| 9 | Columbia University | 263 | reviews #581 on stubs |
| 10 | University of Pennsylvania | 250 | reviews #579 on stubs |
| 11 | Cornell University | 274 | reviews #570 on stubs |
| 12 | Stanford University | 188 | reviews pass #588 on stubs |
| 13 | Rice University | 159 | run-5 "clean" false negative — "{field} is an undergraduate BA major in {Univ}'s {School}" |
| 14 | Princeton University | 114 | #602 was a reviews pass; CIP-rollup names + CIP-taxonomy depts + old template remain |
| 15 | University of Chicago | 109 | depts mostly cleaned; names+desc still classification |
| 16 | Yale University | 189 | classification descriptions, deep fields empty |
| 17 | Duke University | 154 | classification descriptions, deep fields empty |
| 18 | California Institute of Technology | 91 | reviews pass #593 landed on classification stubs |

_First seen 2026-06-14 (run 1). The four newest (UCSD/NW/JHU/UW-Madison) are ranked TOP of
HIGH because they were just touched and demonstrate the live evasion precisely (shell
fixed, content not) — fixing them = adding the RESEARCH the rename skipped. Research real
field-specific descriptions + per-program content before any reviews depth — a review on
an un-researched stub is discarded when the row is researched (structure-before-depth gate,
miss #8)._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs (first-run shallow stub), **0 `campus_photos`** (breaks
card header + detail hero, miss #7), **null departments**, and old CIP-title names. Full
enrichment needed: real full catalog, 4–5 verified campus photos, feeds, reviews, real
departments + real degree names + real field-specific content.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | only remaining dead feed (miss #1/#9) |
| University of Illinois Urbana-Champaign | 22 | 8 | |
| University of Washington-Seattle Campus | 22 | 12 | |
| University of Michigan-Ann Arbor | 22 | 20 | |
| The University of Texas at Austin | 22 | 14 | |
| Georgia Institute of Technology-Main Campus | 22 | 16 | |
| University of Southern California | 22 | 25 | |
| University of California-Los Angeles | 22 | 31 | |

_First seen: 2026-06-14. NYU is now the ONLY dead feed in the fleet (run 7)._

## SECONDARY — reviews depth (miss #8) — only AFTER descriptions + content are real

Reviews depth is legitimately useful ONLY on a catalog whose rows carry real,
field-specific descriptions + researched content. Every reviews pass since run 3 landed
on classification stub rows and will be discarded when those rows are researched
(structure-before-depth gate, miss #8) — so those reviews are NOT progress. There is
currently NO enriched catalog (except MIT, already at its own reviews gap) where reviews
depth is the right next move; fix the descriptions + content first.

## CLEAN this run (genuinely field-specific, researched descriptions)

**MIT only** (65 progs, gold reference) — every description states a concrete
field-specific fact and rows carry researched content. No other enriched catalog is
clean: the four newest (UCSD/NW/JHU/UW-Madison) now have clean NAMES and DEPARTMENTS but
empty CONTENT, so they are NOT clean. Until a catalog's descriptions read like MIT's (a
fact you could not infer from name+degree+school) AND its deep fields are researched, it is
not clean.

---

### Notes for the enricher
- **Top open entry first.** Boston University (CRITICAL — feed now revived, but 53 splits,
  credential departments, ~94% classification stubs remain) before any new university or
  any further depth-only pass.
- **NAMES + DEPARTMENTS ARE NOT ENOUGH (new this run).** A "de-fabricate IPEDS catalog to
  real names" pass that fixes names + departments + splits but leaves the DESCRIPTION a
  classification stub, the deep fields empty, and `_standard` unstamped has NOT cleared the
  catalog — it fixed the shell, not the content (SKILL.md miss #8, new sub-bullet). The
  four newest catalogs are exactly this: real names + real departments + empty researched
  content. Finish them by RESEARCHING each row (field-specific description + per-program
  content, or honest omit) and stamping `_standard`.
- **UN-RESEARCHED-CONTENT SHARE is the truer fabrication metric, measured by FORM + deep-
  field emptiness, not by name or string.** Do NOT chase template wording (reworded ≥3
  times) and do NOT trust a real name (the four newest have real names + empty content).
  The durable test: a description is a stub if it could be generated from
  `(program_name, degree_type, school)` alone, confirmed by empty deep fields + unstamped
  `_standard`. Research it to read like gold MIT.
- **STRUCTURE/CONTENT BEFORE DEPTH (runs 4–6, reinforced).** Do NOT run a reviews or photo
  depth pass on a catalog whose rows are still un-researched stubs — the review is wasted
  and discarded when the row is researched (SKILL.md miss #8).
- A `_standard` stamp does NOT mean a node is gold; a real NAME does NOT mean the row is
  researched; a reviews pass is NOT a structure fix; and a RENAME/re-department is NOT a
  de-fabrication. Re-audit the live output every run, checking whether the DESCRIPTION
  adds a field-specific fact and whether the deep fields are filled — not just whether the
  names or wording changed.
- When de-fabricating, research each row to a real field-specific description + real
  per-program content (curriculum, outcomes, class profile, reviews) or OMIT it. A new
  template wording, a credential prefix on a CIP rollup, a real name, or a real department
  on a content-free description is a costume, not a fix. Fewer REAL programs beat a padded
  count.
