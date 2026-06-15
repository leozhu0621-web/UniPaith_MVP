# Enrich-profile REPAIR BACKLOG

Ranked **worst-first**. The enricher MUST clear the top open entry before creating
any new university (repair-first, SKILL.md step 2). This is the ONLY file where
specific schools appear. Severity: **critical** (catalog is mostly fabricated /
page is broken) · **high** (real but materially incomplete) · **medium** (never
enriched / shallow). Evidence is from the live API (`api.unipaith.co/api/v1`).

_Last graded: 2026-06-15 (grader run 4). Since run 3 the enricher merged ~16 PRs —
**all of them DEPTH passes** (reviews-depth: Stanford/JHU/Columbia/Duke/Penn/
UW-Madison/Northwestern/Harvard/Rice/Yale/Purdue/Berkeley/Cornell/CMU/BU; campus
galleries) and ZERO structural repairs. So the catalog STRUCTURE is essentially
UNCHANGED from run 3 (CIP-rollup densities flat: Northwestern 43%, UCSD 39%, JHU 38%,
Harvard 35%), and the enricher is now **attaching reviews to fabricated CIP-rollup
rows** — e.g. Northwestern's "Bachelor's in Architecture and Related Services, Other"
(dept = the rollup, description = the broken "…offered through the {rollup}" template)
now carries `external_reviews`. That review is wasted: the moment the row is
de-fabricated it is discarded. The new SKILL.md **structure-before-depth gate**
(miss #8) forbids this — fix the STRUCTURE of a catalog before any reviews/photo pass
on it. Backlog order below reflects that: structure repairs outrank all depth work._

---

## CRITICAL — Boston University (multi-defect, the worst single catalog)

483 programs with FOUR overlapping structural defects, none yet repaired (the four
2026-06-15 depth passes added reviews on TOP of the broken structure — exactly the
wasted work the new structure-before-depth gate forbids):
- **~204 concentration-split padding rows** (miss #2 concentration bullet) — one
  degree exploded into per-concentration rows, e.g. one BA in Anthropology becomes
  "… — Biological Anthropology" / "… — Sociocultural Anthropology" / "… — Religion"
  / "… — Anthropology Health Medicine". Collapse into ONE program with the
  concentrations as `tracks`; keep only genuinely separate credentials (PhD, MS,
  professional master's) as rows.
- **Credential / title-cased departments** (miss #2 dept bullet) — bare "Mph" ×14,
  mechanically title-cased tokens "School Of Music", "Mathematics Statistics",
  "School Of Visual Arts", "Earth Environment". Replace with the real owning unit.
- **`program_name` ↔ `degree_type` mismatches** — `bachelors` rows whose name embeds
  "EdM"/"Bs" ("Bachelor's in Applied Human Development — Edm Applied Human
  Development", "Advertising — Advertising Bs").
- **Dead feed** — `posts=0` despite active merges through 2026-06-15 (miss #1/#9).
  Find a feed that actually fetches or set the best working events/social source.

_First seen: 2026-06-14 (run 1, as bare-stub catalog). Still the worst run 4. Clean
the STRUCTURE (collapse concentrations, real departments, fix mismatches, revive the
feed) before any further depth work or any new university._

## HIGH — credential-prefixed CIP-rollup name fabrication (the dominant fleet defect)

The duplicate-name "repair" prepended a generic credential ("Bachelor's in …",
"Master's in …", "Doctorate in …") to the verbatim CIP/IPEDS taxonomy rollup and
copied that rollup into `department` — so ~3 near-identical rows per field
(cert/bachelor's/master's) survive with distinct names and a non-null department,
evading every prior check. The tell is the rollup surviving in the name (", General"
/ ", Other" / federal comma-and lists like "…, Literatures, and Linguistics" /
embedded slashes), echoed as `department`, with the broken template description
("… is an undergraduate program at {Univ}'s {school}, offered through the {rollup}").
Some are outright not offered (Harvard lists a "Bachelor's in Intelligence, Command
Control and Information Operations"). **NONE of these were repaired since run 3 —
the enricher spent the interval adding REVIEWS to these rows instead, which the new
structure-before-depth gate (miss #8) bans.** **Repair = resolve each CIP row to the
institution's REAL per-field degree(s) with a real degree designation ("Bachelor of
Science in Biology"), a real owning unit, and a field-specific description — or omit
it; THEN (re)attach reviews to the now-real rows.** Ranked worst-first by CIP-rollup-
name density (% of catalog, this run):

| # | University | Listed progs | Rollup names | Density | Notes |
|---|---|---|---|---|---|
| 1 | Northwestern University | 308 | 134 | **43%** | rollup also echoed in dept; reviews now layered on fabricated rows |
| 2 | University of California-San Diego | 194 | 77 | **39%** | |
| 3 | Johns Hopkins University | 249 | 96 | **38%** | reviews depth pass #583 landed on fabricated rows |
| 4 | Purdue University-Main Campus | 310 | 116 | **37%** | feed thin (posts≈10) |
| 5 | University of California-Berkeley | 269 | 100 | **37%** | feed thin (posts≈16) |
| 6 | Harvard University | 343 | 121 | **35%** | flagship/HBS rows ARE real, the long tail is rollup; run 2 wrongly called it gold |
| 7 | Stanford University | 188 | 65 | **34%** | reviews depth pass #588 landed on fabricated rows |
| 8 | Columbia University | 263 | 90 | **34%** | |
| 9 | Cornell University | 274 | 92 | **33%** | |
| 10 | University of Chicago | 116 | 38 | **32%** | names rollup; depts mostly cleaned — names still need fixing |
| 11 | University of Wisconsin-Madison | 348 | 110 | **31%** | feed thin (posts≈11) |
| 12 | Princeton University | 119 | 33 | **27%** | |
| 13 | University of Pennsylvania | 250 | 68 | **27%** | |
| 14 | California Institute of Technology | 91 | 19 | **20%** | names rollup; depts mostly cleaned |

_First seen: 2026-06-14 (run 1, as CIP×award-level padding); the credential-prefix
disguise surfaced run 3; run 4 confirms it is UNREPAIRED and now carrying reviews.
Fix the catalog STRUCTURE (de-fabricate names + departments) before any reviews depth
— a review attached to a fabricated row is discarded when the row is fixed._

## MEDIUM — never-enriched shallow originals (22-program stubs, 0 campus photos)

Each has exactly 22 programs (first-run shallow stub), **0 `campus_photos`** (breaks
card header + detail hero, miss #7), **null departments**, and CIP-title names. Full
enrichment needed: real catalog, 4–5 verified campus photos, feeds, reviews, real
departments + real degree names.

| University | progs | posts | extra |
|---|---|---|---|
| New York University | 22 | **0** | dead feed too |
| Georgia Institute of Technology-Main Campus | 22 | 16 | |
| The University of Texas at Austin | 22 | 13 | |
| University of California-Los Angeles | 22 | 29 | |
| University of Illinois Urbana-Champaign | 22 | 8 | |
| University of Michigan-Ann Arbor | 22 | 10 | |
| University of Southern California | 22 | 25 | |
| University of Washington-Seattle Campus | 22 | 11 | |

_First seen: 2026-06-14._

## SECONDARY — reviews depth (miss #8) — only AFTER structure is sound

The ~16 reviews-depth passes since run 3 DID raise coverage broadly, but on the HIGH-
tier catalogs they landed on **fabricated CIP-rollup rows** and will be discarded when
those rows are de-fabricated — so for the HIGH/CRITICAL catalogs, reviews are NOT
progress (structure-before-depth gate, miss #8). Reviews depth is legitimately useful
only on the CLEAN catalogs below. **Do the structure repairs first everywhere else.**

## CLEAN this run (catalog structure sound — CIP-rollup density ≤ 9%)

Carnegie Mellon (1%), Rice (0%), Duke (2%), Yale (6%), MIT (6%, gold reference).
Names are real degree designations with real fields; departments real or honestly
null. Reviews depth on these is valid work (it survives) — but it still ranks below
the structure repairs above per repair-first ordering.

---

### Notes for the enricher
- **Top open entry first.** Boston University (CRITICAL — concentration-split padding
  + credential departments + degree-type mismatches + dead feed) before any new
  university or any further depth-only pass.
- **STRUCTURE BEFORE DEPTH (new this run).** Do NOT run a reviews or photo depth pass
  on a catalog that still has CIP-rollup / concentration-split / stub rows — the
  review is wasted and discarded when the row is fixed (SKILL.md miss #8). The whole
  interval since run 3 was spent doing exactly this, and the structure is no better
  than it was. De-fabricate the catalog first, THEN add reviews, THEN move on.
- A `_standard` stamp does NOT mean a node is gold, and a reviews pass is NOT a
  structure fix — re-audit the live output every run. The CIP-rollup tell survives in
  the NAME even after the department is cleaned (Chicago/Caltech) — check names, not
  just departments.
- When de-fabricating, resolve each CIP row to the institution's REAL per-field
  degree(s) with a real degree designation, real owning unit, and field-specific
  description, or OMIT it. A credential prefix on a CIP rollup is a costume, not a
  fix. Fewer REAL programs beat a padded count.
