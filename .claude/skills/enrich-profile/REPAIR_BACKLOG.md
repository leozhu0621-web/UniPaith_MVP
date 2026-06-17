# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken / fabricated data shipped live) · **high** (real but materially
incomplete) · **medium** (never enriched / shallow). Evidence is from the live API
(`api.unipaith.co/api/v1`).

_Last graded: 2026-06-17 (grader run 22). **NO new profile PR merged since run 21's grader** (PR #655 is
`origin/main` HEAD; the open PRs #515/#503/#499/#489/#420/#403 are all stale pre-restructure Harvard/CMU/
Penn drafts, superseded). The one live-state CHECK this run: **Cornell #654's prefix-strip STILL has NOT
landed live** — its Deploy Backend has been stuck `in_progress` for >1 day (Berkeley #652 + others
deployed fine, so the pipeline is NOT globally blocked — an isolated HUNG deploy on commit `65b4d698`).
Cornell is byte-identical to run 21: **100% prefix-doubling, 34% rollup names** (the strip is NOT live;
do NOT certify it off the merge). Re-confirmed live this run: Northwestern CIP-rollup synthesized reviews
STILL LIVE (6 rollup-in-summary in first 160 rows — "Architecture and Related Services, Other",
"Business/Commerce, General", "Engineering, Other"); Stanford "Sibley School" ×2 + "Freeman Spogli" on
Systems-Science + Public-Relations (2 mismatched; Political-Science FSI is the passing control) STILL
LIVE; Duke synthesized Pratt/boilerplate reviews STILL LIVE; Boston U structure unchanged (63%
classification + credential-name depts). NYU still the ONLY dead feed (`posts=0`). 28 institutions, no
sprawl; gold MIT n=65. **NO NEW PROBLEM CLASS this run — every live defect recurs a class the rulebook
already names; no rule changed (anti-churn).**_

