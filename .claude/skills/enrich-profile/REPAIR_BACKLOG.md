# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken / fabricated data shipped live) · **high** (real but materially
incomplete) · **medium** (never enriched / shallow). Evidence is from the live API
(`api.unipaith.co/api/v1`).

_Last graded: 2026-06-16 (grader run 15). **ONE new profile-enrichment PR merged since run 14's
grader: Princeton #641** ("catalog structural repair — field-specific descriptions for 41
programs") + a follow-up test-align commit `1057be7`. The other 27 catalogs are byte-identical to
run 14 (re-confirmed live: Northwestern n=308 rollup~1% / "Architecture and Related Services, Other"
CIP-rollup review STILL LIVE; Duke n=154 Pratt boilerplate reviews STILL LIVE; gold MIT n=65 6% /
**2%**; NYU still the ONLY dead feed `posts=[]`; 28 institutions, no sprawl)._

**REAL PROGRESS — Princeton #641 is the FIRST genuinely CLEAN structural de-fabrication (but NOT
yet live — its deploy FAILED, see below).** In the data module it drops 73 federal certificate /
incidental-master's padding rows (114→41), replaces every CIP-prefix name with a real degree title
("Bachelor of Arts in Anthropology", "Master of Public Affairs (MPA)"), gives every row a real
owning department, and writes field-specific descriptions that name ONLY real Princeton units
(PACM, ORFE, SEAS, Frick Chemistry Laboratory, Peyton Hall, High Meadows Environmental Institute,
Andlinger Center) — ZERO rollup names, ZERO CIP-prefix names, ZERO prefix-doubling, ZERO
foreign/mismatched units. It is the first non-MIT catalog to satisfy the dimension-agnostic clear
bar on structure AND apply the run-13/14 named-unit-truth lesson. Verify once it deploys.

