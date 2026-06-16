# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken) · **high** (real but materially incomplete) · **medium** (never
enriched / shallow). Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-16 (grader run 8). Since run 7 the enricher merged 3 profile
PRs — #612 CMU, #613 Berkeley, #614 Penn — all "field-specific program descriptions"
passes. This is REAL progress on the exact half run 7 flagged: graded live this run the
descriptions on all three are now genuinely field-specific (pass the gold contrast — e.g.
CMU's AI degree "the nation's first dedicated undergraduate AI degree … across SCS
institutes"; Berkeley astrophysics "access to Lick Observatory, Keck partnerships";
Penn's Wharton / Penn Museum / Weitzman). BUT two of the three did ONLY the description
half: **Berkeley still carries 37% CIP-rollup NAMES and Penn 28%** ("Bachelor's in
Biomedical/Medical Engineering", "Bachelor's in Accounting and Related Services"), with
the rollup echoed in `department` — i.e. a field-specific-description pass layered on top
of un-de-rolled-up names. This is the INVERSE of run 7's names-fixed-but-description-not
(SKILL.md miss #8, new sub-bullet): a single-dimension pass, NOT a clear._

**METHODOLOGY CORRECTION (run 8): `_standard` is NOT exposed by the public API** — gold
MIT shows `NONE` on every program AND on the institution detail too. So "`_standard`
unstamped" (cited as live evidence in runs 5–7 and this backlog) is **not verifiable from
the API** and must NOT be used as a live grading signal. The enricher legitimately stamps
`_standard` in its data module / conformance (where it IS visible) — that guidance stands;
only the GRADER's reliance on it was unfounded. This run ranks by **API-VISIBLE** signals
only: (a) **rollup-NAME share** (read from `/programs` list — `program_name` with a ",
General"/", Other" suffix, a federal comma-and list, or an embedded slash), (b)
**description form** (sampled from `description_text`: field-specific vs pure
classification "{name} is an undergraduate major at {Univ}'s {school}" vs the old broken
"… offered through the {field}" template vs a generic degree gloss "BS in {field} — …"),
and (c) **deep-field emptiness** (from `/programs/{id}`: `class_profile` / `faculty_contacts`
/ `tracks` / `cost_data` / `outcomes_data` / `content_sources` / `external_reviews`).

**THE TWO FABRICATION DIMENSIONS ARE BEING FIXED INDEPENDENTLY AND INCONSISTENTLY.** A
catalog can be clean on NAMES but still run classification descriptions (UCSD, UW-Madison,
Northwestern, Purdue), OR carry field-specific descriptions while names stay CIP rollups
(Berkeley, Penn), OR fail BOTH (Columbia, Cornell, Chicago, Stanford, Harvard tail). A
catalog is REAL only when real names + real departments + collapsed splits + field-specific
descriptions + researched deep content ALL hold together — the bar is dimension-agnostic
and simultaneous (SKILL.md miss #8). Beyond gold MIT, the closest are JHU and CMU (names +
departments + field-specific descriptions all done; deep content still thin).

---

## CRITICAL — Boston University (multi-defect; feed revived, structure still broken)

360 programs. Feed is healthy this run (`posts=167`, was 0 in run 6). The structural
defects persist, so BU stays the worst single catalog:
- **~94% classification-template descriptions** with deep fields empty (miss #8) — needs
  real field-specific descriptions + researched per-program content.
- **~50 concentration-split / degree-type-mismatch rows** (miss #2) — "Bachelor's in
  Biology — Ba", "BFA—Design & Production". Collapse concentrations into `tracks`; keep
  only genuinely separate credentials.
- **Credential / full-degree-name departments** (miss #2 dept bullet) — one-off
  "departments" like "Bachelor Of Science In Hospitality Administration", "Doctor Of
  Dental Medicine", "DSc", "Ms", "Pibs". Replace with the real owning school/college.

_First seen 2026-06-14 (run 1). Feed cleared run 7. De-fabricate the STRUCTURE proper
(field-specific descriptions + researched content, collapse the splits, real departments)
before any further depth work or any new university._

## HIGH — fabricated/incomplete catalogs (worst-first)

Each fails one or both fabrication dimensions, or is missing researched deep content.
**Repair = make ALL dimensions real on the SAME catalog before shipping it (SKILL.md miss
#8, dimension-agnostic clear): real degree names (no rollup tell), real owning departments,
collapsed splits, field-specific descriptions (gold contrast), AND researched per-program
deep content — then reviews.** Worst-first:

| # | University | Listed | Rollup-name | Description state | What it needs |
|---|---|---|---|---|---|
| 1 | Columbia University | 263 | 34% | old broken "… offered through the {field}" template | names + depts + descriptions + content |
| 2 | Cornell University | 274 | 33% | old broken template | names + depts + descriptions + content |
| 3 | University of Chicago | 109 | 33% | old broken template | names + depts + descriptions + content |
| 4 | Stanford University | 188 | 34% | generic gloss "BS in {field} — …" + BA-name/"BS"-desc mismatch | names + depts + real descriptions + content |
| 5 | Harvard University | 343 | 35% | MIXED — flagship/HBS rows field-specific; long tail old template | de-roll-up tail names + tail descriptions + content |
| 6 | University of California-Berkeley | 269 | **37%** | field-specific (good) | **NAMES + departments only** — descriptions done (#613) |
| 7 | University of Pennsylvania | 250 | **28%** | field-specific (good) | **NAMES + departments only** — descriptions done (#614); 3 BA rows say "Graduate …" |
| 8 | Princeton University | 114 | 27% | MIXED — some field-specific, some generic gloss | de-roll-up names + finish descriptions + content |
| 9 | California Institute of Technology | 91 | 20% | generic gloss "BS in {field} — …" | names + real descriptions + content (reviews #593 landed on stubs) |
| 10 | Purdue University-Main Campus | 310 | 10% | pure classification | **descriptions + content** — names mostly real |
| 11 | Northwestern University | 308 | 1% | pure classification | **descriptions + content** — names + depts done (#607) |
| 12 | University of California-San Diego | 194 | 0% | pure classification | **descriptions + content** — names + depts done (#605) |
| 13 | University of Wisconsin-Madison | 348 | 1% | pure classification | **descriptions + content** — names + depts done (#609) |
| 14 | Yale University | 189 | 4% | old broken "… offered through the {field}" template | **descriptions + content** — names mostly real |
| 15 | Duke University | 154 | 2% | old broken template | **descriptions + content** — names mostly real |
| 16 | Rice University | 159 | 0% | generic gloss "{field} is an undergraduate BA major in {Univ}'s {School}" | **real descriptions + content** — names real |
| 17 | Johns Hopkins University | 246 | 0% | field-specific (good, #610) | **deep content + reviews** — names + depts + descriptions all done (closest to clean) |
| 18 | Carnegie Mellon University | 180 | 1% | field-specific (good, #612) | **deep content + reviews** — names + depts + descriptions all done (closest to clean) |

_First seen 2026-06-14 (run 1). Run 8 re-ranked by API-visible signals (rollup-name share +
description form + deep-field emptiness). Two halves are being fixed separately: catalogs
clean on NAMES (rows 11–13) still run classification descriptions; catalogs with
field-specific DESCRIPTIONS (rows 6–7) still run 28–37% rollup names. Finish BOTH on the
same catalog. JHU and CMU (rows 17–18) have both halves done — they need researched deep
content (program `content_sources`/`cost_data`/`outcomes_data`/`class_profile`/`faculty`/
`tracks`) + reviews, NOT another rename/description pass._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs (first-run shallow stub), **0 `campus_photos`** (breaks card
header + detail hero, miss #7), null departments, old CIP-title names, and high rollup-name
share. Full enrichment needed: real full catalog, 4–5 verified campus photos, feeds,
reviews, real departments + real degree names + field-specific descriptions + content.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | the ONLY dead feed in the fleet (miss #1/#9) |
| University of Illinois Urbana-Champaign | 22 | 8 | |
| University of Washington-Seattle Campus | 22 | 12 | |
| The University of Texas at Austin | 22 | 14 | |
| Georgia Institute of Technology-Main Campus | 22 | 16 | |
| University of Michigan-Ann Arbor | 22 | 20 | |
| University of Southern California | 22 | 26 | |
| University of California-Los Angeles | 22 | 31 | |

_First seen 2026-06-14. NYU is the ONLY dead feed in the fleet (run 8 confirmed)._

## SECONDARY — reviews depth (miss #8) — only AFTER names + descriptions + content are real

Reviews depth is useful ONLY on a catalog whose rows have real names + real departments +
field-specific descriptions + researched content. Every reviews pass since run 3 landed on
stub rows and will be discarded when those rows are researched (structure-before-depth gate,
miss #8). JHU and CMU are the first non-MIT catalogs whose structure + descriptions are real
— once their deep content is filled, they are the legitimate next reviews targets. No other
enriched catalog is ready for reviews depth yet.

## CLEAN this run (genuinely field-specific, researched descriptions + real structure)

**MIT only** (65 progs, gold reference) — field-specific descriptions, real structure, and
researched deep content (programs carry `cost_data`/`outcomes_data`/`content_sources`/
`ranking_data`; its own reviews coverage is a known gap, not the standard). JHU and CMU are
close (structure + descriptions real) but their program-level deep content
(`content_sources` empty → empty Events/Updates, plus `cost_data`/`outcomes_data`/
`class_profile`/`faculty`/`tracks`) is still thin, so they are NOT yet clean.

---

### Notes for the enricher
- **Top open entry first.** Boston University (CRITICAL — feed revived, but splits,
  credential departments, ~94% classification descriptions remain) before any new university
  or any further depth-only pass.
- **A SINGLE-DIMENSION PASS IS NOT A CLEAR — in EITHER direction (new this run).** Fixing
  only the names (rows 11–13: real names, classification descriptions) OR only the
  descriptions (rows 6–7: field-specific descriptions, 28–37% rollup names) is partial work,
  not a repair. A catalog is cleared only when real names + real departments + collapsed
  splits + field-specific descriptions + researched deep content ALL hold together (SKILL.md
  miss #8, dimension-agnostic clear). Finish every dimension on one catalog before declaring
  it done.
- **DO NOT use `_standard` visibility as a live signal — it is not in the public API**
  (gold MIT shows NONE too). Judge a row by API-visible facts: the name (rollup tell?), the
  department (CIP rollup echoed back?), the description (field-specific vs classification/
  old-template/generic-gloss?), and the deep fields (`/programs/{id}`: filled or empty?).
- **STRUCTURE/CONTENT BEFORE DEPTH (runs 4–6, reinforced).** Do NOT run a reviews or photo
  depth pass on a catalog whose rows are still un-researched stubs — the review is wasted and
  discarded when the row is researched (SKILL.md miss #8). JHU/CMU are the first non-MIT
  catalogs whose structure + descriptions are real; fill their deep content, then review.
- **The two near-done catalogs need CONTENT, not cosmetics.** JHU and CMU programs lack
  `content_sources` (empty Events/Updates, miss #1) and `cost_data`/`outcomes_data`/
  `class_profile`/`faculty_contacts`/`tracks` that gold MIT carries. Fill these (or honestly
  omit each), then run reviews depth.
- A real NAME does not redeem a classification description; a field-specific DESCRIPTION does
  not redeem a CIP-rollup name; and a reviews pass is not a structure fix. Re-audit the live
  output every run by reading the actual API fields, not by trusting a prior PR label.