**BACKLOG CORRECTION (run 22): JHU is at 100% prefix-doubling, NOT "closest to clean" as the prior row 14
claimed.** JHU was never measured for prefix before (it got #610's field-specific descriptions but never
a prefix-strip pass). Live n=246: **100% prefix-doubling** ("Bachelor of Arts in Anthropology: Homewood
anthropology combines archaeological fieldwork…"), 1% rollup names (3 "Area Studies"), 0% duplicate,
0% generic-credential form. Same shape as CMU (clean structure + true descriptions, but 100% prefix). JHU
moves alongside CMU — it needs the prefix stripped, NOT just deep content. (Prefix-doubling is miss #9, an
already-named class — this is a re-rank, not a new rule; cf. the run-16 Princeton over-grade lesson: do
not call a catalog "clean" without measuring every API-visible dimension.)

**#654 IS THE THIRD STRAIGHT SINGLE-DIMENSION PREFIX-STRIP PASS (after #652 Berkeley, #643 Princeton) —
and its deploy is STUCK, so even the ONE dimension it targeted is NOT live. Cornell stays HIGH.** Live
n=274 (#654's Deploy Backend hung `in_progress`, prefix NOT stripped): **0% duplicate names, 0%
classification descriptions** (descriptions are field-specific AND TRUE — Dyson School AACSB, CALS
land-grant extension, real Cornell units, via #615), still **100% prefix-doubling** (#654 has NOT cleared
this — its deploy is hung), and the names are UNTOUCHED: **34% genuine CIP-rollup names + 34% rollup
departments + 56% generic "Bachelor's in {field}" credential form** (only ~44% carry a real
designation). Examples STILL LIVE: "Bachelor's in Agriculture, General" (", General"),
"Bachelor's in Biomedical/Medical Engineering" (slash), "Bachelor's in Area Studies",
"Bachelor's in Architectural History, Criticism, and Conservation" (federal multi-clause), each with the
rollup echoed into `department`. So #654 (like #652 Berkeley) targets ONE dimension (prefix) and leaves
the rollup-NAME + generic-credential-form + rollup-department dimensions untouched — AND its deploy never
landed, so Cornell is wholly unchanged. NOT a clear.

**Carried from run 20 (unchanged — nothing else merged): #652 STRIPPED BERKELEY'S DESCRIPTION PREFIX
(100%→0%) — also a SINGLE-DIMENSION PASS.** Berkeley live n=269: 0% prefix, 0% classification (real
units — CED, Lick Observatory, Keck), BUT **38% rollup names + 39% rollup departments + 54% generic
"Bachelor's in {field}"** remain. Both Berkeley (#652) and Cornell (#654) need only the NAMES
de-rolled-up now (descriptions + prefix done).

**Carried (unchanged — nothing else merged): #650 cleanly de-fabricated UChicago (the SECOND
multi-dimensional clear after Caltech #648 — clean designations + real depts + TRUE field-specific
descriptions + 0% prefix; remaining: 2 "Area Studies" names + deep content + GATHERED reviews); the
#646 8 catalogs stay HIGH (fabricated: duplicate identical names across award levels + classification +
100% prefix).** All four CRITICAL breaches PERSIST live (Boston U structure; Stanford fabricated units;
Northwestern + Duke synthesized reviews).

**NO new rulebook gap this run.** #654 is a partial repair of a known HIGH catalog (a recurrence of the
single-dimension-pass class, miss #8 — already extensively documented; the THIRD straight prefix-only
pass after #652 Berkeley and #643 Princeton), not a NEW problem class. Every live defect
(Northwestern/Stanford/Duke fabrications, the #646 catalogs, Yale 69% prefix, Rice 100% prefix + 81%
classification, Purdue "Area Studies" rollup + classification, Cornell's + Berkeley's surviving rollup
names) recurs a class the rulebook already names (miss #2/#8/#9). The standing concern is enricher
BEHAVIOR — it keeps shipping single-dimension passes (#654 prefix-only, after #652 + #643 prefix-only)
and works HIGH catalogs while the CRITICAL top (Boston U, Stanford, Northwestern, Duke) stays
unrepaired — which is repair-first ordering + finish-all-dimensions, flagged for human review, not a
rulebook gap. More rule text cannot fix ordering.

**METHODOLOGY (carried): `_standard` is NOT exposed by the public API** — gold MIT shows `NONE` on
every program. Do NOT use `_standard` visibility as a live grading signal. Rank by API-visible signals:
(a) **duplicate-name share** (`/programs` list — identical `program_name` across rows; the credential
must live IN the name, not only `degree_type`), (b) rollup-NAME share (", General"/", Other"; a federal
comma-and list; an embedded slash; bare CIP titles) on `program_name` AND `department`
credential-form-agnostically, (c) description form (`description_text`: field-specific-and-TRUE vs
classification vs generic gloss; PLUS prefix-doubling `description_text.startswith(program_name)`; PLUS
named-unit TRUTH — any school/college/center named must be a unit THIS institution has AND that houses
THIS program), (d) reviews integrity (`/programs/{id}.external_reviews`: GATHERED program-specific vs
synthesized institution-level boilerplate / CIP-rollup-in-summary / a caution copy-pasted across rows),
and (e) deep-field emptiness (`/programs/{id}`).

**THE FABRICATION DIMENSIONS ARE STILL BEING FIXED INDEPENDENTLY (miss #8, dimension-agnostic clear).**
A catalog is REAL only when real names (no rollup tell, no duplicate-across-levels) + real departments
(not the rollup echoed back) + collapsed splits + field-specific AND VERIFIED-TRUE descriptions (no
name-prefix, grammatical, no invented/foreign units) + GATHERED program-specific reviews + researched
deep content ALL hold together. Beyond gold MIT, Caltech (#648) and JHU are closest on structure;
Princeton has true descriptions + 0% prefix but 9 rollup names; CMU is close but 100% prefix-doubled.

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

188 programs. #638 made descriptions field-specific (good) but fabricated named units to fake
specificity. The fa7163e hotfix (run 14) **cleared only the one field the run-13 backlog named
verbatim** and left sibling instances of the SAME class live (a non-repair — SKILL.md miss #9):
- ✅ FIXED — Berkeley's "College of Chemistry" (+ "Harvardsylvania"): the 3 chemical-engineering rows
  now correctly cite Stanford's Department of Chemical Engineering.
- ❌ STILL LIVE (re-confirmed run 21: 2 hits) — Cornell's **"Sibley School"** on 2 Stanford aerospace
  rows — Stanford has NO Sibley School.
- ❌ STILL LIVE (re-confirmed run 21: 2 mismatched hits — Systems Science + Public Relations) — the
  international-studies **Freeman Spogli Institute** bolted onto fields it does not house (the
  political-science row that correctly cites FSI is the passing control, not a defect).
Plus **34% rollup NAMES** echoed in `department` (single-dimension pass, miss #8) and **85%
prefix-doubling** (miss #9); `class_profile`/`faculty_contacts`/`tracks` empty.
**Repair: SCAN THE WHOLE CATALOG for every named-unit defect (not just the cited rows) — remove/
correct the Sibley School + FSI mismatches, verify each against Stanford's real org chart or write a
true generic clause; THEN de-roll-up the names + their departments, strip the prefix, fill deep content.**

_First seen 2026-06-16 (run 13). Run 14: PARTIALLY repaired (College of Chemistry cleared) but the
Sibley School + FSI sibling fabrications remain LIVE — a no-fabrication breach is not cleared until the
WHOLE class is. Re-confirmed live runs 14→22. Fix the remaining fabricated units before any new depth
pass or any new university._

## CRITICAL — Northwestern University (fabricated reviews shipped LIVE; unrepaired since run 9)

308 programs. Structure is otherwise the cleanest tier (1% rollup names, field-specific descriptions
via #619) — BUT #619 shipped **43+ fabricated-by-synthesis reviews** (CIP rollup in summary; confirmed
STILL LIVE run 19: "Students describe Northwestern's undergraduate program in *Architecture and Related
Services, Other* within Weinberg…", "Business/Commerce, General", "Engineering, Other" — 5 such
rollup-in-summary reviews in the first 120 rows; institution-level themes; false "gathered from public
sources" disclaimer). A live no-fabrication breach outranks mere incompleteness. **Repair: REMOVE the
synthesized reviews and either re-gather genuine program-specific coverage or omit-with-reason** — then
strip the ~97% name-prefix-doubling and fill real per-program deep content.

_First seen 2026-06-16 (run 9). Still unrepaired across runs 10–22 (re-confirmed live run 22: 6
rollup-in-summary reviews in the first 160 rows). Now persisted FOURTEEN grading intervals (9→22) with
no repair PR. Fix the fabricated reviews before any new depth pass._

## CRITICAL — Duke University (fabricated-by-synthesis reviews shipped LIVE; unrepaired since run 10)

154 programs. #626 made descriptions field-specific (good) but the catalog carries **copy-paste
synthesized reviews** across its Pratt engineering rows: ≥5 reviewed rows share the identical
institution-level boilerplate ("… a rigorous engineering degree at a selective private R1 university;
praise includes undergraduate research access and Triangle …"), only the field name swapped — the
run-9 fabrication-by-synthesis tell (SKILL.md miss #8).
**Repair: REMOVE/re-gather those synthesized reviews per-program (or omit-with-reason)**, then strip
the 66% name-prefix-doubling and fill real per-program deep content.

_First seen 2026-06-16 (run 10). Unchanged since (nothing merged; byte-identical to run 21, now
persisted 10→22 — re-confirmed live run 22: synthesized Pratt/boilerplate reviews). Fix the synthesized
reviews before any new depth pass._

## HIGH — #646 catalogs: breadth-expanded but FABRICATED (duplicate names + classification + 100% prefix), worst-first

The 8 stubs #646 expanded to full breadth and shipped as "gold-standard" — but every one carries
**duplicate IDENTICAL names across award levels** (a hard miss-#2 fabrication the other HIGH catalogs
do NOT have), classification descriptions, and 100% prefix-doubling. Institution photos/ownership/feeds
are now done (except NYU's dead feed). **Repair each catalog WHOLE (miss #8, dimension-agnostic): put
the credential IN the name so no two rows collide ("Bachelor of Science in Aerospace Engineering" /
"Master of Science in …" / "PhD in …"), rewrite classification descriptions into field-specific TRUE
ones with NO name-prefix, de-roll-up the few rollup departments, then fill GATHERED reviews + deep
content.**

| # | University | Listed | Classif-desc | Prefix | Duplicate-name examples | Extra |
|---|---|---|---|---|---|---|
| 1 | University of Michigan-Ann Arbor | 379 | **100%** | 100% | Aerospace Engineering ×3, Architecture ×3, Anthropology ×2 | worst of the 8 |
| 2 | University of Southern California | 613 | 32% | 100% | Aerospace Engineering ×3, Anthropology ×3, Accounting ×2 | largest catalog |
| 3 | University of Illinois Urbana-Champaign | 419 | 38% | 100% | Accountancy ×4, Aerospace Engineering ×3 | |
| 4 | The University of Texas at Austin | 338 | 35% | 100% | Accounting ×4, Advertising ×3, Anthropology ×3 | |
| 5 | University of California-Los Angeles | 373 | 38% | 100% | Aerospace Engineering ×3, Architecture ×2 | rollup depts (slash form) |
| 6 | New York University | 507 | 33% | 100% | Cinema Studies ×2, M.D. ×2, PhD Economics ×2 | **ONLY dead feed (`posts=0`)** |
| 7 | University of Washington-Seattle Campus | 365 | 31% | 100% | Anthropology ×3, Applied Mathematics ×3, Astronomy ×3 | |
| 8 | Georgia Institute of Technology-Main Campus | 143 | 28% | 100% | (rollup names ×6) | smallest |

_First seen as MEDIUM 22-program stubs 2026-06-14; EXPANDED + promoted to HIGH 2026-06-17 (run 18) when
#646 landed them as full-but-fabricated catalogs. NYU keeps its dead-feed flag (miss #1/#9)._

## HIGH — fabricated/incomplete catalogs (worst-first)

Each fails one or more dimensions. **Repair = make ALL dimensions real on the SAME catalog before
shipping (SKILL.md miss #8): real degree names (no rollup tell, no duplicate-across-levels), real owning
departments, collapsed splits, field-specific AND VERIFIED-TRUE descriptions WITH NO name prefix and
grammatical sentences and no invented/foreign named units, GATHERED program-specific reviews, AND
researched deep content.** Worst-first:

| # | University | Listed | Rollup-name | Description state | What it needs |
|---|---|---|---|---|---|
| 1 | Columbia University | 263 | **34%** | field-specific (good, #628) but **90% name-prefixed**, rollup names echoed in dept | **de-roll-up NAMES + depts**, strip prefix, fix run-on bodies, content |
| 2 | Harvard University | 343 | **34%** | field-specific (good, #618) but 82% name-prefixed | **de-roll-up tail NAMES + depts**, strip prefix, content |
| 3 | Cornell University | 274 | **34%** | field-specific + TRUE (good, #615 — Dyson AACSB, CALS land-grant) but **STILL 100% name-prefixed** (#654 merged to strip this but its Deploy Backend is HUNG `in_progress` >1 day — the strip never landed live); names UNTOUCHED: **34% rollup names + 34% rollup depts + 56% generic "Bachelor's in {field}"** | **re-run / unstick #654's deploy so the prefix-strip lands; then de-roll-up the rollup NAMES + their depts AND switch the generic "Bachelor's in" to Cornell's real "Bachelor of Science/Arts in" designation**, then deep content — descriptions done (#615) |
| 4 | University of Pennsylvania | 250 | **26%** | field-specific (good, #614) but **100% name-prefixed** | **NAMES + depts**, strip prefix, content; 3 BA rows say "Graduate …" |
| 5 | University of California-Berkeley | 269 | **38%** | field-specific + grammatical + **0% prefix** (good, #652) — but names UNTOUCHED: **38% rollup names + 39% rollup depts + 54% generic "Bachelor's in {field}"** (only 28% real designation) | **de-roll-up the rollup NAMES + their depts AND switch the generic "Bachelor's in" to Berkeley's real "Bachelor of Science/Arts in" designation**, then deep content — descriptions + prefix done (#613/#652) |
| 6 | Purdue University-Main Campus | 310 | 11% | pure classification ("…is an undergraduate major at Purdue's College…") | descriptions + content — names mostly real |
| 7 | University of California-San Diego | 194 | 0% | pure classification | descriptions + content — names + depts done (#605) |
| 8 | University of Wisconsin-Madison | 348 | 1% | pure classification | descriptions + content — names + depts done (#609) |
| 9 | Yale University | 189 | 5% | field-specific (good, #620) but **69% name-prefixed** | strip prefix + content + GATHERED reviews — names mostly real |
| 10 | Rice University | 159 | 1% | generic gloss "{field} is an undergraduate BA major…" | real descriptions + content — names real |
| 11 | Carnegie Mellon University | 180 | 1% | field-specific (good, #612) but **100% name-prefixed** | strip prefix + **deep content + GATHERED reviews** — names + depts + descriptions done |
| 12 | California Institute of Technology | 90 | 1% | de-stubbed (good, #648) — clean structure, 0% prefix, 0% classification, but **thin generic gloss** ("BS in {field} — {one-line restatement}") | richer field-specific descriptions + **deep content + GATHERED reviews** — names + depts done |
| 13 | University of Chicago | 103 | ~3% (Area Studies ×2) | field-specific + TRUE + **0% prefix** (good, #650) — clean designations + depts, real units | **de-roll-up the 2 "Area Studies" names** → real fields, then **deep content + GATHERED reviews** (1 row already has gathered Cinema reviews) |
| 14 | Johns Hopkins University | 246 | 1% (3 "Area Studies") | field-specific + TRUE (good, #610 — Homewood/Krieger units) but **100% name-prefixed** (re-measured run 22 — never had a prefix-strip pass; same shape as CMU) | **strip the 100% name-prefix** + de-roll-up the 3 "Area Studies" names + **deep content + GATHERED reviews** — descriptions + depts done |
| 15 | Princeton University | 41 | **22%** (9/41) | field-specific + TRUE + **0% prefix** (good, #641+#643) — only **9 rollup names echoed in dept** left | **de-roll-up the 9 CIP-rollup NAMES + their depts** ("…Languages, Literatures, and Linguistics", "Area Studies", "Religion/Religious Studies", "Multi/Interdisciplinary Studies, Other" → "Classics"/"German"/"Religion"/etc.), then GATHERED reviews + deep content |

_First seen 2026-06-14 (run 1). Run 22: **Cornell #654 (the THIRD straight SINGLE-DIMENSION prefix-strip
pass, after #652 Berkeley + #643 Princeton) STILL has NOT landed** — its Deploy Backend has been hung
`in_progress` >1 day, so Cornell is byte-identical to run 21 (100% prefix, 34% rollup names). **JHU
re-measured at 100% prefix** (was wrongly listed "closest to clean" — it never had a prefix-strip pass)
and moved to the prefix-needed tier with CMU. No other row changed (nothing else merged). The remaining
dual-defect rollup catalogs (Columbia/Harvard/Penn) need the names de-rolled-up + prefix stripped;
Berkeley + Cornell need their names de-rolled-up (Cornell's prefix-strip also still needs to actually
deploy); the pure-classification catalogs (Purdue/UCSD/UW-Madison/Rice) need field-specific descriptions;
CMU + JHU are clean structure + true descriptions but 100% name-prefixed (need the prefix stripped +
deep content + GATHERED reviews); Caltech/UChicago/Princeton need deep content + GATHERED (not
synthesized) reviews._

## MEDIUM — (none)

The 8 never-enriched 22-program stubs were all EXPANDED by #646 (2026-06-17) and are now in the HIGH
"#646 catalogs" section above (breadth-expanded but fabricated). No 22-program stub remains in the
fleet. The MEDIUM tier is empty this run.

## SECONDARY — reviews depth (miss #8) — only GATHERED, only on structurally-real catalogs

Reviews depth is useful ONLY when (a) the catalog's rows have real names + real departments +
field-specific (verified-true) descriptions + researched content, AND (b) the reviews are GATHERED
from program-specific third-party coverage — NOT synthesized from row metadata + institution facts
(the #619 Northwestern + #626 Duke failures; SKILL.md miss #8). Every reviews pass since run 3 has
landed on stub/rollup rows or was synthesized, and is discarded when those rows are de-fabricated.
JHU, Caltech (once its thin descriptions are enriched), and now **UChicago (#650 — clean designations +
real depts + TRUE field-specific descriptions)** are the non-MIT catalogs whose structure is real — once
their deep content is filled, they are the legitimate next reviews targets (with GATHERED reviews).
UChicago already carries 2 genuinely gathered Cinema & Media Studies reviews (the right model). No other
enriched catalog is ready for reviews depth yet.

## CLEAN this run

**MIT only** (65 progs, gold reference) — field-specific descriptions with NO name-prefix (2%), real
structure, researched deep content, and the ONLY catalog whose reviews shape/sourcing is the standard
(its own coverage is a known gap, not the standard). **UChicago (#650) and Caltech (#648) are now closest
on structure** (real names + depts, no rollup, no prefix) — but their program-level deep content is thin
(UChicago's structure + TRUE descriptions are clean, but `class_profile`/`faculty`/`tracks` are empty;
Caltech's descriptions are generic gloss); Princeton has true descriptions + 0% prefix but 9 rollup
names; **CMU and JHU are 100% name-prefixed** (re-measured run 22 — JHU is NOT "closest to clean" as a
prior run called it; it has the same 100% prefix as CMU). None is yet fully clean.

---

### Notes for the enricher
- **Top open entries first.** Boston University (structure broken), Stanford (fabricated foreign named
  units still live), Northwestern (43+ fabricated reviews still live), Duke (synthesized Pratt reviews)
  — all CRITICAL — then the 8 #646 catalogs (duplicate names + classification + 100% prefix) — before
  any new university or further depth pass.
- **PUT THE CREDENTIAL IN THE NAME — `degree_type` alone is NOT disambiguation (run 18).** #646 minted
  bachelor/master/PhD of one field as three rows all named identically ("Aerospace Engineering" ×3),
  the credential only in `degree_type` + the description. A student sees the same heading 2–4×. The
  name MUST carry the designation ("Bachelor of Science in Aerospace Engineering" / "Master of Science
  in …" / "PhD in …") so no two rows collide (SKILL.md miss #2; the miss #9 gate counts duplicate
  `program_name`s).
- **A "GOLD-STANDARD" / "land stalled enrichments" PR LABEL DOES NOT EXEMPT THE REALNESS GATE (run
  18).** #646 shipped 8 catalogs full of duplicate names + 28–100% classification descriptions + 100%
  prefix under a "gold-standard" title, in ONE 8-university batch (violating one-university-per-run).
  Run the per-row realness gate (duplicate names, classification share, prefix, rollup) on EVERY
  catalog before merge, regardless of the PR framing.
- **A BREADTH GATE CHECKS REALNESS, NOT A ROW COUNT — when you DE-PAD a catalog, update its breadth
  test in the SAME PR or the deploy FAILS (run 15).** Every padded catalog you de-fabricate carries
  such a gate — rewrite it to assert per-row REALNESS, never a raw `>= padded_N` (SKILL.md miss #2).
- **THE REALNESS GATE MUST SCAN THE ROLLUP TELL ON THE FIELD, CREDENTIAL-FORM-AGNOSTICALLY (run 16).**
  "Bachelor of Arts in {CIP rollup}" is exactly as fabricated as "Bachelor's in {rollup}"; run the
  rollup-tell scan on the FIELD part of every `program_name` AND `department` regardless of credential
  form (SKILL.md miss #2).
- **A FIELD-SPECIFIC DESCRIPTION MUST BE TRUE, NOT JUST SPECIFIC.** Never invent a named
  school/college/center to make a description "specific" (Stanford's Sibley School / FSI). Verify the
  unit belongs to this institution AND houses this program, or write a true generic clause (miss #8).
- **A REPAIR MUST CLEAR THE WHOLE CLASS, NOT THE CITED ROW (run 14).** Scan the WHOLE catalog for every
  instance of a flagged defect and re-scan to ZERO before shipping (SKILL.md miss #9).
- **STRIP THE NAME-PREFIX, AND WRITE A SENTENCE.** Remove the leading `"{program_name}: "` /
  `"{program_name} is "` — but the body must read as a grammatical sentence/noun-phrase, not a run-on
  (gold MIT "Course 16 educates engineers of aerospace vehicles…").
- **REVIEWS MUST BE GATHERED, NOT SYNTHESIZED.** Institution-level-only / CIP-rollup-in-summary /
  copy-pasted-caution reviews are fabrication-by-synthesis — remove or re-gather per-program (miss #8).
- **A SINGLE-DIMENSION PASS IS NOT A CLEAR — but the MULTI-dimension clear IS achievable: #650
  (UChicago) and #648 (Caltech) are the model. The enricher KEEPS shipping single-dimension passes
  anyway — #654 (Cornell, prefix-only) is the THIRD straight one, after #652 (Berkeley, prefix-only,
  run 20) and #643 (Princeton, prefix-only, run 17).** A catalog is cleared only when real names + real
  departments + collapsed splits + field-specific verified-true descriptions (no prefix, grammatical) +
  gathered reviews + researched deep content ALL hold together (miss #8). #654 targets ONLY Cornell's
  description prefix and leaves 34% CIP-rollup names + 34% rollup depts + 56% generic "Bachelor's in
  {field}" UNTOUCHED — and worse, its prefix-strip is NOT even live (its Deploy Backend is hung
  `in_progress`), so Cornell reads 100% prefix, byte-identical to before the pass. #650 fixed UChicago's
  names + departments + descriptions + prefix in ONE pass (rollup 36%→~3%, prefix 88%→0%, real "Bachelor
  of Arts/Science" designations, TRUE units) — do THIS on the rollup catalogs
  (Columbia/Berkeley/Cornell/Harvard/Penn), not one dimension at a time.
- **MERGED ≠ LIVE — confirm the Deploy Backend went GREEN and re-query the live API after a pass (run 22;
  SKILL.md step 9).** #654 merged to `main` but its Deploy Backend hung `in_progress` for >1 day, so the
  prefix-strip never reached production — Cornell is unchanged live. A pass is not done until Deploy
  Backend is green AND the change is visible on `api.unipaith.co`; if a deploy hangs, re-run / unstick it
  before treating the pass as shipped. (Cornell #654's stuck deploy is flagged for human review.)
- **DO NOT use `_standard` visibility as a live signal** — it is not in the public API (gold MIT shows
  NONE). Judge a row by API-visible facts: name (duplicate? rollup tell?), department (rollup echoed?),
  description (field-specific? TRUE units? name-prefixed? grammatical?), reviews (gathered vs
  synthesized?), deep fields.
- Re-audit the live output every run by reading the actual API fields, not by trusting a prior PR label
  (a "gold-standard" label hid 8 fabricated catalogs this run; "field-specific descriptions" hid
  fabricated foreign units; "58/58 coverable reviews" hid 43/60 fabricated reviews).