**NEW rulebook gap closed this run (SKILL.md miss #2, new sub-bullet): a stale catalog-breadth GATE
BLOCKED the de-fabrication deploy.** Princeton's own profile-standard test asserted
`assert len(PROGRAMS) >= 100` (a row count frozen to the OLD padded catalog). The correct
de-fabrication to 41 real rows tripped it → **Deploy Backend run 27654099686 FAILED** (the migration
+ data never reached production), so the LIVE Princeton is STILL the old 114-row padded catalog
(rollup names, classification-template descriptions, empty deep fields) until a re-deploy lands. The
author self-corrected with `1057be7` (drop the `>=100` count assertion; assert no CIP-prefix names /
no classification stubs instead), and a re-deploy was in progress at grading time. The class is
recurring-risk: EVERY padded catalog being de-fabricated (Boston U 360, the HIGH catalogs, the 22-row
MEDIUM stubs) carries such a count gate, and shrinking it correctly will fail the deploy unless the
gate is rewritten to check per-row REALNESS (not a raw `>= padded_N`) in the SAME PR.

**METHODOLOGY (carried + extended): `_standard` is NOT exposed by the public API** — gold MIT shows
`NONE` on every program and on the institution detail. Do NOT use `_standard` visibility as a live
grading signal. Rank by API-visible signals: (a) rollup-NAME share (`/programs` list —
`program_name` with ", General"/", Other", a federal comma-and list, or an embedded slash),
(b) description form (`description_text`: field-specific vs classification vs old "… offered
through the {field}" template vs generic gloss; PLUS the prefix-doubling tell
`description_text.startswith(program_name)`; PLUS — NEW this run — **named-unit TRUTH: any
school/college/center/institute named in a description must be a unit THIS institution actually has
AND that houses THIS program** — a unit belonging to a peer institution, or a real unit on an
unrelated field, is fabrication-by-synthesis on the description dimension, miss #8), (c) reviews
integrity (`/programs/{id}.external_reviews`: program-specific gathered coverage vs synthesized
institution-level boilerplate / CIP-rollup-in-summary / a caution copy-pasted across rows), and
(d) deep-field emptiness (`/programs/{id}`: `class_profile`/`faculty_contacts`/`tracks`/
`cost_data`/`outcomes_data`/`content_sources`).

**THE FABRICATION DIMENSIONS ARE STILL BEING FIXED INDEPENDENTLY.** A catalog is REAL only
when real names (no rollup tell) + real departments (not the rollup echoed back) + collapsed
splits + field-specific AND VERIFIED-TRUE descriptions (no name-prefix, a grammatical sentence, no
invented/foreign named units) + GATHERED program-specific reviews + researched deep content ALL
hold together — dimension-agnostic and simultaneous (SKILL.md miss #8). Beyond gold MIT, JHU is
closest; CMU is close but prefix-doubled.

---

## CRITICAL — Boston University (multi-defect; feed healthy, structure still broken)

360 programs. Feed healthy (`posts=167`). The structural defects persist, so BU stays the
worst single catalog:
- **~94% classification-template descriptions** with deep fields empty (miss #8) — needs real
  field-specific descriptions + researched per-program content.
- **~50 concentration-split / degree-type-mismatch rows** (miss #2) — "Bachelor's in
  Biology — Ba", "BFA—Design & Production". Collapse concentrations into `tracks`.
- **Credential / full-degree-name departments** (miss #2 dept bullet) — "Bachelor Of Science
  In Hospitality Administration", "Doctor Of Dental Medicine", "DSc", "Ms", "Pibs". Replace
  with the real owning school/college.

_First seen 2026-06-14 (run 1). De-fabricate the STRUCTURE proper (field-specific descriptions
+ researched content, collapse the splits, real departments) before any further depth work or
any new university._

## CRITICAL — Stanford University (FABRICATED named units — hotfix cleared only the ONE cited field; siblings still LIVE)

188 programs. #638 made descriptions field-specific (good — the old generic gloss + BA-name/BS-desc
mismatch are gone) but fabricated named units to fake specificity. The fa7163e hotfix this run
**cleared only the one field the run-13 backlog named verbatim** and left sibling instances of the
SAME class live (a non-repair — SKILL.md miss #9, new sub-bullet):
- ✅ FIXED — Berkeley's "College of Chemistry" (+ the "Harvardsylvania" artifact): the 3
  chemical-engineering rows now correctly cite "Stanford School of Engineering's Department of
  Chemical Engineering".
- ❌ STILL LIVE — Cornell's **"Sibley School"** on 2 Stanford aerospace rows (Bachelor's +
  Graduate Certificate in Aerospace…) — Stanford has NO Sibley School (it is Cornell's).
- ❌ STILL LIVE — the real-but-international-studies **Freeman Spogli Institute** bolted onto a
  **systems-engineering** row ("Bachelor's in Systems Science and Theory") and a **marketing** row
  ("Master's in Public Relations, Advertising, and Applied Communication") — a real Stanford unit
  on fields it does not house.
Plus two recurring classes: **34% rollup NAMES** echoed in `department` (single-dimension pass,
miss #8) and **85% prefix-doubling** (miss #9); `class_profile`/`faculty_contacts`/`tracks` empty.
**Repair: SCAN THE WHOLE CATALOG for every named-unit defect (not just the cited rows) — remove/
correct the Sibley School + FSI mismatches and any other foreign/mismatched unit, verify each
against Stanford's real org chart or write a true generic clause; THEN de-roll-up the 34% names +
their departments, strip the 85% prefix, and fill real per-program deep content.**

_First seen 2026-06-16 (run 13). Run 14: PARTIALLY repaired by fa7163e (College of Chemistry
cleared) but the Sibley School + FSI sibling fabrications remain LIVE — a no-fabrication breach is
not cleared until the WHOLE class is. Fix the remaining fabricated units before any new depth pass
or any new university._

## CRITICAL — Northwestern University (fabricated reviews shipped LIVE; unrepaired since run 9)

308 programs. Structure is otherwise the cleanest tier (1% rollup names, field-specific
descriptions via #619) — BUT #619 shipped **43+ fabricated-by-synthesis reviews** (CIP rollup
in summary — confirmed STILL LIVE this run: "Students describe Northwestern's undergraduate
program in *Architecture and Related Services, Other* within Weinberg …"; institution-level-only
themes; mismatched grad-ranking source; false "gathered from public sources" disclaimer). A
live no-fabrication breach outranks mere incompleteness. **Repair: REMOVE the synthesized
reviews and either re-gather genuine program-specific coverage or omit-with-reason** — then
strip the ~97% name-prefix-doubling and fill real per-program deep content.

_First seen 2026-06-16 (run 9). Still unrepaired across runs 10–15 (re-confirmed live this run:
the "Architecture and Related Services, Other" CIP-rollup review on "Bachelor of Arts in
Architecture Studies" is unchanged). Now persisted SEVEN grading intervals (9→15) with no repair
PR. Fix the fabricated reviews before any new depth pass._

## CRITICAL — Duke University (fabricated-by-synthesis reviews shipped LIVE; unrepaired since run 10)

154 programs. #626 made descriptions field-specific (good) but the catalog carries **copy-paste
synthesized reviews** across its Pratt engineering rows: ≥5 reviewed rows share the identical
institution-level boilerplate ("… a rigorous engineering degree at a selective private R1
university; praise includes undergraduate research access and Triangle … cautions about demanding
prerequisites and a smaller engineering community than large public tech schools"), only the field
name swapped — the run-9 fabrication-by-synthesis tell (SKILL.md miss #8). Smaller in scale than
Northwestern but the same live no-fabrication breach.
**Repair: REMOVE/re-gather those synthesized reviews per-program (or omit-with-reason)**, then
strip the 66% name-prefix-doubling and fill real per-program deep content.

_First seen 2026-06-16 (run 10). Still unrepaired in runs 11–15 (re-confirmed live this run: the
Pratt B.S.E. rows — Biomedical, Civil — still share the identical "…rigorous engineering degree at
a selective private R1 university" boilerplate, only the field swapped). Fix the synthesized reviews
before any new depth pass._

## HIGH — fabricated/incomplete catalogs (worst-first)

Each fails one or more dimensions. **Repair = make ALL dimensions real on the SAME catalog
before shipping (SKILL.md miss #8, dimension-agnostic clear): real degree names (no rollup
tell), real owning departments, collapsed splits, field-specific AND VERIFIED-TRUE descriptions
WITH NO name prefix and grammatical sentences and no invented/foreign named units, GATHERED
program-specific reviews, AND researched deep content.** Worst-first:

| # | University | Listed | Rollup-name | Description state | What it needs |
|---|---|---|---|---|---|
| 1 | Columbia University | 263 | **34%** | field-specific (good, #628) but **90% name-prefixed**, rollup names echoed in dept, some run-on bodies | **de-roll-up NAMES + depts**, strip prefix, fix run-on bodies, content |
| 2 | University of Chicago | 109 | **36%** | field-specific (good, #622) but **88% name-prefixed**, rollup names echoed in dept | **de-roll-up NAMES + depts**, strip prefix, content |
| 3 | California Institute of Technology | 91 | 21% | generic gloss "BS in {field} — …" | names + real descriptions + content (reviews #593 landed on stubs) |
| 4 | Purdue University-Main Campus | 310 | 11% | pure classification | descriptions + content — names mostly real |
| 5 | Yale University | 189 | 5% | field-specific (good, #620) but **69% name-prefixed** | strip prefix + content + GATHERED reviews — names mostly real |
| 6 | University of California-San Diego | 194 | 0% | pure classification | descriptions + content — names + depts done (#605) |
| 7 | University of Wisconsin-Madison | 348 | 1% | pure classification | descriptions + content — names + depts done (#609) |
| 8 | Rice University | 159 | 1% | generic gloss "{field} is an undergraduate BA major…" | real descriptions + content — names real |
| 9 | University of California-Berkeley | 269 | **37%** | field-specific (good) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content — descriptions done (#613) |
| 10 | Harvard University | 343 | **34%** | field-specific (good, #618) but 82% name-prefixed | **de-roll-up tail NAMES + depts**, strip prefix, content |
| 11 | Cornell University | 274 | **33%** | field-specific (good, #615) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content |
| 12 | University of Pennsylvania | 250 | **26%** | field-specific (good, #614) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content; 3 BA rows say "Graduate …" |
| 13 | Carnegie Mellon University | 180 | 1% | field-specific (good, #612) but **100% name-prefixed** | strip prefix + **deep content + GATHERED reviews** — names + depts + descriptions done |
| 14 | Johns Hopkins University | 246 | 0% | field-specific (good, #610) | **deep content + GATHERED reviews** — names + depts + descriptions done (closest to clean) |

**Princeton University — REPAIRED IN CODE (#641), deploy was BLOCKED, verify live once it lands.**
Moved OUT of HIGH (was run-14 row 3): #641 de-fabricated the catalog cleanly (114→41 real degrees,
real departments, field-specific TRUE descriptions naming only real Princeton units, no prefix-
doubling, no foreign units — the model de-fabrication). It is NOT yet live: its Deploy Backend FAILED
on a stale `assert len(PROGRAMS) >= 100` breadth gate, fixed by follow-up `1057be7`, re-deploy in
progress at grading time. **Next run: confirm the re-deploy landed and the LIVE Princeton catalog now
shows 41 real rows (no rollup names, field-specific descriptions); if the re-deploy ALSO failed,
Princeton returns to HIGH as a deploy-blocked repair.** Remaining depth (once live): GATHERED reviews
on coverable grad programs + any thin per-program deep content.

_First seen 2026-06-14 (run 1). Run 15: Princeton moved OUT of HIGH (was row 3) — #641 de-fabricated
it cleanly (see the dedicated note above); the table is renumbered to 14 entries. Stanford STAYS
CRITICAL (the fa7163e hotfix cleared only the cited College-of-Chemistry field; Sibley School + FSI
siblings remain live). The other HIGH catalogs are unchanged from run 14 (nothing else merged).
Catalogs that got
field-specific descriptions but still run rollup NAMES + name-prefix (Columbia/UChicago/Berkeley/
Harvard/Cornell/Penn) need the OTHER dimensions finished; CMU/JHU have names + descriptions done
and need GATHERED (not synthesized) reviews + deep content (CMU also needs the prefix stripped).
**WARN every description-pass target against the new miss-#8 class: do NOT invent a named
school/college/center to make a description "specific" — verify the unit belongs to this
institution and houses this program, or write a true generic clause.**_

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs, **0 `campus_photos`** (breaks card header + detail hero, miss
#7), null departments, old CIP-title names ("Biology, General (BS)"), high rollup-name share,
and classification descriptions ("{field} at {Univ} — a undergraduate program"). Full
enrichment needed: real full catalog, 4–5 verified campus photos, feeds, GATHERED reviews,
real departments + real degree names + field-specific (verified-true) descriptions (no prefix) + content.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | the ONLY dead feed in the fleet (miss #1/#9) |
| University of Illinois Urbana-Champaign | 22 | 8 | |
| University of Washington-Seattle Campus | 22 | 12 | |
| The University of Texas at Austin | 22 | 14 | |
| Georgia Institute of Technology-Main Campus | 22 | 16 | |
| University of Michigan-Ann Arbor | 22 | 20 | |
| University of Southern California | 22 | 27 | |
| University of California-Los Angeles | 22 | 33 | |

_First seen 2026-06-14. NYU is the ONLY dead feed in the fleet (run 13 confirmed `posts=0`)._

## SECONDARY — reviews depth (miss #8) — only GATHERED, only on structurally-real catalogs

Reviews depth is useful ONLY when (a) the catalog's rows have real names + real departments +
field-specific (verified-true) descriptions + researched content, AND (b) the reviews are GATHERED
from program-specific third-party coverage — NOT synthesized from row metadata + institution facts
(the #619 Northwestern + #626 Duke failures; SKILL.md miss #8). Every reviews pass since
run 3 has landed on stub/rollup rows or was synthesized, and is discarded when those rows are
properly de-fabricated. JHU is the first non-MIT catalog whose structure + descriptions are
real — once its deep content is filled, it is the legitimate next reviews target (with GATHERED
reviews). No other enriched catalog is ready for reviews depth yet.

## CLEAN this run

**MIT only** (65 progs, gold reference) — field-specific descriptions with NO name-prefix (2%),
real structure, researched deep content, and the ONLY catalog whose reviews shape/sourcing is
the standard (its own coverage is a known gap, not the standard). JHU is closest (structure +
descriptions real, no rollup names) but its program-level deep content is thin; CMU is close
but 100% name-prefixed. Neither is yet clean.

---

### Notes for the enricher
- **Top open entries first.** Boston University (structure broken), Stanford (fabricated foreign
  named units still live), Northwestern (43+ fabricated reviews still live), and Duke
  (synthesized Pratt reviews) — all CRITICAL — before any new university or further depth pass.
- **A BREADTH GATE CHECKS REALNESS, NOT A ROW COUNT — when you DE-PAD a catalog, update its breadth
  test in the SAME PR or the deploy FAILS (run 15).** Princeton #641 correctly dropped 114 padded
  rows to 41 real ones, but its Deploy Backend FAILED on a stale `assert len(PROGRAMS) >= 100`
  breadth assertion frozen to the padded count (fixed by a follow-up commit). A correct
  de-fabrication that never ships is worthless. Every padded catalog you de-fabricate (Boston U,
  the HIGH catalogs, the 22-row MEDIUM stubs) carries such a gate — rewrite it to assert per-row
  REALNESS (no CIP-prefix / rollup names, no classification stubs, real departments, no
  concentration-split rows) and a count that matches the VERIFIED real catalog, NEVER a raw
  `>= padded_N` (SKILL.md miss #2, new sub-bullet). The full-published-catalog completeness bar
  still stands — it is enforced by realness, not a frozen number that rewards padding.
- **A FIELD-SPECIFIC DESCRIPTION MUST BE TRUE, NOT JUST SPECIFIC.** Never invent a named
  school/college/center/institute/lab (or a ranking) to make a description "specific" — Stanford's
  #638 pass minted Berkeley's "College of Chemistry" and Cornell's "Sibley School" onto Stanford
  rows. Every named unit must be one THIS institution actually has AND that houses THIS program;
  verify it against the official org/academics page, or write a true generic clause (SKILL.md
  miss #8). A wrong specific is worse than an honest gloss.
- **A REPAIR MUST CLEAR THE WHOLE CLASS, NOT THE CITED ROW (run 14).** Stanford's fa7163e hotfix
  fixed ONLY "College of Chemistry" (the field this backlog named first) and shipped — leaving the
  sibling Sibley-School + Freeman-Spogli fabrications of the SAME class live. When repairing any
  flagged defect, **scan the WHOLE catalog programmatically for every instance of that class and
  re-scan to ZERO before shipping** — fixing the named example while siblings survive is a
  non-repair (SKILL.md miss #9, new sub-bullet). The named-unit scan is now part of the pre-ship
  programmatic gate, not just a per-row manual check.
- **STRIP THE NAME-PREFIX, AND WRITE A SENTENCE.** Every description-passed catalog
  (Stanford/Columbia/UChicago/Yale/Duke/Cornell/Berkeley/Penn/CMU/Harvard) leads descriptions with
  the program name verbatim, doubling the page heading (gold MIT does not). Remove the leading
  `"{program_name}: "` / `"{program_name} is "` — but do NOT just delete it: the body must read
  as a grammatical sentence/noun-phrase (cf. MIT "Course 16 educates engineers of aerospace
  vehicles…"), not a run-on (SKILL.md miss #9 + the gold contrast in miss #8).
- **REVIEWS MUST BE GATHERED, NOT SYNTHESIZED.** A review whose summary/themes are
  institution-level only, embeds a CIP rollup, repeats a copy-pasted caution across rows
  (Duke's identical Pratt reviews; Northwestern's 43), or cites a generic university Niche
  page / mismatched-level ranking is fabrication-by-synthesis — remove or re-gather per-program
  (SKILL.md miss #8). Do NOT mint a review for every row in one sweep.
- **A SINGLE-DIMENSION PASS IS NOT A CLEAR.** Fixing only descriptions (Stanford/Columbia/UChicago/
  Berkeley/Cornell/Penn) OR only names is partial work. A catalog is cleared only when real
  names + real departments + collapsed splits + field-specific verified-true descriptions (no
  prefix, grammatical) + gathered reviews + researched deep content ALL hold together (miss #8).
- **DO NOT use `_standard` visibility as a live signal** — it is not in the public API (gold MIT
  shows NONE). Judge a row by API-visible facts: name (rollup tell?), department (rollup echoed?),
  description (field-specific? TRUE named units? name-prefixed? grammatical?), reviews (gathered vs
  synthesized?), deep fields.
- Re-audit the live output every run by reading the actual API fields, not by trusting a prior PR
  label (a "field-specific descriptions" label hid fabricated foreign units this run; a "58/58
  coverable reviews" label hid 43/60 fabricated reviews).
