# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken / fabricated data shipped live) · **high** (real but materially
incomplete) · **medium** (never enriched / shallow). Evidence is from the live API
(`api.unipaith.co/api/v1`).

_Last graded: 2026-06-16 (grader run 12). **NO new profile-enrichment PR has merged since
run 10** — the run-11 grader PR (#632) is `origin/main` HEAD with ZERO commits after it; the
run-10 grader PR (#631) precedes it; the last profile work was the four description PRs (#620
Yale, #622 UChicago, #626 Duke, #628 Columbia) graded by run 10. So the live fleet is now
byte-identical across runs 10→11→12 (THREE consecutive intervals with no new enrichment).
Every metric below was re-confirmed live this run (Northwestern n=308 rollup=1% / prefix-dbl=97%;
Columbia n=263 34% / 90%; Duke n=154 3% / 66%; gold MIT n=65 6% / **2%**; both Northwestern +
Duke synthesized reviews STILL live — Northwestern's "Architecture and Related Services, Other"
CIP-rollup summary and Duke's 5 identical Pratt B.S.E. "rigorous engineering degree at a
selective private R1 university" boilerplate). No NEW defect class; the grader changed NO rules
(anti-churn). The four description PRs ARE real description progress (the old "… offered through
the {field}" template is gone: 0% old-template, 0% empty on all four) but each still carries
defects the rulebook ALREADY forbids:_

- **Prefix-doubling (SKILL.md miss #9, added run 9) recurred on ALL FOUR new catalogs.**
  Descriptions still lead with the program name verbatim (`"{program_name}: …"`), doubling the
  page heading. Share of rows whose `description_text` starts with `program_name`:
  **Columbia 90%, UChicago 88%, Yale 69%, Duke 66%** — vs gold MIT **2%**.
- **Single-dimension passes (SKILL.md miss #8, dimension-agnostic) — Columbia/UChicago layered
  field-specific descriptions on top of un-de-rolled-up names.** Columbia still **34%** rollup
  NAMES with the rollup echoed in `department` ("Bachelor's in Area Studies", dept "Area
  Studies"); UChicago **36%**. A description-only pass is NOT a clear.
- **Fabrication-by-synthesis reviews (SKILL.md miss #8, added run 9) NOW LIVE ON DUKE.** Duke
  carries copy-paste synthesized reviews across its Pratt engineering rows — 5 rows share the
  IDENTICAL institution-level boilerplate "… within Pratt as a rigorous engineering degree at a
  selective private R1 university; praise includes undergraduate research access and Triangle …
  with cautions about demanding prerequisites and a smaller engineering community than large
  public tech schools," only the field swapped. Same breach as #619 Northwestern.

**No NEW fleet-wide defect class this run — every defect above is a recurrence of a class the
rulebook already names, so the grader changed NO rules (anti-churn rail).** The recurrence is
an enricher-BEHAVIOR problem (it is not applying its own rules), flagged for human review in
the changelog, not a rulebook gap.

**METHODOLOGY (carried): `_standard` is NOT exposed by the public API** — gold MIT shows `NONE`
on every program and on the institution detail. Do NOT use `_standard` visibility as a live
grading signal. Rank by API-visible signals: (a) rollup-NAME share (`/programs` list —
`program_name` with ", General"/", Other", a federal comma-and list, or an embedded slash),
(b) description form (`description_text`: field-specific vs classification vs old "… offered
through the {field}" template vs generic gloss; PLUS the prefix-doubling tell
`description_text.startswith(program_name)`), (c) reviews integrity
(`/programs/{id}.external_reviews`: program-specific gathered coverage vs synthesized
institution-level boilerplate / CIP-rollup-in-summary / a caution copy-pasted across rows),
and (d) deep-field emptiness (`/programs/{id}`: `class_profile`/`faculty_contacts`/`tracks`/
`cost_data`/`outcomes_data`/`content_sources`).

**THE FABRICATION DIMENSIONS ARE STILL BEING FIXED INDEPENDENTLY.** A catalog is REAL only
when real names (no rollup tell) + real departments (not the rollup echoed back) + collapsed
splits + field-specific descriptions (no name-prefix, a grammatical sentence) + GATHERED
program-specific reviews + researched deep content ALL hold together — dimension-agnostic and
simultaneous (SKILL.md miss #8). Beyond gold MIT, JHU is closest; CMU is close but
prefix-doubled.

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

## CRITICAL — Northwestern University (fabricated reviews shipped LIVE; unrepaired since run 9)

308 programs. Structure is otherwise the cleanest tier (1% rollup names, field-specific
descriptions via #619) — BUT #619 shipped **43+ fabricated-by-synthesis reviews** (CIP rollup
in summary — confirmed STILL LIVE this run: "Students describe Northwestern's undergraduate
program in *Architecture and Related Services, Other* within Weinberg …"; institution-level-only
themes; mismatched grad-ranking source; false "gathered from public sources" disclaimer). A
live no-fabrication breach outranks mere incompleteness. **Repair: REMOVE the synthesized
reviews and either re-gather genuine program-specific coverage or omit-with-reason** — then
strip the 97% name-prefix-doubling and fill real per-program deep content.

_First seen 2026-06-16 (run 9). Still unrepaired across runs 10–12 (re-confirmed live this run:
the "Architecture and Related Services, Other" CIP-rollup review on "Bachelor of Arts in
Architecture Studies" is unchanged). Now persisted FOUR grading intervals (9→12) with no repair
PR. Fix the fabricated reviews before any new depth pass._

## CRITICAL — Duke University (fabricated-by-synthesis reviews shipped LIVE this run)

154 programs. #626 made descriptions field-specific (good) but the catalog now carries
**copy-paste synthesized reviews** across its Pratt engineering rows: 5 reviewed rows share the
identical institution-level boilerplate ("… a rigorous engineering degree at a selective
private R1 university; praise includes undergraduate research access and Triangle … cautions
about demanding prerequisites and a smaller engineering community than large public tech
schools"), only the field name swapped — the run-9 fabrication-by-synthesis tell (SKILL.md
miss #8). Smaller in scale than Northwestern but the same live no-fabrication breach.
**Repair: REMOVE/re-gather those synthesized reviews per-program (or omit-with-reason)**, then
strip the 66% name-prefix-doubling and fill real per-program deep content.

_First seen 2026-06-16 (run 10). Still unrepaired in runs 11–12 (re-confirmed live this run: 5
Pratt B.S.E. rows still share the identical "…rigorous engineering degree at a selective private
R1 university" boilerplate, only the field swapped). Fix the synthesized reviews before any new
depth pass._

## HIGH — fabricated/incomplete catalogs (worst-first)

Each fails one or more dimensions. **Repair = make ALL dimensions real on the SAME catalog
before shipping (SKILL.md miss #8, dimension-agnostic clear): real degree names (no rollup
tell), real owning departments, collapsed splits, field-specific descriptions WITH NO name
prefix and grammatical sentences, GATHERED program-specific reviews, AND researched deep
content.** Worst-first:

| # | University | Listed | Rollup-name | Description state | What it needs |
|---|---|---|---|---|---|
| 1 | Columbia University | 263 | **34%** | field-specific (good, #628) but **90% name-prefixed**, rollup names echoed in dept, some run-on bodies | **de-roll-up NAMES + depts**, strip prefix, fix run-on bodies, content |
| 2 | University of Chicago | 109 | **36%** | field-specific (good, #622) but **88% name-prefixed**, rollup names echoed in dept | **de-roll-up NAMES + depts**, strip prefix, content |
| 3 | Stanford University | 188 | 34% | generic gloss + BA-name/"BS"-desc mismatch | names + depts + real descriptions + content |
| 4 | Princeton University | 114 | 27% | MIXED — some field-specific, some generic gloss | de-roll-up names + finish descriptions + content |
| 5 | California Institute of Technology | 91 | 21% | generic gloss "BS in {field} — …" | names + real descriptions + content (reviews #593 landed on stubs) |
| 6 | Purdue University-Main Campus | 310 | 11% | pure classification | descriptions + content — names mostly real |
| 7 | Yale University | 189 | 5% | field-specific (good, #620) but **69% name-prefixed** | strip prefix + content + GATHERED reviews — names mostly real |
| 8 | University of California-San Diego | 194 | 0% | pure classification | descriptions + content — names + depts done (#605) |
| 9 | University of Wisconsin-Madison | 348 | 1% | pure classification | descriptions + content — names + depts done (#609) |
| 10 | Rice University | 159 | 1% | generic gloss "{field} is an undergraduate BA major…" | real descriptions + content — names real |
| 11 | University of California-Berkeley | 269 | **37%** | field-specific (good) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content — descriptions done (#613) |
| 12 | Harvard University | 343 | **34%** | field-specific (good, #618) but 82% name-prefixed | **de-roll-up tail NAMES + depts**, strip prefix, content |
| 13 | Cornell University | 274 | **33%** | field-specific (good, #615) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content |
| 14 | University of Pennsylvania | 250 | **26%** | field-specific (good, #614) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content; 3 BA rows say "Graduate …" |
| 15 | Carnegie Mellon University | 180 | 1% | field-specific (good, #612) but **100% name-prefixed** | strip prefix + **deep content + GATHERED reviews** — names + depts + descriptions done |
| 16 | Johns Hopkins University | 246 | 0% | field-specific (good, #610) | **deep content + GATHERED reviews** — names + depts + descriptions done (closest to clean) |

_First seen 2026-06-14 (run 1). Run 10 re-ranked by API-visible signals. Columbia/UChicago
(#628/#622) moved UP within HIGH: they got field-specific descriptions but layered them on
34–36% rollup NAMES (+ rollup departments) AND added 88–90% prefix-doubling — the textbook
single-dimension pass (SKILL.md miss #8). Yale (#620) advanced to "descriptions done, names
mostly real" but is 69% prefix-doubled. Duke moved OUT of HIGH to CRITICAL (synthesized reviews
shipped live). Rows that got field-specific descriptions but still run rollup NAMES + name-prefix
(Columbia/UChicago/Berkeley/Harvard/Cornell/Penn) need the OTHER dimensions finished; CMU/JHU
have names + descriptions done and need GATHERED (not synthesized) reviews + deep content
(CMU also needs the prefix stripped)._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs, **0 `campus_photos`** (breaks card header + detail hero, miss
#7), null departments, old CIP-title names ("Biology, General (BS)"), high rollup-name share,
and classification descriptions ("{field} at {Univ} — a undergraduate program"). Full
enrichment needed: real full catalog, 4–5 verified campus photos, feeds, GATHERED reviews,
real departments + real degree names + field-specific descriptions (no prefix) + content.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | the ONLY dead feed in the fleet (miss #1/#9) |
| University of Illinois Urbana-Champaign | 22 | 8 | |
| University of Washington-Seattle Campus | 22 | 12 | |
| The University of Texas at Austin | 22 | 14 | |
| Georgia Institute of Technology-Main Campus | 22 | 16 | |
| University of Michigan-Ann Arbor | 22 | 20 | |
| University of Southern California | 22 | 27 | |
| University of California-Los Angeles | 22 | 31 | |

_First seen 2026-06-14. NYU is the ONLY dead feed in the fleet (run 10 confirmed `posts=0`)._

## SECONDARY — reviews depth (miss #8) — only GATHERED, only on structurally-real catalogs

Reviews depth is useful ONLY when (a) the catalog's rows have real names + real departments +
field-specific descriptions + researched content, AND (b) the reviews are GATHERED from
program-specific third-party coverage — NOT synthesized from row metadata + institution facts
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
- **Top open entries first.** Boston University (structure broken), Northwestern (43+ fabricated
  reviews still live), and Duke (synthesized Pratt reviews shipped this run) — all CRITICAL —
  before any new university or further depth pass.
- **STRIP THE NAME-PREFIX, AND WRITE A SENTENCE.** Every description-passed catalog
  (Columbia/UChicago/Yale/Duke/Cornell/Berkeley/Penn/CMU/Harvard) leads descriptions with the
  program name verbatim, doubling the page heading (gold MIT does not). Remove the leading
  `"{program_name}: "` / `"{program_name} is "` — but do NOT just delete it: the body must read
  as a grammatical sentence/noun-phrase (cf. MIT "Course 16 educates engineers of aerospace
  vehicles…"), not a run-on like Columbia's "{School name} {bare field} combines …" (SKILL.md
  miss #9 + the gold contrast in miss #8).
- **REVIEWS MUST BE GATHERED, NOT SYNTHESIZED.** A review whose summary/themes are
  institution-level only, embeds a CIP rollup, repeats a copy-pasted caution across rows
  (Duke's 5 identical Pratt reviews; Northwestern's 43), or cites a generic university Niche
  page / mismatched-level ranking is fabrication-by-synthesis — remove or re-gather per-program
  (SKILL.md miss #8). Do NOT mint a review for every row in one sweep.
- **A SINGLE-DIMENSION PASS IS NOT A CLEAR.** Fixing only descriptions (Columbia/UChicago/
  Berkeley/Cornell/Penn) OR only names is partial work. A catalog is cleared only when real
  names + real departments + collapsed splits + field-specific descriptions (no prefix,
  grammatical) + gathered reviews + researched deep content ALL hold together (SKILL.md miss #8).
- **DO NOT use `_standard` visibility as a live signal** — it is not in the public API (gold MIT
  shows NONE). Judge a row by API-visible facts: name (rollup tell?), department (rollup echoed?),
  description (field-specific? name-prefixed? grammatical?), reviews (gathered vs synthesized?),
  deep fields.
- Re-audit the live output every run by reading the actual API fields, not by trusting a prior PR
  label (a "58/58 coverable reviews" label hid 43/60 fabricated reviews; a "field-specific
  descriptions" label hid 88–90% prefix-doubling this run).
</content>
</invoke>
