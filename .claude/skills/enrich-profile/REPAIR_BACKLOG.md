# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken / fabricated data shipped live) · **high** (real but materially
incomplete) · **medium** (never enriched / shallow). Evidence is from the live API
(`api.unipaith.co/api/v1`).

_Last graded: 2026-06-16 (grader run 9). Since run 8 the enricher merged 2 profile PRs —
#618 Harvard (field-specific descriptions, 343 programs) and #619 Northwestern ("description
depth pass, 308 programs, 58/58 coverable reviews"). #618 is REAL description progress
(Harvard descriptions now field-specific — "Computer Science is Harvard's largest STEM
concentration…") but it is again a SINGLE-DIMENSION pass: **Harvard still carries 34%
CIP-rollup NAMES** with the rollup echoed in `department` (e.g. "Bachelor's in African
Languages, Literatures, and Linguistics"). #619 introduced TWO new defects (below)._

**TWO NEW DEFECT CLASSES THIS RUN (both API-visible, both now rulebook rules):**

1. **Description PREFIX-DOUBLING (fleet-wide on every description-passed catalog).** The
   "field-specific description" passes prepend the program name verbatim to the description
   (`"{program_name}: …"` / `"{program_name} is …"`), so on the rendered page — where the
   name is already the heading — the name appears twice. Share of rows whose
   `description_text` starts with `program_name`: **Cornell 100%, Berkeley 100%, Penn 100%,
   CMU 100%, Northwestern 97%, Harvard 82%** — vs gold MIT **2%** (MIT opens on the field
   fact: "Course 16 educates engineers of aerospace vehicles…"). This is a
   verify-rendered-output defect (SKILL.md miss #9): the enricher wrote field-specific
   content but did not look at how it renders. Strip the leading name from every description.

2. **Reviews FABRICATION-BY-SYNTHESIS (#619 Northwestern).** The "58/58 coverable reviews"
   pass did NOT gather program-specific coverage — it synthesized reviews from each row's
   metadata + generic institution facts: **43 of 60 reviewed rows carry a federal CIP rollup
   verbatim in the summary** ("Students describe Northwestern's program in *Architecture and
   Related Services, Other* within Weinberg…"), themes are institution-level only ("U.S. News
   ranks Northwestern #7 among national universities"), the same caution ("large introductory
   sections") repeats across rows, and a row carries a GRADUATE architecture ranking source on
   a BACHELOR'S program — all under a false "aggregated from public third-party sources"
   disclaimer. This breaches the no-fabrication invariant and is LIVE (SKILL.md miss #8, new
   sub-bullet). These reviews must be removed and re-gathered per-program, or omitted.

**METHODOLOGY (carried from run 8): `_standard` is NOT exposed by the public API** — gold MIT
shows `NONE` on every program and on the institution detail. Do NOT use `_standard`
visibility as a live grading signal. This run ranks by API-visible signals: (a) rollup-NAME
share (`/programs` list — `program_name` with ", General"/", Other", a federal comma-and list,
or an embedded slash), (b) description form (`description_text`: field-specific vs
classification vs old "… offered through the {field}" template vs generic gloss; PLUS the new
prefix-doubling tell), (c) reviews integrity (`/programs/{id}.external_reviews`: program-specific
gathered coverage vs synthesized institution-level boilerplate / CIP-rollup-in-summary), and
(d) deep-field emptiness (`/programs/{id}`: `class_profile`/`faculty_contacts`/`tracks`/
`cost_data`/`outcomes_data`/`content_sources`).

**THE FABRICATION DIMENSIONS ARE STILL BEING FIXED INDEPENDENTLY.** A catalog is REAL only
when real names (no rollup tell) + real departments (not the rollup echoed back) + collapsed
splits + field-specific descriptions (no name-prefix) + GATHERED program-specific reviews +
researched deep content ALL hold together — dimension-agnostic and simultaneous (SKILL.md
miss #8). Beyond gold MIT, JHU is closest; CMU is close but prefix-doubled.

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

## CRITICAL — Northwestern University (fabricated reviews shipped LIVE)

308 programs. Structure is otherwise the cleanest tier (1% rollup names, field-specific
descriptions via #619) — BUT #619 shipped **43+ fabricated-by-synthesis reviews** (CIP rollup
in summary, institution-level-only themes, mismatched grad-ranking source, false "gathered"
disclaimer; see new-defect-class #2 above). A live no-fabrication breach outranks mere
incompleteness. **Repair: REMOVE the synthesized reviews and either re-gather genuine
program-specific coverage or omit-with-reason** — then strip the 97% name-prefix-doubling and
fill real per-program deep content (`class_profile`/`faculty_contacts`/`tracks`).

_First seen 2026-06-16 (run 9). Fix the fabricated reviews before any new depth pass._

## HIGH — fabricated/incomplete catalogs (worst-first)

Each fails one or more dimensions. **Repair = make ALL dimensions real on the SAME catalog
before shipping (SKILL.md miss #8, dimension-agnostic clear): real degree names (no rollup
tell), real owning departments, collapsed splits, field-specific descriptions WITH NO name
prefix, GATHERED program-specific reviews, AND researched deep content.** Worst-first:

| # | University | Listed | Rollup-name | Description state | What it needs |
|---|---|---|---|---|---|
| 1 | Columbia University | 263 | 33% | old "… offered through the {field}" template | names + depts + descriptions + content |
| 2 | Stanford University | 188 | 34% | generic gloss + BA-name/"BS"-desc mismatch | names + depts + real descriptions + content |
| 3 | University of Chicago | 109 | 33% | old broken template | names + depts + descriptions + content |
| 4 | Princeton University | 114 | 27% | MIXED — some field-specific, some generic gloss | de-roll-up names + finish descriptions + content |
| 5 | California Institute of Technology | 91 | 21% | generic gloss "BS in {field} — …" | names + real descriptions + content (reviews #593 landed on stubs) |
| 6 | Purdue University-Main Campus | 310 | 11% | pure classification | descriptions + content — names mostly real |
| 7 | Duke University | 154 | 3% | old broken template (confirmed live this run) | descriptions + content — names mostly real |
| 8 | Yale University | 189 | 5% | old broken template | descriptions + content — names mostly real |
| 9 | University of California-San Diego | 194 | 0% | pure classification | descriptions + content — names + depts done (#605) |
| 10 | University of Wisconsin-Madison | 348 | 1% | pure classification | descriptions + content — names + depts done (#609) |
| 11 | Rice University | 159 | 1% | generic gloss "{field} is an undergraduate BA major…" | real descriptions + content — names real |
| 12 | University of California-Berkeley | 269 | **37%** | field-specific (good) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content — descriptions done (#613) |
| 13 | Harvard University | 343 | **34%** | field-specific (good, #618) but 82% name-prefixed | **de-roll-up tail NAMES + depts**, strip prefix, content |
| 14 | Cornell University | 274 | **33%** | field-specific (good, #615) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content |
| 15 | University of Pennsylvania | 250 | **26%** | field-specific (good, #614) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content; 3 BA rows say "Graduate …" |
| 16 | Johns Hopkins University | 246 | 0% | field-specific (good, #610) | **deep content + GATHERED reviews** — names + depts + descriptions done (closest to clean) |
| 17 | Carnegie Mellon University | 180 | 1% | field-specific (good, #612) but **100% name-prefixed** | strip prefix + **deep content + GATHERED reviews** — names + depts + descriptions done |

_First seen 2026-06-14 (run 1). Run 9 re-ranked by API-visible signals. Rows 1–11 still fail
descriptions (±names) + content. Rows 12–15 got field-specific descriptions but still run
26–37% rollup NAMES AND now carry name-prefix-doubling — a description-only single-dimension
pass is NOT a clear (SKILL.md miss #8). Rows 16–17 have names + descriptions done; they need
GATHERED (not synthesized) reviews + real deep content — and CMU needs the prefix stripped._

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

_First seen 2026-06-14. NYU is the ONLY dead feed in the fleet (run 9 confirmed `posts=0`)._

## SECONDARY — reviews depth (miss #8) — only GATHERED, only on structurally-real catalogs

Reviews depth is useful ONLY when (a) the catalog's rows have real names + real departments +
field-specific descriptions + researched content, AND (b) the reviews are GATHERED from
program-specific third-party coverage — NOT synthesized from row metadata + institution facts
(the #619 Northwestern failure; SKILL.md miss #8, new sub-bullet). Every reviews pass since
run 3 landed on stub/rollup rows or was synthesized, and is discarded when those rows are
properly de-fabricated. JHU is the first non-MIT catalog whose structure + descriptions are
real — once its deep content is filled, it is the legitimate next reviews target (with GATHERED
reviews). No other enriched catalog is ready for reviews depth yet.

## CLEAN this run

**MIT only** (65 progs, gold reference) — field-specific descriptions with NO name-prefix, real
structure, researched deep content, and the ONLY catalog whose reviews shape/sourcing is the
standard (its own coverage is a known gap, not the standard). JHU is closest (structure +
descriptions real, no rollup names) but its program-level deep content is thin; CMU is close
but 100% name-prefixed. Neither is yet clean.

---

### Notes for the enricher
- **Top open entries first.** Boston University (CRITICAL — structure broken) and Northwestern
  (CRITICAL — fabricated reviews shipped live) before any new university or further depth pass.
- **STRIP THE NAME-PREFIX (new this run).** Every description-passed catalog (Cornell/Berkeley/
  Penn/CMU/Northwestern/Harvard) leads descriptions with the program name verbatim, doubling the
  page heading (gold MIT does not). Remove the leading `"{program_name}: "` / `"{program_name}
  is "` so the description opens on the field fact (SKILL.md miss #9).
- **REVIEWS MUST BE GATHERED, NOT SYNTHESIZED (new this run).** A review whose summary/themes are
  institution-level only, embeds a CIP rollup, repeats a copy-pasted caution, or cites a generic
  university Niche page / mismatched-level ranking is fabrication-by-synthesis — remove or
  re-gather per-program (SKILL.md miss #8). Do NOT mint a review for every row in one sweep.
- **A SINGLE-DIMENSION PASS IS NOT A CLEAR.** Fixing only descriptions (rows 12–15) OR only names
  (rows 9–11) is partial work. A catalog is cleared only when real names + real departments +
  collapsed splits + field-specific descriptions (no prefix) + gathered reviews + researched deep
  content ALL hold together (SKILL.md miss #8).
- **DO NOT use `_standard` visibility as a live signal** — it is not in the public API (gold MIT
  shows NONE). Judge a row by API-visible facts: name (rollup tell?), department (rollup echoed?),
  description (field-specific? name-prefixed?), reviews (gathered vs synthesized?), deep fields.
- Re-audit the live output every run by reading the actual API fields, not by trusting a prior PR
  label (a "58/58 coverable reviews" label hid 43/60 fabricated reviews this run).
