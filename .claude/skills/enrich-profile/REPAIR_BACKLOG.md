# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken / fabricated data shipped live) · **high** (real but materially
incomplete) · **medium** (never enriched / shallow). Evidence is from the live API
(`api.unipaith.co/api/v1`).

_Last graded: 2026-06-17 (grader run 17). **NO new profile-enrichment PR merged since run 16's
grader** (PR #644 is `origin/main` HEAD) — BUT Princeton #643 ("remove name-prefixed program
descriptions", `2fdc1dc`) landed this interval and cleared Princeton's prefix-doubling. Re-confirmed
live this run: Northwestern n=308 / "Architecture and Related Services, Other" CIP-rollup review STILL
LIVE; Duke 5 Pratt boilerplate reviews STILL LIVE; Stanford Sibley-School + FSI-on-unrelated-fields
fabrications STILL LIVE (5 hits); gold MIT n=65; NYU still the ONLY dead feed `posts=0`; 28
institutions, no sprawl. **NO NEW PROBLEM CLASS this run — every live defect recurs a class the
rulebook already names; no rule changed (anti-churn).**_

**PRINCETON #643 cleared the prefix (31%→0%) — but it was YET ANOTHER single-dimension pass: the 9
CIP-rollup NAMES + their departments are STILL LIVE (miss #8 dimension-agnostic clear).** #643 stripped
the leading `"{program_name}: "` from every description — the LIVE catalog now reads 0% prefix-doubling
(was run-16's 31%), and the after-strip bodies are clean grammatical sentences/noun-phrases ("Anthropology
— the comparative study of human societies and cultures", "Princeton Geosciences covers geology,
geophysics, and paleoclimate with field camps…"). Genuine progress on the prefix dimension, on top of
#641's field-specific TRUE descriptions (real Princeton units — Center for the Study of Religion, ORFE,
SEAS). BUT the de-roll-up the run-16 backlog called for did NOT happen — **9 of 41 rows still carry a
CIP-rollup NAME echoed verbatim into `department`** (miss #2):
- "Bachelor of Arts in Area Studies" (dept "Area Studies"), "…in Religion/Religious Studies",
  "…in Multi/Interdisciplinary Studies, Other", "…in Ethnic, Cultural Minority, Gender, and Group
  Studies", "…in Linguistic, Comparative, and Related Language Studies and Services", and FOUR
  "…Languages, Literatures, and Linguistics" (Classics, Germanic, Romance, Slavic). These are
  federal CIP titles, not Princeton's real degree names ("Classics", "Religion", "German",
  "Near Eastern Studies", …).
- a few thin generic-gloss descriptions on the clean rows ("Economics — micro, macro and
  econometrics") that barely clear the gold contrast (backlog texture, already named).
So Princeton is now near the CLEANEST end of HIGH (true field-specific descriptions, 0% prefix), with
only the 9 rollup names + their departments and deep content/reviews left.

**NO new rulebook gap this run.** The Princeton rollup-name persistence is exactly the single-dimension-
pass class run 16's own rule already targets (the credential-form-agnostic rollup scan): #643 fixed the
prefix dimension in isolation and never touched the names — the enricher is once again repairing ONE
dimension per pass. That is an enricher-BEHAVIOR recurrence (flagged for human review), not a rulebook
gap; more rule text cannot fix it (cf. runs 10/12). The realness gate from run 16 (`1057be7`) was not
re-exercised because #643 did not author a de-roll-up pass.

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

_First seen 2026-06-16 (run 9). Still unrepaired across runs 10–17 (re-confirmed live this run:
the "Architecture and Related Services, Other" CIP-rollup review on "Bachelor of Arts in
Architecture Studies" is unchanged; ≥5 rollup-in-summary reviews in the first 200 rows). Now persisted
NINE grading intervals (9→17) with no repair PR. Fix the fabricated reviews before any new depth pass._

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

_First seen 2026-06-16 (run 10). Still unrepaired in runs 11–17 (re-confirmed live this run: 5
Pratt B.S.E. rows — Biomedical, Civil, Environmental, … — still share the identical "…rigorous
engineering degree at a selective private R1 university" boilerplate, only the field swapped; the
"undergraduate research access and Triangle" phrase also recurs 5×). Fix the synthesized reviews
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
| 15 | Princeton University | 41 | **22%** (9/41) | field-specific + TRUE + **0% prefix** (good, #641+#643) — only **9 rollup names echoed in dept** left | **de-roll-up the 9 CIP-rollup NAMES + their depts** ("…Languages, Literatures, and Linguistics", "Area Studies", "Religion/Religious Studies", "Multi/Interdisciplinary Studies, Other", "Ethnic… Group Studies", "Linguistic, Comparative…" → "Classics"/"German"/"Religion"/etc.), then GATHERED reviews + deep content on coverable grad programs |

**Princeton University — #643 cleared the prefix (31%→0%); now near the CLEANEST end of HIGH.** Live at
41 rows. #641's descriptions are genuinely field-specific and TRUE (real Princeton units — Center for
the Study of Religion, ORFE, SEAS); #643 this interval stripped the 31% name-prefix to 0% (clean
after-strip sentences). What remains: **9 CIP-rollup names echoed verbatim into `department`** (miss #2)
that NO pass has de-rolled-up yet — #643 was a prefix-only single-dimension pass (miss #8). Resolve each
to Princeton's real degree + department, then fill deep content + GATHERED reviews. Stays HIGH (row 15,
cleanest tier: true descriptions, 0% prefix).

_First seen 2026-06-14 (run 1). Run 17: #643 cleared the prefix-doubling (real progress) but left the 9
rollup names — yet another single-dimension pass (miss #8); Princeton stays HIGH (cleanest tier).
Stanford STAYS CRITICAL (the fa7163e hotfix cleared only the cited College-of-Chemistry field; Sibley
School + FSI siblings remain live). The other HIGH catalogs are unchanged from run 16 (nothing else
merged). Catalogs that got
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
- **THE REALNESS GATE MUST SCAN THE ROLLUP TELL ON THE FIELD, CREDENTIAL-FORM-AGNOSTICALLY (run
  16).** Princeton #641's gate `1057be7` (written to replace the count gate, per the note above)
  keyed on the generic "Bachelor's in {rollup}" PREFIX form and so PASSED 8 "Bachelor of Arts in
  {CIP rollup}" rows — "…Languages, Literatures, and Linguistics" ×3, "Area Studies",
  "Religion/Religious Studies", "Multi/Interdisciplinary Studies, Other", "Ethnic… Group Studies" —
  each with the rollup echoed verbatim into `department`, shipped LIVE. A real degree DESIGNATION
  ("Bachelor of Arts in …") does NOT exempt the FIELD: run the rollup-tell scan (", General"/",
  Other"; federal comma-and lists; embedded slashes; bare CIP titles like "Area Studies") on the
  FIELD part of every `program_name` AND `department`, regardless of credential form (SKILL.md
  miss #2, new sub-bullet). Resolve each to Princeton's real degree + department ("Bachelor of Arts
  in Classics" / Department of Classics, "…in Religion" / Department of Religion, "…in German" / …).
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
